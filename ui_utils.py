import discord, random

from models import Channel, User, Account

PROFILE_MESSAGE_TEMPLATE = """# {display}
-# @{handle}
{bio}
-# :round_pushpin: {location} :link: {website} :balloon: Born {month} {day}, {year} :calendar_spiral: Joined {joinedm} {joinedy}
-# **{following}** Following **{followers}** Followers"""

def format_profile_message(account):
    response = f"# {account.display_name}"
    response += f"\n-# @{account.handle}"
    response += f"\n{account.bio}"
    response += f"\n"

class Register(discord.ui.Modal):
    # handle = discord.ui.TextInput(
    #     label="Handle",
    #     placeholder="@ZacDorothy",
    #     required=True,
    #     max_length=32
    # )
    # async def on_submit(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(self.handle.value)
    def __init__(self, session, *args, **kwargs):
        super().__init__(title="Register a Spellr Account")
        self.session = session
        handle = discord.ui.TextInput(
            label="Handle",
            placeholder="ZacDorothy",
            required=True,
            max_length=32
        )
        bday = discord.ui.TextInput(
            label="Birthday (Optional)",
            placeholder="MM/DD/YYYY (sorry)",
            required=False,
            max_length=10
        )
        jday = discord.ui.TextInput(
            label="Account Creation (Optional)",
            placeholder="MM/YYYY (sorry)",
            required=True,
            max_length=10
        )
        following = discord.ui.TextInput(
            label="Following (Optional)",
            placeholder="0 people B)",
            required=False,
            max_length=11
        )
        followers = discord.ui.TextInput(
            label="Followers (Optional)",
            placeholder="Everyone B)",
            required=False,
            max_length=11
        )

        self.add_item(handle)
        self.add_item(bday)
        self.add_item(jday)
        self.add_item(following)
        self.add_item(followers)
        
    
    def get_bday(self):
        if(self.children[1].value):
            dob = self.children[1].value.split("/")
            if(len(dob) == 3):
                bmonth = dob[0]
                bday = dob[1]
                byear = dob[2]
            else:
                bmonth = bday = byear = 0
        else:
            bmonth = bday = byear = 0
        return(bmonth, bday, byear)
    
    def get_jday(self):
        if(self.children[2].value):
            doj = self.children[2].value.split("/")
            if(len(doj) == 2):
                jmonth = doj[0]
                jyear = doj[1]
            else:
                jmonth = jyear = 0
        else:
            jmonth = jyear = 0
        return(jmonth, jyear)

    def get_followage(self):
        if(not self.children[3].value):
            following = 0
        else:
            try:
                following = int(self.children[3].value)
            except:
                following = 0
        if(not self.children[4].value):
            followers = 0
        else:
            try:
                followers = int(self.children[4].value)
            except:
                followers = 0
        return(following, followers)

    async def on_submit(self, interaction: discord.Interaction):
        handle = self.children[0].value
        bmonth, bday, byear = self.get_bday()
        jmonth, jyear = self.get_jday()
        following, followers = self.get_followage()

        # verify channel
        db_channel = self.session.get(Channel, interaction.channel.id)
        if(not db_channel):
            await interaction.response.send_message("Spellr feed does not exist. Perhaps it was deleted while you were filling out the form?", ephemeral=True)
            return
        
        # verify account
        db_account = self.session.query(Account).filter_by(channel=db_channel, handle=handle).first()
        if(db_account):
            await interaction.response.send_message("Account with that username already exists. Pick another username.", ephemeral=True)
            return
        
        # identify or create user
        db_user = self.session.get(User, interaction.user.id)
        if(not db_user):
            db_user = User(
                id = interaction.user.id
            )
            self.session.add(db_user)
            try:
                self.session.commit()
            except:
                await interaction.response.send_message("Failed to register account.", ephemeral=True)
                return

        # create account
        new_account = Account(
            channel=db_channel,
            discord_userid=interaction.user.id,
            handle=handle.casefold(),
            display_name=handle,
            bio="",
            location="",
            website=f"spellr.gg/@{handle.casefold()}",
            bmonth=bmonth,
            bday=bday,
            byear=byear,
            jmonth=jmonth,
            jyear=jyear,
            following=following,
            followers=followers
        )
        self.session.add(new_account)
        try:
            self.session.commit()
        except:
            await interaction.response.send_message("Failed to register account.", ephemeral=True)
            return
        
        profile_thread = await interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Profile",
            auto_archive_duration=10080,
            
        )
        await profile_thread.send("Profile Message")
        spells_thread = await interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Spells",
            auto_archive_duration=10080
        )
        await spells_thread.send("Spells message")

        await interaction.response.send_message("Registered :inverted_upload:1343858469924503582:", ephemeral=True)

class Dropdown(discord.ui.Select):
    def __init__(self, options):
        options = [discord.SelectOption(label=label, description=description, emoji=emoji) for option in options]

        super().__init__(placeholder="Select an account to change display name...", min_values=1, max_values=1, options=options)