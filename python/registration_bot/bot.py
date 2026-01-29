"""
Standalone Registration Bot for F1 League
Handles Driver, Steward, and Commentator registrations.
"""
import discord
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import config
import database
import datetime

# --- MOJIFY helper ---
def load_mojify_patch():
    # Patch discord.py if needed? No, standard is fine.
    pass

# --- 🏎️ DRIVER MODAL ---
class DriverModal(Modal):
    """Specific form for Drivers"""
    def __init__(self):
        super().__init__(title="Driver Application")
    
    ea_id = TextInput(label="EA ID", placeholder="Enter your EA ID...", required=True)
    team_choice = TextInput(
        label="Team (ferrari, mercedes, redbull...)",
        placeholder="Choose: ferrari, mercedes, redbull, mclaren...",
        required=True
    )
    silverstone_tt = TextInput(label="Silverstone Time (TT)", placeholder="Example: 1:26.450", required=True)
    baku_tt = TextInput(label="Baku Time (TT)", placeholder="Example: 1:40.120", required=True)
    experience = TextInput(
        label="Experience", 
        placeholder="Previous leagues, wheel or controller etc.", 
        style=discord.TextStyle.paragraph, 
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Validate team choice
        team_id = self.team_choice.value.lower().strip()
        
        if team_id not in config.TEAMS:
            available_teams = ", ".join(config.TEAMS.keys())
            await interaction.response.send_message(
                f"❌ Invalid team! Choose from: {available_teams}",
                ephemeral=True
            )
            return
        
        # Check if team is full
        if database.is_team_full(team_id):
            team_name = config.TEAMS[team_id]["name"]
            await interaction.response.send_message(
                f"❌ Team {team_name} is full! Choose another team.",
                ephemeral=True
            )
            return
        
        answers = {
            "ea_id": self.ea_id.value,
            "team": team_id,
            "silverstone_tt": self.silverstone_tt.value,
            "baku_tt": self.baku_tt.value,
            "experience": self.experience.value
        }
        await handle_submission(interaction, "driver", "🏎️ Driver", answers)

# --- ⚖️ STEWARD MODAL ---
class StewardModal(Modal):
    """Specific form for Stewards"""
    def __init__(self):
        super().__init__(title="Steward Application")
    
    ea_id = TextInput(label="EA ID", placeholder="Enter your EA ID...", required=True)
    rules = TextInput(
        label="Rules Knowledge", 
        placeholder="How well do you know F1 rules? (track limits, blue flags...)", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    conflict = TextInput(
        label="Conflict Resolution", 
        placeholder="How would you handle an incident involving a friend?", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    availability = TextInput(label="Availability", placeholder="Which days/times can you review incidents?", required=True)
    prev_exp = TextInput(label="Previous Experience", placeholder="Leagues where you were a steward", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        answers = {
            "ea_id": self.ea_id.value,
            "rules": self.rules.value,
            "conflict": self.conflict.value,
            "availability": self.availability.value,
            "prev_exp": self.prev_exp.value
        }
        await handle_submission(interaction, "steward", "⚖️ Steward", answers)

# --- 🎙️ COMMENTATOR MODAL ---
class CommentatorModal(Modal):
    """Specific form for Commentators"""
    def __init__(self):
        super().__init__(title="Commentator Application")
    
    ea_id = TextInput(label="EA ID", placeholder="Enter your EA ID...", required=True)
    setup = TextInput(label="Technical Setup", placeholder="Streaming gear, internet speed, mic", required=True)
    portfolio = TextInput(label="Portfolio/Links", placeholder="Links to previous work (Twitch, YT)", required=True)
    style_commitment = TextInput(
        label="Style & Commitment", 
        placeholder="Hype or Analytic? Can you do every weekend?", 
        style=discord.TextStyle.paragraph,
        required=True
    )
    vod_review = TextInput(
        label="Race Analysis (VOD)",
        placeholder="How would you analyze a specific race segment?",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        answers = {
            "ea_id": self.ea_id.value,
            "setup": self.setup.value,
            "portfolio": self.portfolio.value,
            "style_commitment": self.style_commitment.value,
            "vod_review": self.vod_review.value
        }
        await handle_submission(interaction, "commentator", "🎙️ Commentator", answers)


# --- 📝 REVIEW MODAL ---
class ReviewModal(Modal):
    def __init__(self, action: str, target_user: discord.Member, role_value: str, role_name: str, original_msg: discord.Message):
        titles = {
            "approve": "Approve Application",
            "reject": "Reject Application",
            "review": "Send to Review",
            "testing": "Send to Testing"
        }
        super().__init__(title=titles.get(action, "Application"))
        self.action = action
        self.target_user = target_user
        self.role_value = role_value
        self.role_name = role_name
        self.original_msg = original_msg
    
    comment = TextInput(
        label="Comment / Reason", 
        placeholder="Message for the user...", 
        style=discord.TextStyle.paragraph, 
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        final_role_id = None
        applicant_role_id = None
        
        if self.role_value == "driver":
            final_role_id = config.ROLE_DRIVER
            applicant_role_id = config.ROLE_DRIVER_APPLICANT
        elif self.role_value == "steward":
            final_role_id = config.ROLE_STEWARD
            applicant_role_id = config.ROLE_STEWARD_APPLICANT
        elif self.role_value == "commentator":
            final_role_id = config.ROLE_COMMENTATOR
            applicant_role_id = config.ROLE_COMMENTATOR_APPLICANT

        try:
            guild = interaction.guild
            member = guild.get_member(self.target_user.id)
            if not member:
                member = await guild.fetch_member(self.target_user.id)
            
            # Roles logic
            role_to_add_id = None
            if self.action == "approve": role_to_add_id = final_role_id
            elif self.action == "review": role_to_add_id = config.ROLE_UNDER_REVIEW
            elif self.action == "testing": role_to_add_id = config.ROLE_UNDER_TESTING
            
            roles_to_remove_ids = set()
            if config.AUTO_JOIN_ROLE_ID: roles_to_remove_ids.add(int(config.AUTO_JOIN_ROLE_ID))
            
            if self.action in ["approve", "reject"]:
                if config.ROLE_DRIVER_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_DRIVER_APPLICANT))
                if config.ROLE_STEWARD_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_STEWARD_APPLICANT))
                if config.ROLE_COMMENTATOR_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_COMMENTATOR_APPLICANT))
                if config.ROLE_UNDER_REVIEW: roles_to_remove_ids.add(int(config.ROLE_UNDER_REVIEW))
                if config.ROLE_UNDER_TESTING: roles_to_remove_ids.add(int(config.ROLE_UNDER_TESTING))
            elif self.action == "testing":
                if applicant_role_id: roles_to_remove_ids.add(int(applicant_role_id))
                if config.ROLE_UNDER_REVIEW: roles_to_remove_ids.add(int(config.ROLE_UNDER_REVIEW))
            elif self.action == "review":
                if applicant_role_id: roles_to_remove_ids.add(int(applicant_role_id))

            current_role_ids = [r.id for r in member.roles]
            new_roles = [guild.get_role(rid) for rid in current_role_ids if rid not in roles_to_remove_ids]
            
            if role_to_add_id:
                target_role = guild.get_role(int(role_to_add_id))
                if target_role and target_role not in new_roles:
                    new_roles.append(target_role)
            
            new_roles = list(set([r for r in new_roles if r is not None]))
            await member.edit(roles=new_roles)
            
        except Exception as e:
            print(f"❌ Error updating roles: {e}")

        try:
            target_user_mention = self.target_user.mention
            role_display = self.role_name
            admin_mention = interaction.user.mention
            
            status_map = {
                "approve": ("APPROVED", "✅"),
                "reject": ("REJECTED", "❌"),
                "review": ("moved to REVIEW", "🔍"),
                "testing": ("moved to TESTING", "🧪")
            }
            status_text, emoji = status_map.get(self.action, ("PROCESSED", "⚙️"))
            
            await self.original_msg.delete()
            
            summary = f"{emoji} Application for **{target_user_mention}** ({role_display}) was **{status_text}** by {admin_mention}."
            if self.comment.value:
                summary += f"\n> **Comment:** {self.comment.value}"
            
            if self.action in ["review", "testing"]:
                clean_role_name = self.role_name.replace(" ", "_")
                custom_id = f"trial_finish:{self.target_user.id}:{self.role_value}:{clean_role_name}"
                
                dynamic_view = View(timeout=None)
                dynamic_view.add_item(discord.ui.Button(
                    label="✅ Finished (Trial)", 
                    style=discord.ButtonStyle.green, 
                    custom_id=custom_id,
                    emoji="✅"
                ))
                await interaction.channel.send(summary, view=dynamic_view)
            else:
                summary_msg = await interaction.channel.send(summary)
                await summary_msg.delete(delay=86400)
            
            if not interaction.response.is_done():
                await interaction.response.send_message("Status updated!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

        try:
            dm_map = {
                "approve": f"🎉 Your application for **{self.role_name}** was **APPROVED**! Welcome to the team.",
                "reject": f"Your application for **{self.role_name}** was **REJECTED**.",
                "review": f"Your application for **{self.role_name}** is now **UNDER REVIEW**. We will contact you soon!",
                "testing": f"Your application for **{self.role_name}** has moved to **TESTING PHASE**. Get ready!"
            }
            msg = dm_map.get(self.action, "Your application status has been updated.")
            if self.comment.value:
                msg += f"\n\n**Admin Comment:** {self.comment.value}"
            await self.target_user.send(msg)
        except:
            pass

# --- 📝 REVIEW BUTTONS ---
class ApplicationReviewView(View):
    def __init__(self, target_user: discord.Member, role_value: str, role_name: str):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.role_value = role_value
        self.role_name = role_name

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, custom_id="app_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="approve", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Review", style=discord.ButtonStyle.blurple, custom_id="app_review")
    async def review_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="review", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Testing", style=discord.ButtonStyle.gray, custom_id="app_testing")
    async def testing_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="testing", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red, custom_id="app_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="reject", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

