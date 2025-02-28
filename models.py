from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv
import os, discord

load_dotenv()

DATABASE_NAME = os.getenv("SQLITE_DATABASE_NAME")
month_list = [
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
]

async def format_cast(account, text, client):
    thread = await client.fetch_channel(account.profile_threadid)
    profile_message = await thread.fetch_message(account.profile_messageid)
    profile_link = profile_message.jump_url
    formatted = f"-# [@{account.handle}]({profile_link})\n{text}"
    return(formatted)

async def format_recast(db_account, interaction, text, new_spell, recasting):
    db_recasting_spell = interaction.client.db_session.get(Spell, recasting)
    if(not db_recasting_spell):
        raise discord.app_commands.CheckFailure("Unable to find spell to recast.")
    recasting_channel = await interaction.client.fetch_channel(db_recasting_spell.author.profile_threadid)
    new_spell.recasting_to = db_recasting_spell
    
    # link for handle
    recasting_display_name = db_recasting_spell.author.display_name
    recasting_handle = db_recasting_spell.author.handle
    recasting_profile_message = await recasting_channel.fetch_message(db_recasting_spell.author.profile_messageid)
    recasting_profile_link = recasting_profile_message.jump_url

    # link for "recasting:"
    recasting_spell = await recasting_channel.fetch_message(db_recasting_spell.thread_messageid)
    recasting_link = recasting_spell.jump_url

    content = f"-# [@{db_account.handle}]({recasting_profile_link})"
    content += f"\n**[Recasting to {recasting_display_name}]({recasting_link})**"
    content += f"\n> -# [@{recasting_handle}]({recasting_profile_link})"
    content += f"\n> {db_recasting_spell.content}\n\n"
    content += text

    return(content)

