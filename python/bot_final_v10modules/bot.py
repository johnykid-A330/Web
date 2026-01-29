"""
Complete Rewrite of F1 League Bot - FIA Registration Module
"""
import discord
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
from discord.ext import commands, tasks
import config
import database
import datetime

# --- SETUP ---
class LeagueBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(LeagueRegistrationView())

    async def on_ready(self):
        print(f"✅ Bot is online as {self.user}")
        try:
            if self.guilds:
                guild = self.guilds[0]
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"🔄 Commands synced to {guild.name}")
            else:
                print("⚠️ No guilds found to sync commands.")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")

bot = LeagueBot()

# --- ⚖️ FIA APPLICANT SYSTEM ---

class FIAModal(Modal):
    """Přihláška pro FIA"""
    def __init__(self):
        super().__init__(title="Přihláška do FIA")
    
    personal_info = TextInput(
        label="Jméno, Příjmení a Věk", 
        placeholder="Např: Jan Novák, 18 let", 
        required=True
    )
    
    experience = TextInput(
        label="Praxe (Simracing & FIA)", 
        placeholder="Jak dlouho jezdíš? Byl jsi už FIA v jiné lize?", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    
    activity = TextInput(
        label="Aktivita", 
        placeholder="Můžeš řešit incidenty po každém závodě?", 
        required=True
    )

    rules = TextInput(
        label="Znalost pravidel", 
        placeholder="Znáš pravidla FIA? Popiš úroveň znalostí.", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    
    conflict = TextInput(
        label="Řešení konfliktů", 
        placeholder="Jak řešíš nadávky v chatu kvůli trestu?", 
        style=discord.TextStyle.paragraph, 
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        answers = {
            "personal_info": self.personal_info.value,
            "experience": self.experience.value,
            "activity": self.activity.value,
            "rules": self.rules.value,
            "conflict": self.conflict.value
        }
        # Using 'steward' as internal role identifier
        await handle_submission(interaction, "steward", "⚖️ FIA", answers)


async def handle_submission(interaction: discord.Interaction, role_value: str, role_name: str, answers: dict):
    # Register in database
    database.register_player(
        user_id=interaction.user.id,
        username=str(interaction.user),
        role=role_value,
        answers=answers
    )
    
    # Success Embed for user
    user_embed = discord.Embed(
        title="✅ Přihláška odeslána!",
        description=f"**Uživatel:** {interaction.user.mention}\n**Role:** {role_name}\n**Info:** Úspěšně uloženo.",
        color=config.EMBED_COLOR_SUCCESS
    )
    user_embed.set_footer(text="Tvoje přihláška byla uložena! 🏁")
    await interaction.response.send_message(embed=user_embed, ephemeral=True)
    
    # Admin Notification
    if config.ADMIN_CHANNEL_ID:
        try:
            admin_channel = interaction.client.get_channel(int(config.ADMIN_CHANNEL_ID))
            if not admin_channel:
                admin_channel = await interaction.client.fetch_channel(int(config.ADMIN_CHANNEL_ID))
                
            if admin_channel:
                admin_embed = discord.Embed(
                    title=f"📢 Nová přihláška: {role_name}!",
                    description=f"**Uživatel:** {interaction.user.mention} ({interaction.user})",
                    color=config.EMBED_COLOR_PRIMARY
                )
                
                # Mapping user friendly names for fields
                field_names = {
                    "personal_info": "👤 Osobní údaje",
                    "experience": "🏎️ Zkušenosti",
                    "activity": "📅 Aktivita",
                    "rules": "📜 Pravidla",
                    "conflict": "🔥 Konflikty"
                }

                for key, val in answers.items():
                    if val:
                        field_name = field_names.get(key, key.replace('_', ' ').title())
                        admin_embed.add_field(name=field_name, value=val, inline=False)
                
                admin_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                admin_embed.timestamp = discord.utils.utcnow()
                
                content = None
                if config.ROLE_ADMIN_ID:
                    content = f"<@&{config.ROLE_ADMIN_ID}>"

                await admin_channel.send(content=content, embed=admin_embed)
        except Exception as e:
            print(f"❌ Error sending admin notification: {e}")


class RoleSelect(Select):
    """Dropdown menu for selecting league role"""
    def __init__(self):
        # Dynamically load enabled roles from config
        options = [
            discord.SelectOption(label=role["name"], value=role["value"], description=role["description"])
            for role in config.LEAGUE_ROLES
        ]
        super().__init__(placeholder="🎯 Select a role...", min_values=1, max_values=1, options=options, custom_id="league_role_select")
    
    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        if val == "steward":
            await interaction.response.send_modal(FIAModal())

class LeagueRegistrationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())


# --- COMMANDS ---

@bot.tree.command(name="rc-registrace", description="Show registration panel (FIA Only)")
async def send_registration(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏆 League Registration System",
        description="Select your role below to apply.\n\n📌 **Available Roles:**\n",
        color=config.EMBED_COLOR_PRIMARY
    )
    for role in config.LEAGUE_ROLES:
        embed.description += f"• {role['name']} - {role['description']}\n"
    
    embed.set_footer(text="⬇️ Opens application form")
    await interaction.channel.send(embed=embed, view=LeagueRegistrationView())
    await interaction.response.send_message("✅ Registration panel sent!", ephemeral=True)


if __name__ == "__main__":
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN)
    else:
        print("❌ Error: DISCORD_TOKEN not found in config.py")
