from discord.ext import commands
from feed_cog import FeedCog
from dotenv import load_dotenv
import discord, os, sys
from ui_utils import SpellView

from models import User, create_database, Spell

load_dotenv()
DISCORD_CLIENT_TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="s!", intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")
    try:
        session = create_database()
        self_user = session.get(User, client.user.id)
        if(not self_user):
            new_user = User(
                id=client.user.id,
            )
            session.add(new_user)
            session.commit()
        client.db_session = session
        spells = session.query(Spell).all()
        for spell in spells:
            client.add_view(SpellView(spell.id, client, "thread"))
            if(spell.feed_messageid):
                client.add_view(SpellView(spell.id, client, "feed"))
        await client.add_cog(FeedCog(client))
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        sys.exit()

client.run(DISCORD_CLIENT_TOKEN)