# --- GLOBAL SUBMISSION HANDLER ---
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
        title="✅ Application Sent!",
        description=f"**User:** {interaction.user.mention}\n**Role:** {role_name}\n**EA ID:** `{answers.get('ea_id')}`",
        color=config.EMBED_COLOR_SUCCESS
    )
    user_embed.set_footer(text="Your application has been saved! 🏁")
    await interaction.response.send_message(embed=user_embed, ephemeral=True)

    # Assign Applicant Role
    try:
        app_role_id = None
        if role_value == "driver": app_role_id = config.ROLE_DRIVER_APPLICANT
        elif role_value == "steward": app_role_id = config.ROLE_STEWARD_APPLICANT
        elif role_value == "commentator": app_role_id = config.ROLE_COMMENTATOR_APPLICANT
        
        if app_role_id:
            role_to_add = interaction.guild.get_role(int(app_role_id))
            if role_to_add: await interaction.user.add_roles(role_to_add)
    except Exception as e:
        print(f"❌ Error assigning applicant role: {e}")

    # Admin Notification
    if config.ADMIN_CHANNEL_ID:
        try:
            admin_channel = interaction.client.get_channel(int(config.ADMIN_CHANNEL_ID))
            if not admin_channel:
                admin_channel = await interaction.client.fetch_channel(int(config.ADMIN_CHANNEL_ID))
                
            if admin_channel:
                admin_embed = discord.Embed(
                    title=f"📢 New {role_name} Application!",
                    description=f"**User:** {interaction.user.mention} ({interaction.user})\n**EA ID:** `{answers.get('ea_id')}`",
                    color=config.EMBED_COLOR_PRIMARY
                )
                
                for key, val in answers.items():
                    if key != 'ea_id' and val:
                        field_name = key.replace('_', ' ').title()
                        admin_embed.add_field(name=f"🔹 {field_name}", value=val, inline=False)
                
                admin_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                admin_embed.timestamp = discord.utils.utcnow()
                
                view = ApplicationReviewView(target_user=interaction.user, role_value=role_value, role_name=role_name)
                
                content = None
                if config.ROLE_ADMIN_ID:
                    content = f"<@&{config.ROLE_ADMIN_ID}>"

                await admin_channel.send(content=content, embed=admin_embed, view=view)
        except Exception as e:
            print(f"❌ Error sending admin notification: {e}")

