from discord.ext import commands
from feed_cog import feed_cog
from dotenv import load_dotenv
import discord, os, sys

from models import User, create_database

load_dotenv()
DISCORD_CLIENT_TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="s!", intents=intents)

async def prepareBot(client, session):
    await client.add_cog(ImageCog(client, session))

@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")
    try:
        session = create_database()
        self_user = session.get(user, client.user.id)
        if(not self_user):
            new_user = User(
                id=client.user.id,
                is_admin=True
            )
            session.add(new_user)
            session.commit()
        await client.add_cog(ChatCog(client, session))
        await prepareBot()
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        sys.exit()

client.run(DISCORD_CLIENT_TOKEN)