from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_NAME = os.getenv("SQLITE_DATABASE_NAME")

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
    user = relationship("User", back_populates="accounts")
    channel = relationship("Channel", back_populates="accounts")

    discord_userid = Column(Integer)
    profile_threadid = Column(Integer)
    profile_messageid = Column(Integer)
    spells_threadid = Column(Integer)
    
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
    def update_tweet_num():
        pass


def create_database():
    database = create_engine(f"sqlite:///{DATABASE_NAME}")
    Base.metadata.create_all(database)
    Session = sessionmaker(bind=database)
    session = Session()
    return(session)