class RoleSelect(Select):
    """Dropdown menu for selecting league role"""
    def __init__(self):
        options = [
            discord.SelectOption(label=role["name"], value=role["value"], description=role["description"])
            for role in config.LEAGUE_ROLES
        ]
        super().__init__(placeholder="🎯 Select a role...", min_values=1, max_values=1, options=options, custom_id="league_role_select")
    
    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        if val == "driver":
            await interaction.response.send_modal(DriverModal())
        elif val == "steward":
            await interaction.response.send_modal(StewardModal())
        elif val == "commentator":
            await interaction.response.send_modal(CommentatorModal())

class LeagueRegistrationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

class RegistrationBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        self.add_view(LeagueRegistrationView())
    
    async def on_ready(self):
        print(f"🤖 Registration Bot is online as: {self.user}")
        try:
            guild = discord.Object(id=self.guilds[0].id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Synced commands to {self.guilds[0].name}")
        except Exception as e:
            print(f"❌ Error syncing: {e}")

    async def on_interaction(self, interaction: discord.Interaction):
        # Handle Persistent Trial Logic via specific custom_id pattern
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("trial_finish:"):
                try:
                    _, user_id_str, role_value, role_name_clean = custom_id.split(":")
                    user_id = int(user_id_str)
                    role_name = role_name_clean.replace("_", " ")
                    
                    guild = interaction.guild
                    target_user = guild.get_member(user_id)
                    if not target_user: target_user = await guild.fetch_member(user_id)
                    
                    player = database.get_player(user_id)
                    answers = player.get("answers", {}) if player else {}
                    
                    admin_embed = discord.Embed(
                        title=f"📢 Decision Needed: {role_name}!",
                        description=f"**User:** {target_user.mention}\n**Status:** Trial/Review Finished",
                        color=config.EMBED_COLOR_PRIMARY
                    )
                    view = ApplicationReviewView(target_user=target_user, role_value=role_value, role_name=role_name)
                    
                    await interaction.message.delete(delay=86400)
                    await interaction.channel.send(embed=admin_embed, view=view)
                    if not interaction.response.is_done(): await interaction.response.defer()
                except Exception as e:
                    print(f"Error: {e}")

bot = RegistrationBot()

@bot.tree.command(name="rc-registrace", description="Show registration panel")
async def send_registration(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏆 League Registration System",
        description="Select your role and fill out the application form.\n\n📌 **Available Roles:**\n",
        color=config.EMBED_COLOR_PRIMARY
    )
    for role in config.LEAGUE_ROLES:
        embed.description += f"• {role['name']} - {role['description']}\n"
    embed.set_footer(text="⬇️ Select role below to open the form")
    await interaction.channel.send(embed=embed, view=LeagueRegistrationView())
    await interaction.response.send_message("✅ Registration panel sent!", ephemeral=True)

@bot.tree.command(name="rc-profil", description="View your application details")
async def my_profile(interaction: discord.Interaction):
    player = database.get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ No application found.", ephemeral=True)
        return
    embed = discord.Embed(title="👤 Your Profile", color=config.EMBED_COLOR_PRIMARY)
    embed.add_field(name="Role", value=player["role"].title(), inline=True)
    for k, v in player.get("answers", {}).items():
        if v: embed.add_field(name=k.replace('_', ' ').title(), value=v, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    import config
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN)
    else:
        print("❌ Chyba: DISCORD_TOKEN v config.py není nastaven!")
