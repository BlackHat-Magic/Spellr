from discord.ext import commands
from feed_cog import FeedCog
from dotenv import load_dotenv
import discord, os, sys
from ui_utils import SpellView

from models import User, create_database, Spell

load_dotenv()
DISCORD_CLIENT_TOKEN = os.getenv("DISCORD_CLIENT_TOKEN")

SHARE_EMOJI_MARKDOWN = os.getenv("SHARE_EMOJI_MARKDOWN")
LOCATION_EMOJI_MARKDOWN = os.getenv("LOCATION_EMOJI_MARKDOWN")
WEBSITE_EMOJI_MARKDOWN = os.getenv("WEBSITE_EMOJI_MARKDOWN")
CHARM_EMOJI_MARKDOWN = os.getenv("CHARM_EMOJI_MARKDOWN")
RECAST_EMOJI_MARKDOWN = os.getenv("RECAST_EMOJI_MARKDOWN")
ANALYTICS_EMOJI_MARKDOWN = os.getenv("ANALYTICS_EMOJI_MARKDOWN")
JOIN_EMOJI_MARKDOWN = os.getenv("JOIN_EMOJI_MARKDOWN")
SCRIBE_EMOJI_MARKDOWN = os.getenv("SCRIBE_EMOJI_MARKDOWN")
BIRTHDAY_EMOJI_MARKDOWN = os.getenv("BIRTHDAY_EMOJI_MARKDOWN")
PONDER_EMOJI_MARKDOWN = os.getenv("PONDER_EMOJI_MARKDOWN")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="s!", intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")
    try:
        # database setup
        session = create_database()
        self_user = session.get(User, client.user.id)
        if(not self_user):
            new_user = User(
                id=client.user.id,
            )
            session.add(new_user)
            session.commit()
        client.db_session = session

        # persistent views
        spells = session.query(Spell).all()
        for spell in spells:
            client.add_view(SpellView(spell.id, client, "thread"))
            if(spell.feed_messageid):
                client.add_view(SpellView(spell.id, client, "feed"))
        
        client.emojis = {}
        client.emojis["share"] = SHARE_EMOJI_MARKDOWN
        client.emojis["location"] = LOCATION_EMOJI_MARKDOWN
        client.emojis["website"] = WEBSITE_EMOJI_MARKDOWN
        client.emojis["charm"] = CHARM_EMOJI_MARKDOWN
        client.emojis["recast"] = RECAST_EMOJI_MARKDOWN
        client.emojis["analytics"] = ANALYTICS_EMOJI_MARKDOWN
        client.emojis["join"] = JOIN_EMOJI_MARKDOWN
        client.emojis["scribe"] = SCRIBE_EMOJI_MARKDOWN
        client.emojis["birthday"] = BIRTHDAY_EMOJI_MARKDOWN
        client.emojis["ponder"] = PONDER_EMOJI_MARKDOWN

        # add cog
        await client.add_cog(FeedCog(client))
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        sys.exit()

client.run(DISCORD_CLIENT_TOKEN)