async def format_ponder(db_account, interaction, text, new_spell, pondering):
    db_pondering_spell = interaction.client.db_session.get(Spell, pondering)
    if(not db_pondering_spell):
        raise discord.app_commands.CheckFailure("Unable to find spell to ponder.")
    
    while db_pondering_spell.pondering_to:
        if(not db_pondering_spell.content):
            db_pondering_spell = db_pondering_spell.pondering_to
        else:
            break

    pondering_channel = await interaction.client.fetch_channel(db_pondering_spell.author.profile_threadid)
        
    pondering_profile = await pondering_channel.fetch_message(db_pondering_spell.author.profile_messageid)
    new_spell.pondering_to = db_pondering_spell
    
    # link for handle
    pondering_display_name = db_pondering_spell.author.display_name
    pondering_handle = db_pondering_spell.author.handle
    pondering_profile_link = pondering_profile.jump_url

    # link for "pondering:"
    pondering_spell = await pondering_channel.fetch_message(db_pondering_spell.thread_messageid)
    pondering_link = pondering_spell.jump_url

    # content
    if(text):
        content = await format_cast(db_account, text, interaction.client)
    else:
        content = ""
    content += "\n-# Pondering:"

    # parent embed
    ponder_preview = discord.Embed(
        title=pondering_display_name,
        description=db_pondering_spell.content
    )
    ponder_preview.set_author(
        name=f"@{pondering_handle}",
        url=pondering_profile_link,
        icon_url=db_pondering_spell.author.avatar_url
    )
    ponder_preview.url = pondering_link
    ponder_preview.color = discord.Colour(0x2b2d31)
    if(db_pondering_spell.pondering_to):
        ponder_preview.set_footer(
            text=f"Pondering {db_pondering_spell.pondering_to.author.display_name}",
            icon_url=db_pondering_spell.pondering_to.author.avatar_url
        )
    if(pondering_spell.attachments):
        ponder_preview.set_image(url=pondering_spell.attachments[0].url)
    
    return((content, ponder_preview))

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    accounts = relationship("Account", back_populates="user")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    accounts = relationship("Account", back_populates="channel")
    webhookid = Column(Integer)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    channelid = Column(Integer, ForeignKey("channels.id"))
    userid = Column(Integer, ForeignKey("users.id"))

    # Define relationships with proper back_populates
    channel = relationship("Channel", back_populates="accounts")
    user = relationship("User", back_populates="accounts")
    
    discord_userid = Column(Integer)
    profile_threadid = Column(Integer)
    profile_messageid = Column(Integer)
    spells_threadid = Column(Integer)
    
    avatar_url = Column(String)
    display_name = Column(String)
    handle = Column(String)
    bio = Column(String)
    location = Column(String)
    website = Column(String)
    bmonth = Column(Integer)
    bday = Column(Integer)
    byear = Column(Integer)
    jmonth = Column(Integer)
    jyear = Column(Integer)
    following = Column(Integer)
    followers = Column(Integer)

    spells = relationship("Spell", back_populates="author")
    
    async def update(self, interaction):
        profile_thread = interaction.guild.get_thread(self.profile_threadid)
        parent_feed = profile_thread.parent
        profile_webhook = await interaction.client.fetch_webhook(self.channel.webhookid)

        # update the profile
        await profile_webhook.edit_message(
            self.profile_messageid, 
            content=self.print_profile(), 
            thread=profile_thread
        )
        await profile_thread.edit(name=f"{self.display_name}'s Profile")

        # update each tweet
        for cast in self.spells:
            edited_thread_message = await profile_webhook.edit_message(
                spell.thread_messageid,
                username=self.display_name,
                avatar_url=self.avatar_url,
                thread=profile_thread
            )
            if(spell.feed_messageid):
                edited_feed_message = await profile_webhook.edit_message(
                    spell.feed_messageid,
                    username=self.display_name,
                    avatar_url=self.avatar_url,
                )
                spell.feed_messageid = edited_feed_message.id


    def print_profile(self):
        result = f"# {self.display_name}"
        result += f"\n-# @{self.handle}"
        if(self.bio):
            result += f"\n{self.bio}"
        result += "\n-# "
        if(self.location):
            result += f"<:location:1344069387333926992> {self.location} | "
        result += f"<:website:1344069349325013057> [{self.website}](https://{self.website}) | "
        if(self.bday and self.bmonth and self.byear):
            result += f"<:birthday:1344068939126149130> {month_list[int(self.bmonth)]} {self.bday}, {self.byear} | "
        if(self.jmonth and self.jyear):
            result += f"<:joined:1344069033342927059> Joined {month_list[self.jmonth]} {self.jyear}"
        result += f"\n-# **{self.following}** Following | **{self.followers}** Followers"
        return(result)

class Spell(Base):
    __tablename__ = "spells"
    id = Column(Integer, primary_key=True)
    accountid = Column(Integer, ForeignKey("accounts.id"))
    author = relationship("Account", back_populates="spells")

    content = Column(String)
    thread_messageid = Column(BigInteger)
    feed_messageid = Column(BigInteger, nullable=True)
    charms = Column(Integer, default=0)
    scribes = Column(Integer, default=0)
    recasts = Column(Integer, default=0)

    recasting_id = Column(Integer, ForeignKey("spells.id"), nullable=True)
    recasting_to = relationship("Spell", back_populates="recasts", remote_side=[id], uselist=False, foreign_keys=[recasting_id]) # Who is it replying to?
    recasts = relationship("Spell", back_populates="recasting_to", foreign_keys=[recasting_id])

    pondering_id = Column(Integer, ForeignKey("spells.id"), nullable=True)
    pondering_to = relationship("Spell", back_populates="ponders", remote_side=[id], uselist=False, foreign_keys=[pondering_id]) # who is it retweeting?
    ponders = relationship("Spell", back_populates="pondering_to", foreign_keys=[pondering_id])

def create_database():
    database = create_engine(f"sqlite:///{DATABASE_NAME}")
    Base.metadata.create_all(database)
    Session = sessionmaker(bind=database)
    session = Session()
    return(session)