import discord, random

from models import Channel, User, Account

ADJECTIVES = ["witty", "misty", "abusive", "real", "competitive", "careful", "gaping", "assorted", "bloody", "ill-informed", "rightful", "snobbish", "tight", "clever", "forgetful", "plastic", "hateful", "decent", "ten", "amusing", "tightfisted", "wiggly", "hypnotic", "offbeat", "better", "changeable", "wary", "ethereal", "draconian", "unadvised", "inner", "shiny", "flippant", "mundane", "worthless", "lowly", "bustling", "abashed", "complete", "wasteful", "malicious", "willing", "dramatic", "swanky", "obviously", "tender", "robust", "suspicious", "fixed", "dizzy"]

NOUNS = ["refrigerator", "phone", "garbage", "writing", "marketing", "death", "assistant", "story", "software", "committee", "improvement", "tension", "variation", "competition", "road", "driver", "feedback", "length", "judgment", "departure", "mixture", "difference", "media", "philosophy", "inflation", "disk", "assignment", "president", "property", "data", "accident", "lab", "association", "confusion", "mud", "patience", "warning", "artisan", "error", "wedding", "apple", "person", "promotion", "ratio", "advertising", "cell", "army", "satisfaction", "music", "midnight"]

def random_username():
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    username = adjective.capitalize()
    number = random.randint(0, 99)
    if(random.randint(0, 1)):
        username += str(number)
        username += "-"
        username += noun.capitalize()
    else:
        username += "-"
        username += noun.capitalize()
        username += str(number)
    return(username, adjective, noun, number)

class Register(discord.ui.Modal):
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
        if(not self.children[1].value):
            return((0, 0, 0))
        try:
            dob = self.children[1].value.split("/")
            bmonth = int(dob[0])
            bday = int(dob[1])
            byear = int(dob[2])
            if(bmonth < 1 or bmonth > 12):
                return((0, 0, 0))
            if(bday < 1):
                return((0, 0, 0))
            if(bmonth in [1, 3, 5, 7, 8, 10, 12] and bday > 31):
                return((0, 0, 0))
            if(bmonth in [4, 6, 9, 11] and bday > 30):
                return((0, 0, 0))
            if(bmonth == 2 and bday > 29):
                return((0, 0, 0))
            return((bmonth, bday, byear))
        except:
            return((0, 0, 0))
    
    def get_jday(self):
        if(not self.children[2].value):
            return((0, 0))
        try:
            doj = self.children[2].value.split("/")
            jmonth = doj[0]
            jyear = doj[1]
            if(jmonth > 12 or jmonth < 1):
                return((0, 0))
            return((jmonth, jyear))
        except:
            return((0, 0))

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
        adjective = noun = number = None
        for character in handle:
            if(not character.isalnum() and character not in ["-", "_"]):
                handle, adjective, noun, number = random_username()
        if(adjective is None):
            display_name = handle
        else:
            display_name = f"{adjective.capitalize()} {noun.capitalize()}"
        handle = handle.casefold()
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
            await interaction.response.send_message("Account with that handle already exists. Pick handle username.", ephemeral=True)
            return
        
        # identify or create user
        db_user = self.session.get(User, interaction.user.id)
        if(not db_user):
            db_user = User(
                id=interaction.user.id
            )
            self.session.add(db_user)
            self.session.commit()

        # create account
        new_account = Account(
            user=db_user,
            channel=db_channel,
            discord_userid=interaction.user.id,
            handle=handle,
            display_name=display_name,
            bio="",
            location="",
            website=f"spellr.gg/@{handle}",
            bmonth=bmonth,
            bday=bday,
            byear=byear,
            jmonth=jmonth,
            jyear=jyear,
            following=following,
            followers=followers,
            avatar_url=interaction.user.avatar.url
        )
        profile_thread = await interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Profile",
            auto_archive_duration=10080,
        )
        profile_webhook = await interaction.channel.create_webhook(name=f"{handle} Webhook", reason=f"Create Spellr posts for {handle}")
        profile_message = await profile_webhook.send(
            content=new_account.print_profile(), 
            username=new_account.display_name, 
            avatar_url=new_account.avatar_url, 
            thread=profile_thread
        )
        new_account.profile_threadid = profile_thread.id
        new_account.profile_messageid = profile_message.id
        new_account.webhookid = profile_webhook.id


        spells_thread = await interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Spells",
            auto_archive_duration=10080
        )
        new_account.spells_threadid = spells_thread.id
        self.session.add(new_account)
        self.session.commit()

        response_message = "Registered.\n\nUse `/update_profile` to update your Display Name, Handle, Bio, or Location"
        if(adjective != None):
            response_message += '\n\nHandles must only be alphanumeric characters (a-z, A-Z, 0-9), dashes ("-") and underscores ("_") are allowed. You have been assigned a random handle. Use `/update_profile` to set it yourself.\n\nUse `/following` and `/followers` to update following and followers count, respectively.'
        if(any([bmonth == 0, bday == 0, byear == 0])):
            response_message += "\n\nInvalid birthday specified. Use `/birthday` to correct it."
        if(jmonth == 0 or jyear == 0):
            response_message += "\n\nInvalid join date specified. Use `/join_date` to correct it."
        await interaction.response.send_message(response_message, ephemeral=True)

