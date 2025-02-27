import discord, random, re

from models import Channel, User, Account, format_cast, Spell, format_recast, format_ponder

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
    def __init__(self, *args, **kwargs):
        super().__init__(title="Register a Spellr Account")
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
            jmonth = int(doj[0])
            jyear = int(doj[1])
            if(jmonth > 12 or jmonth < 1):
                return((0, 0))
            return((jmonth, jyear))
        except Exception as e:
            print(e)
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
        db_channel = interaction.client.db_session.get(Channel, interaction.channel.id)
        if(not db_channel):
            await interaction.response.send_message("Spellr feed does not exist. Perhaps it was deleted while you were filling out the form?", ephemeral=True)
            return
        
        # verify account
        db_account = interaction.client.db_session.query(Account).filter_by(channel=db_channel, handle=handle).first()
        if(db_account):
            await interaction.response.send_message("Account with that handle already exists. Pick handle username.", ephemeral=True)
            return
        
        # identify or create user
        db_user = interaction.client.db_session.get(User, interaction.user.id)
        if(not db_user):
            try:
                db_user = User(
                    id=interaction.user.id
                )
                interaction.client.db_session.add(db_user)
                interaction.client.db_session.commit()
            except:
                await interaction.response.send_message("Account creation failed. Try again later.", ephemeral=True)
                return

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
            type=discord.ChannelType.public_thread
        )
        profile_webhook = await interaction.channel.create_webhook(name=f"{handle} Webhook", reason=f"Create Spellr posts for {handle}")
        profile_message = await profile_webhook.send(
            content=new_account.print_profile(), 
            username=new_account.display_name, 
            avatar_url=new_account.avatar_url, 
            thread=profile_thread,
            wait=True
        )
        new_account.profile_threadid = profile_thread.id
        new_account.profile_messageid = profile_message.id
        new_account.webhookid = profile_webhook.id


        spells_thread = await interaction.channel.create_thread(
            name=f"{new_account.display_name}'s Spells",
            auto_archive_duration=10080,
            type=discord.ChannelType.public_thread
        )
        new_account.spells_threadid = spells_thread.id
        try:
            interaction.client.db_session.add(new_account)
            interaction.client.db_session.commit()
        except:
            interaction.response.send_message("Account creation failed. Try again later.", ephemeral=True)
            return

        async for message in interaction.channel.history(limit=10):
            if(message.type == discord.MessageType.thread_created):
                await message.delete()

        response_message = "Registered.\n\nUse `/update_profile` to update your Display Name, Handle, Bio, or Location"
        if(adjective != None):
            response_message += '\n\nHandles must only be alphanumeric characters (a-z, A-Z, 0-9), dashes ("-") and underscores ("_") are allowed. You have been assigned a random handle. Use `/update_profile` to set it yourself.\n\nUse `/following` and `/followers` to update following and followers count, respectively.'
        if(any([bmonth == 0, bday == 0, byear == 0])):
            response_message += "\n\nInvalid birthday specified. Use `/birthday` to correct it."
        if(jmonth == 0 or jyear == 0):
            response_message += "\n\nInvalid join date specified. Use `/join_date` to correct it."
        await interaction.response.send_message(response_message, ephemeral=True)

class SpellButtonsDropdown(discord.ui.Select):
    def __init__(self, interaction, action, target):
        self.action = action
        self.target = target

        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        else:
            channelid = interaction.channel.parent_id
        self.accounts = interaction.client.db_session.query(Account).filter_by(userid=interaction.user.id, channelid=channelid).all()

        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(self.accounts)]

        super().__init__(placeholder=f"Account with which to {action}...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]

        if(self.action == "recast" or self.action == "ponder"):
            await interaction.response.send_modal(CastModal(
                accountid=db_account.id, 
                recasting=self.target if self.action == "recast" else None,
                pondering=self.target if self.action == "ponder" else None
            ))

class SpellButton(
    discord.ui.DynamicItem[discord.ui.Button], 
    template=r"(?P<castid>[0-9]+)-(?P<action>[a-z]+)-(?P<location>[a-z]+)"
):
    def __init__(self, castid, action, emoji, location, label):
        super().__init__(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.grey,
                custom_id=f"{str(castid)}-{action}-{location}",
                emoji=emoji
            )
        )
        self.castid = castid
        self.action = action
        self.emoji = emoji
        self.location = location
    
    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str]):
        castid = int(match["castid"])
        spell = interaction.client.db_session.get(Spell, castid)
        action = match["action"]
        if(action == "recast"):
            emoji = "<:recast:1344069245918773288>"
            label = str(len(spell.recasts))
        elif(action == "ponder"):
            emoji = "<:ponder:1344068886588555397>"
            label = str(len(spell.ponders))
        elif(action == "charm"):
            emoji = "<:charm:1344068841973612644>"
            label = str(spell.charms)
        else:
            emoji = "<:scribe:1344068996387049614>"
            label = str(spell.scribes)
        location = match["location"]
        return(cls(castid, action, emoji, location, label))
    
    async def callback(self, interaction: discord.Interaction):
        # check channel
        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        else:
            channelid = interaction.channel.parent_id

        #if user only has one account, relatively straightforward
        db_accounts = interaction.client.db_session.query(Account).filter_by(channelid=channelid, userid=interaction.user.id).all()
        if(self.action == "recast" or self.action == "ponder"):
            if(len(db_accounts) == 1):
                await interaction.response.send_modal(CastModal(
                    accountid=db_accounts[0].id, 
                    recasting=self.castid if self.action == "recast" else None, 
                    pondering=self.castid if self.action == "ponder" else None
                ))
                return
            
            # otherwise we send them the appropriate account selection dropdown
            view = discord.ui.View()
            view.add_item(SpellButtonsDropdown(interaction, self.action, self.castid))
            await interaction.response.send_message(f"Select an account to {self.action} with:", view=view, ephemeral=True)
        
        # liking
        if(self.action == "charm"):
            cast = interaction.client.db_session.get(Cast, castid)
            cast.charms += 1
            interaction.client.db_session.add(cast)
            interaction.client.db_session.commit()
            self.item.label = str(int(self.label) + 1)
            await interaction.message.edit(view=self.view)
        
        # bookmarking
        if(self.action == "scribe"):
            cast = interaction.client.db_session.get(Spell, castid)
            cast.scribes += 1
            interaction.client.db_session.add(cast)
            interaction.client.db_session.commit()
            self.item.label = str(int(self.label) + 1)
            await interaction.message.edit(view=self.view)

