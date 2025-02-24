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

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    accounts = relationship("Account", back_populates="channel")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    channel = relationship("Channels", back_populates="accounts")

    discord_userid = Column(Integer)
    
    handle = Column(String)
    display_name = Column(String)
    def update_tweet_num():
        pass


def create_database():
    database = create_engine(f"sqlite:///{DATABASE_NAME}")
    Base.metadata.create_all(databse)
    Session = sessionmaker(bind=database)
    session = Session()
    return(session)