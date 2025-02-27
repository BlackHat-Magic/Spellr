from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv
import os

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

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    accounts = relationship("Account", back_populates="user")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    accounts = relationship("Account", back_populates="channel")

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
    webhookid = Column(Integer)
    
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

    casts = relationship("Cast", back_populates="author")
    
    async def update(self, interaction):
        parent_feed = profile_thread.parent
        profile_webhook = await interaction.client.fetch_webhook(self.webhookid)
        profile_thread = interaction.guild.get_thread(self.profile_threadid)

        # update the profile
        await profile_webhook.edit_message(
            self.profile_messageid, 
            content=self.print_profile(), 
            username=self.display_name, 
            avatar_url=interaction.user.avatar.url,
            thread=profile_thread
        )
        await profile_thread.edit(name=f"{self.display_name}'s Profile")

        # update each tweet
        for cast in self.casts:
            message_content = await interaction.client.fetch_message(cast.messageid).content
            await profile_webhook.edit_message(
                self.profile_messageid,
                content=format_cast(message_content),
                username=self.display_name,
                avatar_url=interaction.user.avatar.url,
                thread=profile_thread
            )


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

class Cast(Base):
    __tablename__ = "casts"
    id = Column(Integer)

    accountid = Column(Integer, ForeignKey("accounts.id"))
    author = relationship("Account", back_populates="casts")
    messageid = Column(Integer)
    likes = Column(Integer)
    recasts = Column(Integer)

    parentid = Column(Integer, ForeignKey("casts.id"), nullable=True)
    parent = relationship("Cast", back_populates="replies")

    replies = relationship("Cast", back_populates="parent")

def create_database():
    database = create_engine(f"sqlite:///{DATABASE_NAME}")
    Base.metadata.create_all(database)
    Session = sessionmaker(bind=database)
    session = Session()
    return(session)