class SpellView(discord.ui.View):
    def __init__(self, castid, client, location):
        super().__init__(timeout=None)
        spell = client.db_session.get(Spell, castid)
        actions = [
            ("recast", "<:recast:1344069245918773288>", str(len(spell.recasts))),
            ("ponder", "<:ponder:1344068886588555397>", str(len(spell.ponders))),
            ("charm", "<:charm:1344068841973612644>", str(spell.charms)),
            ("scribe", "<:scribe:1344068996387049614>", str(spell.scribes))
        ]
        for action, emoji, label in actions:
            self.add_item(SpellButton(castid, action, emoji, location, label))

class CastModal(discord.ui.Modal):
    def __init__(self, accountid=None, recasting=None, pondering=None, *args, **kwargs):
        super().__init__(title="Cast a spell!")
        self.accountid = accountid
        self.recasting = recasting
        self.pondering = pondering
        content = discord.ui.TextInput(
            label=f"Spell Content{' (Optional)' if self.pondering else ''}",
            style=discord.TextStyle.long,
            placeholder="What's on your mind?",
            required=(self.pondering == None),
            max_length=300,
        )
        attachment_url = discord.ui.TextInput(
            label="Attachment URL (Optional)",
            placeholder="https://awesomesite.com/my_image.png",
            required=False,
            max_length=1024
        )
        self.add_item(content)
        self.add_item(attachment_url)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # check channel
        if(isinstance(interaction.channel, discord.TextChannel)):
            channelid = interaction.channel.id
        elif(isinstance(interaction.channel, discord.Thread)):
            channelid = interaction.channel.parent_id
        else:
            await interaction.followup.send("Spellr only supports threads and text channels; not forums, voice channels, or DMs.", ephemeral=True)
            return
        
        # get account
        if(self.accountid is None):
            db_user = interaction.client.db_session.query(Account).filter_by(userid=interaction.user.id, channelid=channelid).first()
        else:
            db_user = interaction.client.db_session.get(Account, self.accountid)
        if(not db_user):
            await interaction.followup.send("You don't have any registered accounts in this feed. Use `/register` to register one.", ephemeral=True)
            return

        # start sending message
        profile_webhook = await interaction.client.fetch_webhook(db_user.webhookid)
        profile_thread = await interaction.client.fetch_channel(db_user.profile_threadid)
        new_spell = Spell(
            author=db_user,
            content=self.children[0].value,
        )
        interaction.client.db_session.add(new_spell)
        interaction.client.db_session.flush()
        # reply
        if(self.recasting):
            print("recasting")
            content = await format_recast(db_user, interaction, self.children[0].value, new_spell, self.recasting)

            # get databse object of recasted spell
            db_recasting_spell = interaction.client.db_session.get(Spell, self.recasting)

            # get thread message of recasted spell
            recast_from_thread = db_recasting_spell.author.profile_threadid
            recast_thread_channel = await interaction.client.fetch_channel(recast_from_thread)
            recast_thread_message = await recast_thread_channel.fetch_message(db_recasting_spell.thread_messageid)
            thread_embeds = recast_thread_message.embeds

            # get feed message of recasted spell
            if(not db_recasting_spell.feed_messageid):
                recast_feed_message = None
            else:
                recast_feed_channel = await interaction.client.fetch_channel(channelid)
                recast_feed_message = await recast_feed_channel.fetch_message(db_recasting_spell.feed_messageid)
            
            # check that we can do this
            if(len(thread_embeds) >= 10):
                await interaction.followup.send("Too many replies on this spell (only 10 supported).", ephemeral=True)
                return

            # send the profile message
            thread_message = await profile_webhook.send(
                content=content,
                username=db_user.display_name,
                avatar_url=db_user.avatar_url,
                thread=profile_thread,
                wait=True,
                view=SpellView(new_spell.id, interaction.client, "thread")
            )

            # construct embed
            db_user_profile = await profile_thread.fetch_message(db_user.profile_messageid)
            db_user_url = db_user_profile.jump_url
            embedded_reply = discord.Embed(
                color=discord.Colour(0x0080FF), 
                title=db_user.display_name, 
                url=db_user_url,
                description=self.children[0].value
            )
            embedded_reply.set_author(
                name=f"@{db_user.handle}",
                url=db_user_url,
                icon_url=db_user.avatar_url
            )
            thread_embeds.append(embedded_reply)

            # add to thread message
            print(db_recasting_spell.thread_messageid)
            edited_thread_message = await profile_webhook.edit_message(
                db_recasting_spell.thread_messageid,
                embeds=thread_embeds,
                thread=profile_thread
            )
            db_recasting_spell.thread_messageid = edited_thread_message.id

            # add to feed message
            if(recast_feed_message):
                edited_feed_message = await profile_webhook.edit_message(
                    recast_feed_message.id,
                    embeds=thread_embeds
                )
                db_recasting_spell.feed_message_id = edited_feed_message.id

            new_spell.thread_messageid = thread_message.id
            new_spell.feed_messageid = None
            interaction.client.db_session.add(db_recasting_spell)
        elif(self.pondering):
            # get parent information
            content, embed = await format_ponder(db_user, interaction, self.children[0].value, new_spell, self.pondering)

            thread_message = await profile_webhook.send(
                content=content,
                username=db_user.display_name,
                avatar_url=db_user.avatar_url,
                thread=profile_thread,
                wait=True,
                view=SpellView(new_spell.id, interaction.client, "thread"),
                embeds=[embed]
            )
            feed_message = await profile_webhook.send(
                content=content,
                username=db_user.display_name,
                avatar_url=db_user.avatar_url,
                wait=True,
                view=SpellView(new_spell.id, interaction.client, "feed"),
                embeds=[embed]
            )
            new_spell.thread_messageid = thread_message.id
            new_spell.feed_messageid = feed_message.id
        else:
            content = await format_cast(db_user, self.children[0].value, interaction.client)

            thread_message = await profile_webhook.send(
                content=content,
                username=db_user.display_name,
                avatar_url=db_user.avatar_url,
                thread=profile_thread,
                wait=True,
                view=SpellView(new_spell.id, interaction.client, "thread")
            )
            feed_message = await profile_webhook.send(
                content=content,
                username=db_user.display_name,
                avatar_url=db_user.avatar_url,
                wait=True,
                view=SpellView(new_spell.id, interaction.client, "feed")
            )
            new_spell.thread_messageid = thread_message.id
            new_spell.feed_messageid = feed_message.id
        interaction.client.db_session.commit()

