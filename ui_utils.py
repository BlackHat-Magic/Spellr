import discord

class Register(discord.ui.Modal, title="Register a Spellr Account"):
    username = discord.ui.TextInput(
        label="Handle",
        placeholder="@ZacDorothy",
        required=True,
        max_length=32
    )
    display_name = discord.ui.TextInput(
        label="Display Name (Optional)",
        placeholder="Not Treelom Tusk",
        required=False,
        max_length=32
    )
    bio = discord.ui.TextInput(
        label="Bio (Optional)",
        placeholder="Founder at Tooter (Now Z), now I make Spellr.",
        style=discord.TextStyle.long,
        required=False,
        max_length=512,
    )

    async def on_submit(self, interaction: discord.Interaction):
        db_channel = lmao
        await interaction.response.send_message("")