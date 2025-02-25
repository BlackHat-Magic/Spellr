from discord import app_commands, ui
from discord.ext import commands
from ui_utils import Register, AccountDropdown
import discord, asyncio, json

from models import User, Channel, Account

class FeedCog(commands.Cog):
    def __init__(self, client, session):
        self.client = client
        self.session_ = session
    
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="setup")
    async def setup(self, interaction: discord.Interaction):
        # check if the user has sufficient permissions
        # if(not interaction.user.guild_permissions.manage_guild and not interaction.user.guild_permissions.admin):
        #     await interaction.response.send_message("Insufficient permissions; you need the \"Manage Server\" permission to set up new Spellr feeds", ephemeral=True)
        #     return
        
        # check if this is avalid channel
        if(not isinstance(interaction.channel, discord.TextChannel)):
            await interaction.response.send_message("Spellr must be set up in a channel; not a DM or a Thread.", ephemeral=True)

        # check if this channel is already a spellr feed
        db_channel = self.session_.get(Channel, interaction.channel.id)
        if(db_channel):
            await interaction.response.send_message("Spellr already set up in this channel", ephemeral=True)
            return
        new_channel = Channel(
            id=interaction.channel.id
        )
        try:
            self.session_.add(new_channel)
            self.session_.commit()
            db_channel = new_channel
        except:
            await interaction.response.send_message("Failed to create new Spellr feed.", ephemeral=True)
            return
        
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
    
    @app_commands.command(name="register")
    async def register(self, interaction: discord.Interaction):
        # check if this isn't a db_channel
        db_channel = self.session_.get(Channel, interaction.channel.id)
        if(not db_channel):
            await interaction.response.send_message("This channel is not a Spellr feed. Use /setup to set one up!", ephemeral=True)
            return
        
        await interaction.response.send_modal(Register(session=self.session_))
    
    @app_commands.command(name="display")
    async def display(self, interaction: discord.Interaction, display_name: str):
        await interaction.response.defer()

        if(display_name == ""):
            await interaction.followup.send("Usage: `/display <new display name>`\n\nThen, you will be asked which account to change the display name of.", ephemeral=True)
            return
        
        if(len(display_name) > 32):
            await interaction.followup.send("Display name too long; max 32 characters.", ephemeral=True)
            return

        channelid = interaction.channel.id
        userid = interaction.user.id
        db_accounts = self.session_.query(Account).filter_by(channelid=channelid, userid=userid).all()
        if(not db_accounts):
            await interaction.followup.send("You don't have any registered accounts in this feed to change.", ephemeral=True)
            return
        
        if(len(db_accounts) == 1):
            db_accounts[0].display_name = display_name
            try:
                self.session_.add(db_accounts[0])
                self.session_.commit()
            except:
                await interaction.followup.send("Unable to change display name.", ephemeral=True)
                return
            await interaction.followup.send(f"Display name changed to {display_name}")
            return
        
        view = AccountDropdown(db_accounts)

        await interaction.followup.send("", view=view, ephemeral=True)

    @app_commands.command(name="handle")
    async def display(self, interaction: discord.Interaction, handle: str):
        await interaction.response.defer(ephemeral=True)

        if(handle == ""):
            await interaction.followup.send("Usage: `/handle <new account handle>`\n\nThen, you will be asked which account to change the handle of", ephemeral=True)
            return
        
        if(len(handle) > 32):
            await interaction.followup.send("`Handle too long; max 32 characters.`", ephemeral=True)
            return

        channelid = interaction.channel.id
        userid = interaction.user.id
        db_accounts = self.session_.query(Account).filter_by(channelid=channelid, userid=userid).all()
        if(not db_accounts):
            await interaction.followup.send("You don't have any registered accounts in this feed to change.", ephemeral=True)
            return