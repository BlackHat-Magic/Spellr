from discord import app_commands, ui
from discord.ext import app_commands
from dotenv import load_dotenv
import discord, asyncio, json, os

from models import User, Channel

load_dotenv()

HELP_MSG = """# Spellr Character Profile Template:

```
# Display Name
-# @Username
-# :round_pushpin: Ur Dad's House � :link: your.link � :balloon: Born Month DD, YYYY � :calendar_spiral: Joined Month YYYY
-# **XXX** Following � **XXXX** Followers
```

# Spellr Post Template:

```
**Display Name**
-# @Username
Your text here
```"""

class FeedCog(commands.Cog):
    def __init__(self, client, session):
        self.client = client
        self.session_ = session_
    
    @app_commands.command(name="help")
    @app_commands.describe(style="Get Help with Using Spellr")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(HELP_MSG)
    
    @app_commands.command(name="setup")
    @app_commands.describe(style="Set Up a New Spellr Feed")
    async def setup(self, interaction: discord.Interaction):
        # check if the user has sufficient permissions
        if(not interaction.user.guild_permissions.manage_guild):
            await interaction.response.send_message("Insufficient permissions; you need the \"Manage Server\" permission to set up new Spellr feeds", ephemeral=True)
            return
        
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
        await interaction.response.defer()
        async for message in interaction.channel.history(limit=100, oldest_first=True):
            await message.delete()
        async for webhook in interaction.channel.webhooks():
            await webhook.delete()
        
        # order the posts in disparate threads and re-send them with webhooks
        for thread in interaction.channel.threads:
            await thread.delete()
    
    @app_commands.command(name="register")
    @app_commands.describe(style="Set Up a New Spellr Feed")
    async def register(self, interaction: discord.Interaction):
        # check if this isn't a db_channel
        db_channel = self.session_.get(Channel, interaction.channel.id)
        if(not db_channel):
            await interaction.response.send_message("This channel is not a Spellr feed. Use /setup to set one up!")
            return
        
        # check if the user is already registered here
        user_in_feed = self.session.query(Account).filter_by(discord_userid=interaction.user.id)
        if(user_in_feed):
            await interaction.response.send_message("You already have an account in this feed. Alt accounts coming soon (tm).")
            return