class CastModal(discord.ui.Modal):
    def __init__(self, session, accountid=None, *args, **kwargs):
        super().__init__(title="Cast a spell!")
        self.session_ = session
        content = discord.ui.TextInput(
            label="Spell Content",
            style=discord.TextStyle.long,
            placeholder="What's on your mind?",
            required=True,
            max_length=140,
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        elif(isinstance(interaction.channel, discord.Thread)):
            channelid = interaction.channel.parent_id
        else:
            await interaction.followup.send("Spellr only supports threads and text channels; not forums, voice channels, or DMs.", ephemeral=True)
            return
        
        if(accountid is None)
            db_user = self.session_.query(Account).filter_by(userid=interaction.user.id, channelid=channelid).first()
        else:
            db_user = self.session_.get(Account, accountid)
        if(not db_user):
            await interaction.followup.send("You don't have any registered accounts in this feed. Use `/register` to register one.")
            return

        cast_message = await profile_webhook.send(
            content=self.children[0].value,
            username=db_user.display_name,
            avatar_url=db_user.avatar_url,
            thread=db_user.thread
        )
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

class AccountDropdown(discord.ui.Select):
    def __init__(self, accounts, session, what, new_value):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
        self.session_ = session
        self.accounts = accounts
        self.what = what
        self.what_name = what.replace("_", " ")
        self.new_value = new_value

        super().__init__(placeholder=f"Account to change {self.what_name}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]
        if(target_account is None or not db_account):
            await interaction.followup.send(f"Unable to change {self.what_name}.", ephemeral=True)
            return
        old_handle = db_account.handle
        
        setattr(db_account, self.what.replace(" ", "_"), self.new_value)
        self.session_.add(db_account)
        self.session_.commit()
        await db_account.update(interaction)
        await interaction.followup.send(f"Changed @{old_handle}'s {self.what_name} to {self.new_value}.", ephemeral=True)

class DOBDropdown(discord.ui.Select):
    def __init__(self, accounts, session, bday, bmonth, byear):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
        self.session_ = session
        self.accounts = accounts
        self.bday = bday
        self.bmonth = bmonth
        self.byear = byear

        super().__init__(placeholder=f"Select an account to change date of birth...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]
        if(target_account is None or not db_account):
            await interaction.followup.send(f"Unable to change date of birth.", ephemeral=True)
            return
        
        bday, bmonth, byear = self.bday, self.bmonth, self.byear

        if(bday < 1):
            await interaction.followup.send(f"Invalid birth day; must be at least 1.", ephemeral=True)
            return
        if(bmonth in [1, 3, 5, 7, 8, 10, 12] and bday > 31):
            await interaction.followup.send(f"Chosen month only has 31 days; pick a day between 1 and 31.")
            return
        if(bmonth in [4, 6, 9, 11] and bday > 30):
            await interaction.followup.send(f"Chosen month only has 30 days; pick a day between 1 and 30")
            return
        if(bmonth == 2 and bday > 29):
            await interaction.followup.send(f"February only has 28-29 days; pick a day between 1 and 29")
            return
        
        db_account.bday = self.bday
        db_account.bmonth = self.bmonth
        db_account.byear = self.byear
        self.session_.add(db_account)
        self.session_.commit()
        await db_account.update(interaction)

        await interaction.followup.send(f"Changed @{db_account.handle}'s date of birth to {self.bmonth} {self.bday}, {self.byear}.", ephemeral=True)

class JoinDateDropdown(discord.ui.Select):
    def __init__(self, accounts, session, jmonth, jyear):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
        self.session_ = session
        self.accounts = accounts
        self.jmonth = jmonth
        self.jyear = jyear

        super().__init__(placeholder=f"Select an account to change join date...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]
        if(target_account is None or not db_account):
            await interaction.followup.send(f"Unable to change date of birth.", ephemeral=True)
            return
        
        db_account.jmonth = self.jmonth
        db_account.jyear = self.jyear
        self.session_.add(db_account)
        self.session_.commit()
        await db_account.update(interaction)

        await interaction.followup.send(f"Changed @{db_account.handle}'s join date to {self.jmonth} {self.jyear}.", ephemeral=True)