class AccountDropdown(discord.ui.Select):
    def __init__(self, accounts, what, new_value):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
        self.accounts = accounts
        self.what = what
        self.what_name = what.replace("_", " ")
        self.new_value = new_value

        super().__init__(placeholder=f"Account to change {self.what_name}...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]
        old_handle = db_account.handle
        
        setattr(db_account, self.what.replace(" ", "_"), self.new_value)
        interaction.client.db_session.add(db_account)
        interaction.client.db_session.commit()
        await db_account.update(interaction)
        await interaction.followup.send(f"Changed @{old_handle}'s {self.what_name} to {self.new_value}.", ephemeral=True)

class CastDropdown(discord.ui.Select):
    def __init__(self, accounts):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
        self.accounts=accounts

        super().__init__(placeholder="Account to cast with...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        target_account = self.values[0]
        db_account = self.accounts[int(target_account)]

        await interaction.response.send_modal(CastModal(accountid=db_account.id))

class DOBDropdown(discord.ui.Select):
    def __init__(self, accounts, bday, bmonth, byear):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
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
        interaction.client.db_session.add(db_account)
        interaction.client.db_session.commit()
        await db_account.update(interaction)

        month = [
            None,
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ][self.bmonth]

        await interaction.followup.send(f"Changed @{db_account.handle}'s date of birth to {month} {self.bday}, {self.byear}.", ephemeral=True)

class JoinDateDropdown(discord.ui.Select):
    def __init__(self, accounts, jmonth, jyear):
        options = [discord.SelectOption(label=account.display_name, description=f"@{account.handle}", value=i) for i, account in enumerate(accounts)]
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
        interaction.client.db_session.add(db_account)
        interaction.client.db_session.commit()
        await db_account.update(interaction)

        month = [
            None,
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ][self.jmonth]

        await interaction.followup.send(f"Changed @{db_account.handle}'s join date to {month} {self.jyear}.", ephemeral=True)