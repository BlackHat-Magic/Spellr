import discord

from models import Channel, User, Account

PROFILE_MESSAGE_TEMPLATE = """# {display_name}'s Profile
-# @{handle}
{bio}
"""

class Register(discord.ui.Modal, title="Register a Spellr Account"):
    def __init__(self, session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_ = session
        self.handle = discord.ui.TextInput(
            label="Handle",
            placeholder="@ZacDorothy",
            required=True,
            max_length=32
        )
        self.display_name = discord.ui.TextInput(
            label="Display Name (Optional)",
            placeholder="Not Treelom Tusk",
            required=False,
            max_length=32
        )
        self.bio = discord.ui.TextInput(
            label="Bio (Optional)",
            placeholder="Founder at Tooter (Now Z), now I make Spellr.",
            style=discord.TextStyle.long,
            required=False,
            max_length=512,
        )

    async def on_submit(self, interaction: discord.Interaction):
        # verify channel
        db_channel = self.session_.get(Channel, interaction.channel.id)
        if(not db_channel):
            await interaction.response.send_message("Spellr feed does not exist. Perhaps it was deleted while you were filling out the form?", ephemeral=True)
            return
        
        # verify account
        db_account = self.session_.query(Account).filter_by(channel=db_channel, handle=self.handle).first()
        if(db_user):
            await interaction.response.send_message("Account with that username already exists. Pick another username.", ephemeral=True)
        
        # identify or create user
        db_user = self.session_.get(User, interaction.user.id)
        if(not db_user):
            db_user = User(
                id = Column(Integer, primary_key=True)
            )
            db.session.add(db_user)
            try:
                db.session.commit()
            except:
                await interaction.response.send_message("Failed to register account.", ephemeral=True)
                return
        
        # create account
        if(not self.display_name):
            self.display_name = self.handle
        new_account = Account(
            channel=db_channel,
            discord_userid=interaction.user.id,
            handle=self.handle,
            display_name=self.display_name,
            bio=self.bio
        )
        db.session.add(new_account)
        try:
            db.session.commit()
        except:
            await interaction.response.send_message("Failed to register account.", ephemeral=True)
            return
        
        profile_thread = interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Profile",
            message=
        )
        spell_thread = interaction.channel.create_thread()

        await interaction.response.send_message("")