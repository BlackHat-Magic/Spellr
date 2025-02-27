from ui_utils import Register, AccountDropdown, DOBDropdown, JoinDateDropdown
from sqlalchemy.exc import SQLAlchemyError
from discord import app_commands, ui
from discord.ext import commands
import discord, asyncio, json

from models import User, Channel, Account

class FeedCog(commands.Cog):
    def __init__(self, client, session):
        self.client = client
        self.session_ = session
        self._interaction_cache = {}
    
    def require_feed(self, interaction: discord.Interaction):
        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        elif(isinstance(interaction.channel, discord.Thread)):
            channelid = interaction.channel.parent_id
        else:
            raise app_commands.CheckFailure("Spellr feeds only supported in normal text channels; not others like forums or voice channels.")
        db_channel = self.session_.get(Channel, channelid)
        if(not db_channel):
            raise app_commands.CheckFailure("This channel is not a Spellr feed. Use `/setup` to set one up!")
        interaction.extras["db_channel"] = db_channel

    def require_account(self, interaction: discord.Interaction):
        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        elif(isinstance(interaction.channel, discord.Thread)):
            channelid = interaction.channel.parent_id
        else:
            raise app_commands.CheckFailure("You don't have any registered accounts in this feed to change. Use `/register` to register one.")
        userid = interaction.user.id
        db_accounts = self.session_.query(Account).filter_by(channelid=channelid, userid=interaction.user.id).all()
        if(not db_accounts):
            raise app_commands.CheckFailure("You don't have any registered accounts in this feed to change. Use `/register` to register one.")
        interaction.extras["db_accounts"] = db_accounts
    
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="setup")
    async def setup(self, interaction: discord.Interaction):
        # check if this is a valid channel
        if(not isinstance(interaction.channel, discord.TextChannel)):
            await interaction.response.send_message("Spellr must be set up in a channel; not a DM or a Thread.", ephemeral=True)
            return

        # check if this channel is already a spellr feed
        db_channel = self.session_.get(Channel, interaction.channel.id)
        if(db_channel):
            await interaction.response.send_message("Spellr already set up in this channel", ephemeral=True)
            return
        new_channel = Channel(
            id=interaction.channel.id
        )
        self.session_.add(new_channel)
        self.session_.commit()
        db_channel = new_channel
        
        # otherwise delete all the old messages and webhooks
        await interaction.response.defer(ephemeral=True)
        safeid = await interaction.original_response()
        async for message in interaction.channel.history(limit=100, oldest_first=True):
            if(message.id == safeid.id):
                continue
            await message.delete()
        webhooks = await interaction.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
        
        # delete other threads
        for thread in interaction.channel.threads:
            await thread.delete()
        
        await interaction.followup.send("New Spellr feed created.", ephemeral=True)

    @app_commands.command()
    @app_commands.describe(account_property="Property of profile to change")
    @app_commands.choices(
        account_property=[
            app_commands.Choice(name="Display Name", value="display_name"),
            app_commands.Choice(name="Handle", value="handle"),
            app_commands.Choice(name="Bio", value="bio"),
            app_commands.Choice(name="Location", value="location"),
            app_commands.Choice(name="Website", value="website")
        ]
    )
    async def update_profile(self, interaction: discord.Interaction, account_property: str, new_value: str):
        await interaction.response.defer(ephemeral=True)
        self.require_feed(interaction)
        self.require_account(interaction)
        
        # set max length
        if(account_property in ["display_name", "handle", "location", "website"]):
            max_length = 32
        else:
            max_length = 512
        if(len(new_value) > max_length):
            await interaction.followup.send(f"{property_name} text too long; max {max_length} characters.", ephemeral=True)
            return

        property_name = account_property.replace("_", " ").capitalize()
        
        # pretty easy if user only has one account
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            setattr(db_accounts[0], account_property, new_value)
            self.session_.add(db_accounts[0])
            self.session_.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send(f"{property_name} changed to {new_value}")
            return
        
        # if user has multiple, we need a view
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, self.session_, account_property, new_value))
        await interaction.followup.send(f"Select an account to change {property_name}:", view=view, ephemeral=True)
    
    @app_commands.command(name="birthday")
    @app_commands.describe(birth_month="The Month you were born", birth_day="The day in the month you were born", birth_year="The year you were born")
    @app_commands.choices(
        birth_month=[
            app_commands.Choice(name="January", value=1),
            app_commands.Choice(name="February", value=2),
            app_commands.Choice(name="March", value=3),
            app_commands.Choice(name="April", value=4),
            app_commands.Choice(name="May", value=5),
            app_commands.Choice(name="June", value=6),
            app_commands.Choice(name="July", value=7),
            app_commands.Choice(name="August", value=8),
            app_commands.Choice(name="September", value=9),
            app_commands.Choice(name="October", value=10),
            app_commands.Choice(name="November", value=11),
            app_commands.Choice(name="December", value=12)
        ],
    )
    async def birthday(self, interaction:discord.Interaction, birth_month: int, birth_day: int, birth_year: int):
        await interaction.response.defer(ephemeral=True)
        self.require_feed(interaction)
        self.require_account(interaction)

        # make sure date is (mostly) valid
        if(birth_month in [4, 6, 9, 11] and birth_day > 30):
            await interaction.followup.send("Selected month only has 30 days. Pick a day between 1 an 30.", ephemeral=True)
            return
        if(birth_month == 2 and birth_month > 29):
            await interaction.followup.send("February only has 28-29 days. Pick a day between 1 and 29.", ephemeral=True)
            return
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].bday = birth_day
            db_accounts[0].bmonth = birth_month
            db_accounts[0].byear = birth_year
            self.session_.add(db_accounts[0])
            self.session_.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Date of birth updated.", ephemeral=True)
            return
        
        # otherwise we need a view
        view = discord.ui.View()
        view.add_item(DOBDropdown(db_accounts, self.session_, birth_day, birth_month, birth_year))
        await interaction.followup.send("Select an account to change date of birth:", view=view)
    
    @app_commands.command(name="join_date")
    @app_commands.describe(join_month="The date you joined")
    @app_commands.describe(join_year="The year you joined")
    @app_commands.choices(
        join_month=[
            app_commands.Choice(name="January", value=1),
            app_commands.Choice(name="February", value=2),
            app_commands.Choice(name="March", value=3),
            app_commands.Choice(name="April", value=4),
            app_commands.Choice(name="May", value=5),
            app_commands.Choice(name="June", value=6),
            app_commands.Choice(name="July", value=7),
            app_commands.Choice(name="August", value=8),
            app_commands.Choice(name="September", value=9),
            app_commands.Choice(name="October", value=10),
            app_commands.Choice(name="November", value=11),
            app_commands.Choice(name="December", value=12)
        ],
        join_year=[app_commands.Choice(name=str(i), value=i) for i in range(2006, 2026)]
    )
    async def joinday(self, interaction: discord.Interaction, join_month: int, join_year: int):
        await interaction.response.defer(ephemeral=True)
        self.require_feed(interaction)
        self.require_account(interaction)
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].jmonth = join_month
            db_accounts[0].jyear = join_year
            self.session_.add(db_accounts[0])
            self.session_.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Join date updated.", ephemeral=True)
            return
        
        # otherwise we need a view
        view = discord.ui.View()
        view.add_item(JoinDateDropdown(db_accounts, self.session_, join_month, join_year))
        await interaction.followup.send("Select an account to change the join date:", view=view)
    
    @app_commands.command(name="following")
    @app_commands.describe(following="The number of accounts you're following.")
    async def following(self, interaction: discord.Interaction, following: int):
        await interaction.response.defer(ephemeral=True)
        self.require_feed(interaction)
        self.require_account(interaction)

        # make sure user has an account in this feed
        userid = interaction.user.id
        db_accounts = self.session_.query(Account).filter_by(channelid=channelid, userid=userid).all()
        if(not db_accounts):
            await interaction.followup.send("You don't have any registered accounts in this feed to change. Use `/register` to register one.", ephemeral=True)
            return
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].following = following
            self.session_.add(db_accounts[0])
            self.session_.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Followage updated.", ephemeral=True)
            return
        
        #otherwise we need a view
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, self.session_, "following", following))
        await interaction.followup.send("Select an account to change followage:", view=view, ephemeral=True)
    
    @app_commands.command(name="followers")
    @app_commands.describe(followers="The number of followers you have.")
    async def followers(self, interaction: discord.Interaction, followers: int):
        await interaction.response.defer(ephemeral=True)
        self.require_feed(interaction)
        self.require_account(interaction)
        
        # if the user only has one account in this feed, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].followers = followers
            self.session_.add(db_accounts[0])
            self.session_.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Followers updated.", ephemeral=True)
            return
        
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, self.session_, "followers", followers))
        await interaction.followup.send("Select an account to change followers:", view=view, ephemeral=True)
    
    @app_commands.command(name="cast")
    async def cast(self, interaction: discord.Interaction):
        self.require_feed(interaction)
        self.require_account(interaction)

        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            await interaction.response.send_modal(CastModal(session=self.session_))
        await interaction.response.send_modal(CastModal(session=self.session_))

    @app_commands.command(name="register")
    async def register(self, interaction: discord.Interaction):
        self.require_feed(interaction)
        await interaction.response.send_modal(Register(session=self.session_))
    
    @commands.Cog.listener()
    async def on_command_error(self, interaction: discord.Interaction, error):
        if(isinstance(error, app_commands.CheckFailure)):
            if(interaction.response.is_done()):
                await interaction.followup.send(error.args[0] if error.args else "You do not have permission to use this command.", ephemeral=True)
            else:
                await interaction.followup.send_message(error.args[0] if error.args else "You do not have permission to use this command.", ephemeral=True)
        elif(isinstance(error, ValueError)):
            if(interaction.response.is_done()):
                await interaction.followup.send(error.args[0] if error.args else "Other ValueError while processing command.", ephemeral=True)
            else:
                await interaction.followup.send_message(error.args[0] if error.args else "Other ValueError while processing command.", ephemeral=True)
        elif(isinstance(error, SQLAlchemyError)):
            self.session_.rollback()
            if(interaction.response.is_done()):
                await interaction.followup.send("Database error occurred; try again later.", ephemeral=True)
            else:
                await interaction.response.send_message("Database error occurred; try again later.", ephemeral=True)
        else:
            if(interaction.response.is_done()):
                await interaction.followup.send("An unexpected error occurred.", ephemeral=True)
            else:
                await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)
            raise error
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if(message.type == discord.MessageType.channel_name_change and message.author == self.client.user):
            try:
                await message.delete()
            except discord.Forbidden:
                print("Bot lacks sufficient permissions.")
            except discord.NotFound:
                print("Message already deleted.")
            except Exception as e:
                print(e)