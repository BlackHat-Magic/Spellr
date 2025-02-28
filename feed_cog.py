from ui_utils import Register, AccountDropdown, DOBDropdown, JoinDateDropdown, CastModal, SpellButton, SpellButtonsDropdown, CastDropdown, format_cast, SpellView, Spell
from sqlalchemy.exc import SQLAlchemyError
from discord import app_commands, ui
from discord.ext import commands
import discord, asyncio, json

from models import User, Channel, Account

class FeedCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._interaction_cache = {}
    
    def require_feed(self, interaction: discord.Interaction):
        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        elif(isinstance(interaction.channel, discord.Thread)):
            channelid = interaction.channel.parent_id
        else:
            raise app_commands.CheckFailure("Spellr feeds only supported in normal text channels; not others like forums or voice channels.")
        db_channel = self.client.db_session.get(Channel, channelid)
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
        db_accounts = self.client.db_session.query(Account).filter_by(channelid=channelid, userid=interaction.user.id).all()
        if(not db_accounts):
            raise app_commands.CheckFailure("You don't have any registered accounts in this feed to change. Use `/register` to register one.")
        interaction.extras["db_accounts"] = db_accounts
    
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="setup")
    async def setup(self, interaction: discord.Interaction):
        # check if this is a valid channel
        if(not isinstance(interaction.channel, discord.TextChannel)):
            await interaction.response.send_message("Spellr must be set up in a channel; not a DM or a Thread.", ephemeral=True, delete_after=30)
            return

        # check if this channel is already a spellr feed
        db_channel = self.client.db_session.get(Channel, interaction.channel.id)
        if(db_channel):
            await interaction.response.send_message("Spellr already set up in this channel.", ephemeral=True, delete_after=15)
            return
        
        # setup database stuff
        db_channel = Channel(
            id=interaction.channel.id
        )
        
        # otherwise delete all the old messages and webhooks
        await interaction.response.defer(ephemeral=True)
        safeid = await interaction.original_response()
        await interaction.channel.purge()
        webhooks = await interaction.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
        channel_webhook = await interaction.channel.create_webhook(name="Spellr Webhook", reason="New Spellr feed")
        db_channel.webhookid = channel_webhook.id
        
        # delete other threads
        for thread in interaction.channel.threads:
            await thread.delete()
        
        try:
            self.client.db_session.add(db_channel)
            self.client.db_session.commit()
        except:
            self.client.db_session.rollback()
            await interaction.response.send_message("Failed to create Spellr feed. Try again later.", ephemeral=True, delete_after=15)
            return
        
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
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        # set max length
        if(account_property in ["display_name", "handle", "location", "website"]):
            max_length = 32
        else:
            max_length = 512
        if(len(new_value) > max_length):
            await interaction.followup.send(f"{property_name} text too long; max {max_length} characters.", ephemeral=True)
            return
        
        if(account_property == "handle"):
            new_value = new_value.casefold()
            matching_profiles = interaction.client.db_session.query(Account).filter_by(handle=new_value).all()
            if(matching_profiles):
                await interaction.followup.send("An account with that handle already exists. Choose another handle.", ephemeral=True)
                return

        property_name = account_property.replace("_", " ").capitalize()
        
        # pretty easy if user only has one account
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            setattr(db_accounts[0], account_property, new_value)
            self.client.db_session.add(db_accounts[0])
            self.client.db_session.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send(f"{property_name} changed to {new_value}")
            return
        
        # if user has multiple, we need a view
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, account_property, new_value))
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
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        # make sure date is (mostly) valid
        if(birth_day < 1):
            await interaction.followup.send("Invalid day. Pick a day greater than 0.", ephemeral=True)
            return
        if(birth_month in [1, 3, 5, 7, 8, 10, 12] and birth_day > 31):
            await interaction.followup.send("Selected month only has 31 days. Pick a day between 1 and 31", ephemeral=True)
            return
        if(birth_month in [4, 6, 9, 11] and birth_day > 30):
            await interaction.followup.send("Selected month only has 30 days. Pick a day between 1 an 30.", ephemeral=True)
            return
        if(birth_month == 2 and birth_day > 29):
            await interaction.followup.send("February only has 28-29 days. Pick a day between 1 and 29.", ephemeral=True)
            return
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].bday = birth_day
            db_accounts[0].bmonth = birth_month
            db_accounts[0].byear = birth_year
            self.client.db_session.add(db_accounts[0])
            self.client.db_session.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Date of birth updated.", ephemeral=True)
            return
        
        # otherwise we need a view
        view = discord.ui.View()
        view.add_item(DOBDropdown(db_accounts, birth_day, birth_month, birth_year))
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
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].jmonth = join_month
            db_accounts[0].jyear = join_year
            self.client.db_session.add(db_accounts[0])
            self.client.db_session.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Join date updated.", ephemeral=True)
            return
        
        # otherwise we need a view
        view = discord.ui.View()
        view.add_item(JoinDateDropdown(db_accounts, join_month, join_year))
        await interaction.followup.send("Select an account to change the join date:", view=view)
    
    @app_commands.command(name="following")
    @app_commands.describe(following="The number of accounts you're following.")
    async def following(self, interaction: discord.Interaction, following: int):
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        # make sure user has an account in this feed
        userid = interaction.user.id
        db_accounts = interaction.extras["db_accounts"]
        if(not db_accounts):
            await interaction.followup.send("You don't have any registered accounts in this feed to change. Use `/register` to register one.", ephemeral=True)
            return
        
        # if the user only has one account, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].following = following
            self.client.db_session.add(db_accounts[0])
            self.client.db_session.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Followage updated.", ephemeral=True)
            return
        
        #otherwise we need a view
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, "following", following))
        await interaction.followup.send("Select an account to change followage:", view=view, ephemeral=True)
    
    @app_commands.command(name="followers")
    @app_commands.describe(followers="The number of followers you have.")
    async def followers(self, interaction: discord.Interaction, followers: int):
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        
        # if the user only has one account in this feed, this is pretty straightforward
        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            db_accounts[0].followers = followers
            self.client.db_session.add(db_accounts[0])
            self.client.db_session.commit()
            await db_accounts[0].update(interaction)
            await interaction.followup.send("Followers updated.", ephemeral=True)
            return
        
        view = discord.ui.View()
        view.add_item(AccountDropdown(db_accounts, "followers", followers))
        await interaction.followup.send("Select an account to change followers:", view=view, ephemeral=True)
    
    @app_commands.command(name="cast")
    async def cast(self, interaction: discord.Interaction):
        try:
            self.require_feed(interaction)
            self.require_account(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command.", ephemeral=True)
            return

        db_accounts = interaction.extras["db_accounts"]
        if(len(db_accounts) == 1):
            await interaction.response.send_modal(CastModal())
            return

        if(isinstance(interaction.channel, discord.Thread)):
            matching_profile = interaction.client.db_session.query(Account).filter_by(profile_threadid=interaction.channel.id, userid=interaction.user.id).first()
            if(matching_profile and matching_profile.userid == interaction.user.id):
                await interaction.response.send_modal(CastModal(accountid=matching_profile.id))
                return
        
        view = discord.ui.View()
        view.add_item(CastDropdown(db_accounts))
        await interaction.response.send_message("Select an account to cast with:", view=view, ephemeral=True)

    @app_commands.command(name="register")
    async def register(self, interaction: discord.Interaction):
        try:
            self.require_feed(interaction)
        except app_commands.CheckFailure as e:
            await interaction.response.send_message(e.args[0] if e.args else "You do not have permission to use this command", ephemeral=True, delete_after=30)
            return
        await interaction.response.send_modal(Register())
    
    # @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if(isinstance(message.channel, discord.Thread)):
            # is this channel a feed?
            db_channel = self.client.db_session.get(Channel, message.channel.parent_id)
            if(not db_channel):
                return

            # is there an account associated with this thread and user in this feed?
            db_user = self.client.db_session.query(Account).filter_by(channelid=db_channel.id, profile_threadid=message.channel.id, userid=message.author.id).first()
            if(not db_user):
                return
        elif(isinstance(message.channel, discord.TextChannel)):
            db_channel = self.client.db_session.get(Channel, message.channel.id)
            if(not db_channel):
                return
            
            db_users = self.client.db_session.query(Account).filter_by(channelid=db_channel.id, userid=message.author.id).all()
            if(not db_users or len(db_users) > 1):
                await message.delete()
                return
            db_user = db_users[0]
        else:
            return
            
        content = await format_cast(db_user, message.content[:300], self.client)
        thread = message.channel
        await message.delete()

        webhook = await self.client.fetch_webhook(db_channel.webhookid)

        new_spell = Spell(
            author=db_user,
            content=content
        )
        try:
            self.client.db_session.add(new_spell)
            self.client.db_session.flush()
        except:
            self.client.db_session.rollback()
            return

        thread_message = await webhook.send(
            content=content,
            username=db_user.display_name,
            avatar_url=db_user.avatar_url,
            view=SpellView(new_spell.id, self.client, "thread"),
            wait=True,
            thread=thread
        )
        new_spell.thread_messageid = thread_message.id
        feed_message = await webhook.send(
            content=content,
            username=db_user.display_name,
            avatar_url=db_user.avatar_url,
            view=SpellView(new_spell.id, self.client, "feed"),
            wait=True
        )
        new_spell.feed_messageid = feed_message.id
        try:
            self.client.db_session.commit()
        except:
            self.client.db_session.rollback()
            await thread_message.delete()
            await feed_message.delete()