"""
Discord League Registration Bot - Role-Specific Version
Advanced version with unique Modals for Driver, Steward, and Commentator
"""
import discord
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
from discord.ext import tasks  # MODULE 10: Automated notifications
import config
import database
import datetime
import csv
import io

# --- 🗓️ ATTENDANCE VIEW ---
class AttendanceBoard(View):
    """View for race signups with persistent buttons (Sesh-style)"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Jezdec", style=discord.ButtonStyle.green, custom_id="att_driver", emoji="🏎️")
    async def driver_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_attendance(interaction.user.id, str(interaction.user), "Driver")
        await self.update_message(interaction)

    @discord.ui.button(label="Komentátor", style=discord.ButtonStyle.blurple, custom_id="att_comm", emoji="🎙️")
    async def comm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_attendance(interaction.user.id, str(interaction.user), "Commentator")
        await self.update_message(interaction)

    @discord.ui.button(label="Maršál", style=discord.ButtonStyle.gray, custom_id="att_marshal", emoji="⚖️")
    async def marshal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_attendance(interaction.user.id, str(interaction.user), "Marshal")
        await self.update_message(interaction)

    @discord.ui.button(label="Možná", style=discord.ButtonStyle.secondary, custom_id="att_maybe", emoji="🤔")
    async def maybe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_attendance(interaction.user.id, str(interaction.user), "Maybe")
        await self.update_message(interaction)

    @discord.ui.button(label="Neúčastním se", style=discord.ButtonStyle.red, custom_id="att_no", emoji="❌")
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.update_attendance(interaction.user.id, str(interaction.user), "Declined")
        await self.update_message(interaction)


    async def update_message(self, interaction: discord.Interaction):
        """Re-render the attendance list with a premium Sesh-like look"""
        data = database.get_attendance()
        
        # Lists for categories
        drivers = []
        commentators = []
        marshals = []
        
        maybe = []
        declined = []

        # Process all entries based on saved STATUS
        for user_id_str, entry in data.items():
            user_id = int(user_id_str)
            status = entry.get('status', 'Declined')
            mention = f"<@{user_id}>"
            
            if status == "Driver":
                drivers.append((user_id, mention))  # Store tuple for sorting
            elif status == "Commentator":
                commentators.append(mention)
            elif status == "Marshal":
                marshals.append(mention)
            elif status == "Accepted": # Fallback for old data
                 drivers.append((user_id, mention))
            elif status == "Maybe":
                maybe.append(mention)
            elif status == "Declined":
                declined.append(mention)

        # MODULE 3: Reserve Priority - Split drivers into Main Grid and Reserves
        main_grid = []
        reserves = []
        
        # Sort drivers by role (main drivers first, then reserves)
        try:
            guild = interaction.guild
            reserve_role_id = int(config.ROLE_RESERVE) if config.ROLE_RESERVE else None
            
            for user_id, mention in drivers:
                member = guild.get_member(user_id)
                if member and reserve_role_id:
                    # Check if user has reserve role
                    has_reserve_role = any(role.id == reserve_role_id for role in member.roles)
                    if has_reserve_role:
                        reserves.append(mention)
                    else:
                        main_grid.append(mention)
                else:
                    # If can't determine role, add to main grid
                    main_grid.append(mention)
            
            # Enforce grid limit
            if len(main_grid) > config.MAX_MAIN_GRID_SIZE:
                # Move excess to reserves
                overflow = main_grid[config.MAX_MAIN_GRID_SIZE:]
                main_grid = main_grid[:config.MAX_MAIN_GRID_SIZE]
                reserves = overflow + reserves
                
        except Exception as e:
            print(f"❌ Error processing reserve priority: {e}")
            # Fallback: all drivers in one list
            main_grid = [m for _, m in drivers]
            reserves = []

        total = len(main_grid) + len(reserves) + len(commentators) + len(marshals) + len(maybe)
        
        embed = discord.Embed(
            title="🏁 Nadcházející závod: Registrace",
            description=f"Celkem přihlášeno: **{total}**",
            color=0x2b2d31, # Professional dark grey
            timestamp=discord.utils.utcnow()
        )
        
        # Helper to format lists
        def fmt_list(lst, numbered=True):
            if not lst: return "_Nikdo_"
            if numbered:
                return "\n".join([f"{i+1}. {u}" for i, u in enumerate(lst)])
            return ", ".join(lst)
            
        # Add Fields - MODULE 3: Separate Main Grid and Reserves
        if main_grid or reserves:
            embed.add_field(
                name=f"🏁 Main Grid ({len(main_grid)}/{config.MAX_MAIN_GRID_SIZE})", 
                value=fmt_list(main_grid), 
                inline=False
            )
            if reserves:
                embed.add_field(
                    name=f"🔄 Reserves ({len(reserves)})", 
                    value=fmt_list(reserves, numbered=False), 
                    inline=False
                )
        else:
            embed.add_field(name="🏎️ Jezdci (0)", value="_Nikdo_", inline=False)
            
        embed.add_field(name=f"🎙️ Komentátoři ({len(commentators)})", value=fmt_list(commentators, numbered=False), inline=False)
        embed.add_field(name=f"⚖️ Maršálové ({len(marshals)})", value=fmt_list(marshals, numbered=False), inline=False)

        embed.add_field(name=f"🤔 Možná ({len(maybe)})", value=fmt_list(maybe, numbered=False), inline=False)
        embed.add_field(name=f"❌ Neúčastním se ({len(declined)})", value=fmt_list(declined, numbered=False), inline=False)
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        embed.set_footer(text="Klikni na tlačítka níže pro registraci")
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.message.edit(embed=embed, view=self)

# --- 🏎️ DRIVER MODAL ---
class DriverModal(Modal):
    """Specific form for Drivers"""
    def __init__(self):
        super().__init__(title="Přihláška Jezdce")
    
    ea_id = TextInput(label="EA ID", placeholder="Zadej své EA ID...", required=True)
    silverstone_tt = TextInput(label="Silverstone Čas (TT)", placeholder="Příklad: 1:26.450", required=True)
    baku_tt = TextInput(label="Baku Čas (TT)", placeholder="Příklad: 1:40.120", required=True)
    experience = TextInput(
        label="Zkušenosti", 
        placeholder="Předchozí ligy, volant nebo ovladač atd.", 
        style=discord.TextStyle.paragraph, 
        required=False
    )
    skill_review = TextInput(
        label="Ukázka jízdy",
        placeholder="Odkaz na klip nebo popis tvé rychlosti/dovedností",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        answers = {
            "ea_id": self.ea_id.value,
            "silverstone_tt": self.silverstone_tt.value,
            "baku_tt": self.baku_tt.value,
            "experience": self.experience.value,
            "skill_review": self.skill_review.value
        }
        await handle_submission(interaction, "driver", "🏎️ Jezdec", answers)

# --- ⚖️ STEWARD MODAL ---
class StewardModal(Modal):
    """Specific form for Stewards"""
    def __init__(self):
        super().__init__(title="Přihláška Stewarda")
    
    ea_id = TextInput(label="EA ID", placeholder="Zadej své EA ID...", required=True)
    rules = TextInput(
        label="Znalost pravidel", 
        placeholder="Jak dobře znáš pravidla F1? (limity tratě, modré vlajky...)", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    conflict = TextInput(
        label="Řešení konfliktů", 
        placeholder="Jak bys řešil incident, ve kterém figuruje kamarád?", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    availability = TextInput(label="Dostupnost", placeholder="Které dny/časy můžeš řešit incidenty?", required=True)
    prev_exp = TextInput(label="Předchozí zkušenosti", placeholder="Ligy, kde jsi dělal stewarda", required=False)

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
        super().__init__(title="Přihláška Komentátora")
    
    ea_id = TextInput(label="EA ID", placeholder="Zadej své EA ID...", required=True)
    setup = TextInput(label="Technické vybavení", placeholder="Streamovací zařízení, rychlost netu, mikrofon", required=True)
    portfolio = TextInput(label="Portfolio/Odkazy", placeholder="Odkazy na tvou předchozí práci (Twitch, YT)", required=True)
    style_commitment = TextInput(
        label="Styl a odhodlání", 
        placeholder="Hype nebo Analytik? Můžeš každý víkend?", 
        style=discord.TextStyle.paragraph,
        required=True
    )
    vod_review = TextInput(
        label="Analýza závodu (VOD)",
        placeholder="Jak bys analyzoval konkrétní segment závodu?",
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
        await handle_submission(interaction, "commentator", "🎙️ Komentátor", answers)

# --- ⚖️ MIA INCIDENT SYSTEM ---
class MIAReportModal(Modal):
    """Modal for drivers to report race incidents"""
    def __init__(self):
        super().__init__(title="Nahlásit incident (MIA)")

    driver_involved = TextInput(label="Zapojení jezdci", placeholder="Kdo další byl v incidentu?", required=True)
    lap_session = TextInput(label="Kolo / Část", placeholder="Např: Kolo 12 / Kvalifikace", required=True)
    description = TextInput(
        label="Popis", 
        placeholder="Co se stalo? Buď konkrétní.", 
        style=discord.TextStyle.paragraph, 
        required=True
    )
    evidence = TextInput(label="Důkaz (Video)", placeholder="Odkaz na klip (YouTube, Twitch...)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Notify user
        await interaction.response.send_message("✅ Tvoje hlášení bylo odesláno komisařům!", ephemeral=True)
        
        # Send to Incident Channel for Admins
        if config.INCIDENT_REPORT_CHANNEL_ID:
            channel = interaction.client.get_channel(int(config.INCIDENT_REPORT_CHANNEL_ID))
            if not channel: channel = await interaction.client.fetch_channel(int(config.INCIDENT_REPORT_CHANNEL_ID))
            
            embed = discord.Embed(
                title="🚨 Nové Hlášení Incidentu",
                description=f"**Nahlásil:** {interaction.user.mention}\n**Zapojení:** {self.driver_involved.value}\n**Část:** {self.lap_session.value}",
                color=config.EMBED_COLOR_ERROR,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="🔹 Popis", value=self.description.value, inline=False)
            embed.add_field(name="🎥 Důkaz", value=self.evidence.value, inline=False)
            
            # Admins will have a "Process Decision" button here
            view = MIAReviewView(reporter=interaction.user, report_data={
                "drivers": self.driver_involved.value,
                "session": self.lap_session.value,
                "desc": self.description.value,
                "link": self.evidence.value
            })
            
            # Construct ping string for Marshals
            ping_content = ""
            if hasattr(config, 'MIA_REPORT_PING_ROLES') and config.MIA_REPORT_PING_ROLES:
                 ping_content = " ".join([f"<@&{role_id}>" for role_id in config.MIA_REPORT_PING_ROLES])
            
            await channel.send(content=ping_content, embed=embed, view=view)

class MIAReviewView(View):
    """View for admins to process an incident and post to documents"""
    def __init__(self, reporter, report_data):
        super().__init__(timeout=None)
        self.reporter = reporter
        self.report_data = report_data

    @discord.ui.button(label="Vydat MIA Dokument", style=discord.ButtonStyle.blurple, emoji="📄")
    async def post_decision(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MIADecisionModal(self.reporter, self.report_data, interaction.message))

class MIADecisionModal(Modal):
    """Final decision modal for MIA Document"""
    def __init__(self, reporter, report_data, original_msg):
        super().__init__(title="Konečné rozhodnutí MIA")
        self.reporter = reporter
        self.report_data = report_data
        self.original_msg = original_msg

    decision = TextInput(label="Verdikt / Trest", placeholder="Např: 5s Penalizace & 2 Trestné body", style=discord.TextStyle.paragraph, required=True)
    reasoning = TextInput(label="Odůvodnění", placeholder="Vysvětli rozhodnutí...", style=discord.TextStyle.paragraph, required=True)
    penalty_points = TextInput(label="Trestné body (MODULE 1)", placeholder="0", required=False, default="0")  # NEW
    penalized_user = TextInput(label="Potrestaný jezdec (mention)", placeholder="@Username", required=False)  # NEW

    async def on_submit(self, interaction: discord.Interaction):
        # MODULE 1: Process penalty points
        penalty_user_id = None
        points_to_add = 0
        
        try:
            if self.penalty_points.value and self.penalty_points.value.strip():
                points_to_add = int(self.penalty_points.value.strip())
                
                # Parse user mention
                if self.penalized_user.value:
                    mention = self.penalized_user.value.strip()
                    # Extract user ID from mention <@123456789>
                    if mention.startswith("<@") and mention.endswith(">"):
                        mention = mention.replace("<@!", "").replace("<@", "").replace(">", "")
                        penalty_user_id = int(mention)
        except ValueError:
            await interaction.response.send_message("❌ Neplatný formát trestných bodů!", ephemeral=True)
            return
        
        # Add penalty points if specified
        limit_exceeded = False
        total_penalty_points = 0
        if penalty_user_id and points_to_add > 0:
            result = database.add_penalty_points(
                user_id=penalty_user_id,
                points=points_to_add,
                reason=self.decision.value,
                incident_id=f"MIA_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            if result["success"]:
                limit_exceeded = result["limit_exceeded"]
                total_penalty_points = result["total_points"]
        
        # Send to MIA Documents Channel
        if config.MIA_DOCS_CHANNEL_ID:
            channel = interaction.client.get_channel(int(config.MIA_DOCS_CHANNEL_ID))
            if not channel: channel = await interaction.client.fetch_channel(int(config.MIA_DOCS_CHANNEL_ID))
            
            doc_embed = discord.Embed(
                title="⚖️ MIA Oficiální Dokument",
                color=0x2b2d31, # Dark professional color
                timestamp=discord.utils.utcnow()
            )
            doc_embed.add_field(name="📌 ZÁVODNÍ INCIDENT", value=f"**Část:** {self.report_data['session']}\n**Zapojení:** {self.report_data['drivers']}", inline=False)
            doc_embed.add_field(name="💬 VERDIKT", value=f"```\n{self.decision.value}\n```", inline=False)
            doc_embed.add_field(name="📔 ODŮVODNĚNÍ", value=self.reasoning.value, inline=False)
            
            # Add penalty info if applicable
            if penalty_user_id and points_to_add > 0:
                doc_embed.add_field(
                    name="⚠️ TRESTNÉ BODY", 
                    value=f"<@{penalty_user_id}> obdržel **{points_to_add} trestných bodů**\nCelkem: **{total_penalty_points}/{config.PENALTY_POINTS_LIMIT}**",
                    inline=False
                )
            
            doc_embed.set_footer(text=f"Nahlásil {self.reporter.display_name}")

            # Construct ping string
            ping_content = ""
            if hasattr(config, 'MIA_PING_ROLES') and config.MIA_PING_ROLES:
                 ping_content = " ".join([f"<@&{role_id}>" for role_id in config.MIA_PING_ROLES])

            await channel.send(content=ping_content, embed=doc_embed)
            await self.original_msg.delete()
            
        # MODULE 1: Handle penalty limit exceeded
        if limit_exceeded and penalty_user_id:
            try:
                guild = interaction.guild
                penalized_member = guild.get_member(penalty_user_id)
                if not penalized_member:
                    penalized_member = await guild.fetch_member(penalty_user_id)
                
                # Send warning to admin channel
                if config.ADMIN_CHANNEL_ID:
                    admin_channel = interaction.client.get_channel(int(config.ADMIN_CHANNEL_ID))
                    if not admin_channel:
                        admin_channel = await interaction.client.fetch_channel(int(config.ADMIN_CHANNEL_ID))
                    
                    warning_embed = discord.Embed(
                        title="🚨 LIMIT TRESTNÝCH BODŮ PŘEKROČEN!",
                        description=f"**Jezdec:** {penalized_member.mention}\n**Celkové body:** {total_penalty_points}/{config.PENALTY_POINTS_LIMIT}",
                        color=config.EMBED_COLOR_ERROR,
                        timestamp=discord.utils.utcnow()
                    )
                    warning_embed.add_field(name="Akce", value="Bot automaticky přidělil Banned roli.", inline=False)
                    
                    # Ping admin
                    admin_ping = ""
                    if config.ROLE_ADMIN_ID:
                        admin_ping = f"<@&{config.ROLE_ADMIN_ID}>"
                    
                    await admin_channel.send(content=admin_ping, embed=warning_embed)
                
                # Assign banned role if configured
                if config.PENALTY_AUTO_BAN and config.ROLE_BANNED_DRIVER:
                    banned_role = guild.get_role(int(config.ROLE_BANNED_DRIVER))
                    if banned_role:
                        await penalized_member.add_roles(banned_role)
                        print(f"✅ Assigned banned role to {penalized_member}")
                
                # Send DM to penalized user
                try:
                    await penalized_member.send(
                        f"🚨 **VAROVÁNÍ:** Překročil jsi limit trestných bodů ({config.PENALTY_POINTS_LIMIT})!\n"
                        f"Celkové trestné body: **{total_penalty_points}**\n\n"
                        f"Kontaktuj adminy pro další informace."
                    )
                except:
                    pass  # DM failed
                    
            except Exception as e:
                print(f"❌ Error handling penalty limit: {e}")
        
        await interaction.response.send_message("✅ MIA Dokument byl zveřejněn!", ephemeral=True)


class IncidentReportView(View):
    """Permanent view for Incident Reporting"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Nahlásit Incident (MIA)", style=discord.ButtonStyle.danger, custom_id="mia_report_btn", emoji="🚨")
    async def report_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MIAReportModal())

# --- 🧪 PERSISTENT TRIAL VIEW ---
class PersistentTrialView(View):
    """
    Global handler for Trial buttons. 
    It doesn't store state itself, but listens for interactions with custom_id starting with 'trial_finish:'
    """
    def __init__(self):
        super().__init__(timeout=None)

    # We cannot use a decorator here because the custom_id is dynamic.
    # Instead, we register this View in setup_hook, but we need to handle the interaction slightly differently.
    # Actually, the standard discord.py persistence requires the exact custom_id to be registered.
    # If the custom_id varies (contains user ID), we can't pre-register a single button.
    
    # SOLUTION: Use `bot.add_view()` with a View that has a dynamic custom_id checking logic? 
    # No, `add_view` registers the Item's custom_id.
    
    # ALTERNATIVE: Use `client.interaction_check` or a global event listener `on_interaction`.
    # OR: Since we restart often, maybe we just parse it in `on_interaction`.

# Let's switch to the `on_interaction` approach for this specific dynamic button, 
# OR just recreate the view with the same custom_id logic.
# The `add_view` method only works for static custom_ids.

# Okay, simpler plan for this specific user request:
# We will use `on_interaction` in the bot class to catch ANY button press starting with "trial_finish:"
# This is robust and doesn't require complex View registration for millions of IDs.


# --- 📝 REVIEW MODAL ---
class ReviewModal(Modal):
    def __init__(self, action: str, target_user: discord.Member, role_value: str, role_name: str, original_msg: discord.Message):
        # Set title based on action
        titles = {
            "approve": "Schválit přihlášku",
            "reject": "Zamítnout přihlášku",
            "review": "Poslat do Přezkumu",
            "testing": "Poslat do Testování"
        }
        super().__init__(title=titles.get(action, "Přihláška"))
        self.action = action
        self.target_user = target_user
        self.role_value = role_value
        self.role_name = role_name
        self.original_msg = original_msg
    
    comment = TextInput(
        label="Komentář / Důvod", 
        placeholder="Napiš zprávu pro uživatele...", 
        style=discord.TextStyle.paragraph, 
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        final_role_id = None
        applicant_role_id = None
        
        # Determine IDs
        if self.role_value == "driver":
            final_role_id = config.ROLE_DRIVER
            applicant_role_id = config.ROLE_DRIVER_APPLICANT
        elif self.role_value == "steward":
            final_role_id = config.ROLE_STEWARD
            applicant_role_id = config.ROLE_STEWARD_APPLICANT
        elif self.role_value == "commentator":
            final_role_id = config.ROLE_COMMENTATOR
            applicant_role_id = config.ROLE_COMMENTATOR_APPLICANT

        # Handle Roles
        try:
            guild = interaction.guild
            # Fetch member fresh to avoid stale role data
            member = guild.get_member(self.target_user.id)
            if not member:
                member = await guild.fetch_member(self.target_user.id)
            
            # 1. Determine role to ADD
            role_to_add_id = None
            if self.action == "approve": role_to_add_id = final_role_id
            elif self.action == "review": role_to_add_id = config.ROLE_UNDER_REVIEW
            elif self.action == "testing": role_to_add_id = config.ROLE_UNDER_TESTING
            
            # 2. Determine roles to REMOVE (exhaustive cleanup)
            roles_to_remove_ids = set()
            if config.AUTO_JOIN_ROLE_ID: roles_to_remove_ids.add(int(config.AUTO_JOIN_ROLE_ID))
            
            # On final decision, remove ALL applicant and trial roles
            if self.action in ["approve", "reject"]:
                if config.ROLE_DRIVER_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_DRIVER_APPLICANT))
                if config.ROLE_STEWARD_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_STEWARD_APPLICANT))
                if config.ROLE_COMMENTATOR_APPLICANT: roles_to_remove_ids.add(int(config.ROLE_COMMENTATOR_APPLICANT))
                if config.ROLE_UNDER_REVIEW: roles_to_remove_ids.add(int(config.ROLE_UNDER_REVIEW))
                if config.ROLE_UNDER_TESTING: roles_to_remove_ids.add(int(config.ROLE_UNDER_TESTING))
            elif self.action == "testing":
                # Moving to testing -> remove applicant and review
                if applicant_role_id: roles_to_remove_ids.add(int(applicant_role_id))
                if config.ROLE_UNDER_REVIEW: roles_to_remove_ids.add(int(config.ROLE_UNDER_REVIEW))
            elif self.action == "review":
                # Moving to review -> remove applicant
                if applicant_role_id: roles_to_remove_ids.add(int(applicant_role_id))

            # 3. Calculate new role set
            current_role_ids = [r.id for r in member.roles]
            # Keep roles that aren't in our removal list
            new_roles = [guild.get_role(rid) for rid in current_role_ids if rid not in roles_to_remove_ids]
            
            # Add the target role
            if role_to_add_id:
                target_role = guild.get_role(int(role_to_add_id))
                if target_role and target_role not in new_roles:
                    new_roles.append(target_role)
            
            # Filter None and duplicates
            new_roles = list(set([r for r in new_roles if r is not None]))
            
            # 4. Apply changes atomically
            await member.edit(roles=new_roles)
            print(f"✅ Atomically updated roles for {member}")
                    
        except Exception as e:
            print(f"❌ Error updating roles: {e}")

        # Delete original message and send summary
        try:
            target_user_mention = self.target_user.mention
            role_display = self.role_name
            admin_mention = interaction.user.mention
            
            status_map = {
                "approve": ("SCHVÁLENA", "✅"),
                "reject": ("ZAMÍTNUTA", "❌"),
                "review": ("přesunuta do PŘEZKUMU", "🔍"),
                "testing": ("přesunuta do TESTOVÁNÍ", "🧪")
            }
            status_text, emoji = status_map.get(self.action, ("ZPRACOVÁNA", "⚙️"))
            
            # Delete the admin notification embed
            await self.original_msg.delete()
            
            summary = f"{emoji} Přihláška pro **{target_user_mention}** ({role_display}) byla **{status_text}** uživatelem {admin_mention}."
            if self.comment.value:
                summary += f"\n> **Komentář:** {self.comment.value}"
            
            # Send summary
            if self.action in ["review", "testing"]:
                # Intermediate states: SEND WITH PERSISTENT VIEW (using dynamic custom_id)
                clean_role_name = self.role_name.replace(" ", "_") # encoding safety
                custom_id = f"trial_finish:{self.target_user.id}:{self.role_value}:{clean_role_name}"
                
                # Create dynamic view for persistence
                dynamic_view = View(timeout=None)
                dynamic_view.add_item(discord.ui.Button(
                    label="✅ Splněno (Trial)", 
                    style=discord.ButtonStyle.green, 
                    custom_id=custom_id,
                    emoji="✅"
                ))
                
                await interaction.channel.send(summary, view=dynamic_view)
            else:
                # Final states (Approve/Reject): AUTO-DELETE AFTER 24h
                summary_msg = await interaction.channel.send(summary)
                await summary_msg.delete(delay=86400)
            
            # Since we send a separate message, we must acknowledge the modal interaction
            if not interaction.response.is_done():
                await interaction.response.send_message("Stav aktualizován!", ephemeral=True)
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

        # Send DM to user
        try:
            dm_map = {
                "approve": f"🎉 Tvoje přihláška na roli **{self.role_name}** byla **SCHVÁLENA**! Vítej v týmu.",
                "reject": f"Tvoje přihláška na roli **{self.role_name}** byla **ZAMÍTNUTA**.",
                "review": f"Tvoje přihláška na roli **{self.role_name}** je nyní v **PŘEZKUMU DOVEDNOSTÍ**. Brzy se ozveme!",
                "testing": f"Tvoje přihláška na roli **{self.role_name}** se přesunula do **TESTOVACÍ FÁZE**. Připrav se!"
            }
            msg = dm_map.get(self.action, "Stav tvé přihlášky byl aktualizován.")
            if self.comment.value:
                msg += f"\n\n**Komentář admina:** {self.comment.value}"
            
            await self.target_user.send(msg)
        except:
            pass # DM failed

# --- 📝 REVIEW BUTTONS ---
class ApplicationReviewView(View):
    def __init__(self, target_user: discord.Member, role_value: str, role_name: str):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.role_value = role_value
        self.role_name = role_name

    @discord.ui.button(label="Schválit", style=discord.ButtonStyle.green, custom_id="app_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="approve", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Do přezkumu", style=discord.ButtonStyle.blurple, custom_id="app_review")
    async def review_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="review", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Do testování", style=discord.ButtonStyle.gray, custom_id="app_testing")
    async def testing_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="testing", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.red, custom_id="app_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ReviewModal(action="reject", target_user=self.target_user, role_value=self.role_value, role_name=self.role_name, original_msg=interaction.message)
        )


# --- GLOBAL SUBMISSION HANDLER ---
async def handle_submission(interaction: discord.Interaction, role_value: str, role_name: str, answers: dict):
    """Generic handler for storing data and sending notifications"""
    # Register in database
    result = database.register_player(
        user_id=interaction.user.id,
        username=str(interaction.user),
        role=role_value,
        answers=answers
    )
    
    # Success Embed for user
    user_embed = discord.Embed(
        title="✅ Přihláška odeslána!",
        description=f"**Uživatel:** {interaction.user.mention}\n**Role:** {role_name}\n**EA ID:** `{answers.get('ea_id')}`",
        color=config.EMBED_COLOR_SUCCESS
    )
    user_embed.set_footer(text="Tvoje přihláška byla uložena! 🏁")
    await interaction.response.send_message(embed=user_embed, ephemeral=True)

    # Assign Applicant Role immediately
    try:
        # Remove Member role if it exists
        if config.AUTO_JOIN_ROLE_ID:
            member_role = interaction.guild.get_role(int(config.AUTO_JOIN_ROLE_ID))
            if member_role and member_role in interaction.user.roles:
                await interaction.user.remove_roles(member_role)
                print(f"➖ Removed Member role from {interaction.user}")

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
            # First try cache
            admin_channel = interaction.client.get_channel(int(config.ADMIN_CHANNEL_ID))
            
            # If not in cache, fetch it
            if not admin_channel:
                admin_channel = await interaction.client.fetch_channel(int(config.ADMIN_CHANNEL_ID))
                
            if admin_channel:
                admin_embed = discord.Embed(
                    title=f"📢 New {role_name} Application!",
                    description=f"**User:** {interaction.user.mention} ({interaction.user})\n**EA ID:** `{answers.get('ea_id')}`",
                    color=config.EMBED_COLOR_PRIMARY
                )
                
                # Dynamically add all answer fields
                for key, val in answers.items():
                    if key != 'ea_id' and val:
                        field_name = key.replace('_', ' ').title()
                        admin_embed.add_field(name=f"🔹 {field_name}", value=val, inline=False)
                
                admin_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                admin_embed.timestamp = discord.utils.utcnow()
                
                # Create View with buttons
                view = ApplicationReviewView(target_user=interaction.user, role_value=role_value, role_name=role_name)
                
                # Ping content
                content = None
                if config.ROLE_ADMIN_ID:
                    content = f"<@&{config.ROLE_ADMIN_ID}>"

                await admin_channel.send(content=content, embed=admin_embed, view=view)
            else:
                print(f"⚠️ Warning: Could not find Admin Channel with ID {config.ADMIN_CHANNEL_ID}")
        except Exception as e:
            print(f"❌ Error sending admin notification: {e}")


class RoleSelect(Select):
    """Dropdown menu for selecting league role"""
    def __init__(self):
        options = [
            discord.SelectOption(label=role["name"], value=role["value"], description=role["description"])
            for role in config.LEAGUE_ROLES
        ]
        super().__init__(placeholder="🎯 Vyber si roli...", min_values=1, max_values=1, options=options, custom_id="league_role_select")
    
    async def callback(self, interaction: discord.Interaction):
        """Handle role selection - Opens the correct Modal"""
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


class LeagueBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.synced = False
    
    async def setup_hook(self):
        self.add_view(LeagueRegistrationView())
        self.add_view(AttendanceBoard())
        self.add_view(IncidentReportView())
        self.add_view(PersistentTrialView()) 
    
    async def on_ready(self):
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🤖 Bot is online as: {self.user}")
        print(f"📊 Connected to {len(self.guilds)} guild(s)")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        print("🔄 Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"✅ Successfully synced {len(synced)} slash commands!")
            for cmd in synced:
                print(f"  • /{cmd.name}")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
        
        # MODULE 10: Start automated notification tasks
        if not race_reminder_task.is_running():
            race_reminder_task.start()
            print("✅ Started automated notification tasks")

    async def on_member_join(self, member):
        """Auto-assign role on join"""
        print(f"👤 New member joined: {member}")
        
        role = None
        # Try finding by ID first
        if config.AUTO_JOIN_ROLE_ID:
            role = member.guild.get_role(int(config.AUTO_JOIN_ROLE_ID))
        
        # If not found by ID (or ID not set), try by name "Member"
        if not role:
            role = discord.utils.get(member.guild.roles, name="Member")
            
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ Assigned role {role.name} to {member}")
            except Exception as e:
                print(f"❌ Failed to assign role: {e}")
        else:
            print("⚠️ Auto-role 'Member' (or ID) not found in guild.")

    async def on_interaction(self, interaction: discord.Interaction):
        """Global interaction listener for dynamic persistent buttons"""
        # Check if it's a component interaction (Button/Select)
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            
            # Handle Trial Button: "trial_finish:USER_ID:ROLE:ROLE_NAME"
            if custom_id.startswith("trial_finish:"):
                try:
                    # Parse data
                    _, user_id_str, role_value, role_name_clean = custom_id.split(":")
                    user_id = int(user_id_str)
                    role_name = role_name_clean.replace("_", " ") # Decode space
                    
                    # Fetch User Object
                    guild = interaction.guild
                    target_user = guild.get_member(user_id)
                    if not target_user:
                        target_user = await guild.fetch_member(user_id)
                    
                    # Execute Logic (Same as old finish_btn)
                    player = database.get_player(user_id)
                    if not player:
                        await interaction.response.send_message("❌ Chyba: Data přihlášky nenalezena.", ephemeral=True)
                        return

                    answers = player.get("answers", {})
                    
                    # Admin Notification
                    admin_embed = discord.Embed(
                        title=f"📢 Rozhodnutí potřeba: {role_name}!",
                        description=f"**Uživatel:** {target_user.mention} ({target_user})\n**EA ID:** `{answers.get('ea_id')}`",
                        color=config.EMBED_COLOR_PRIMARY
                    )
                    
                    for key, val in answers.items():
                        if key != 'ea_id' and val:
                            field_name = key.replace('_', ' ').title()
                            admin_embed.add_field(name=f"🔹 {field_name}", value=val, inline=False)
                    
                    admin_embed.set_thumbnail(url=target_user.display_avatar.url)
                    admin_embed.timestamp = discord.utils.utcnow()
                    admin_embed.set_footer(text="Pokračování rozhodnutí po fázi Trial/Přezkumu")

                    view = ApplicationReviewView(target_user=target_user, role_value=role_value, role_name=role_name)
                    
                    # Schedule deletion of the old status message after 24h, then send the new review panel
                    await interaction.message.delete(delay=86400)
                    await interaction.channel.send(embed=admin_embed, view=view)
                    
                    # Acknowledge the interaction to prevent "failed"
                    if not interaction.response.is_done():
                        await interaction.response.defer() # or send_message ephemeral

                except Exception as e:
                    print(f"❌ Error in dynamic trial handler: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Nastala chyba při zpracování tlačítka.", ephemeral=True)

bot = LeagueBot()

@bot.tree.command(name="rc-nastaveni-dochazky", description="Vytvořit nový příspěvek pro docházku (Admin pouze)")
@app_commands.default_permissions(administrator=True)
async def setup_attendance(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        database.reset_attendance() # Start fresh for new race
        embed = discord.Embed(
            title="🏁 Nadcházející závod: Registrace",
            description="Celkem přihlášeno: **0**",
            color=0x2b2d31
        )
        embed.add_field(name="✅ Jedu (0)", value="_Nikdo_", inline=False)
        embed.add_field(name="🤔 Možná (0)", value="_Nikdo_", inline=False)
        embed.add_field(name="❌ Nejedu (0)", value="_Nikdo_", inline=False)
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="Klikni na tlačítka níže pro registraci")
        
        await interaction.channel.send(embed=embed, view=AttendanceBoard())
        await interaction.followup.send("✅ Docházka byla zveřejněna a resetována!")
    except Exception as e:
        await interaction.followup.send(f"❌ Chyba při zveřejnění docházky: {e}")

@bot.tree.command(name="rc-nastaveni-incidentu", description="Vytvořit panel pro hlášení incidentů (MIA)")
@app_commands.default_permissions(administrator=True)
async def setup_incidents(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🚨 MIA Hlášení Incidentů",
        description="Klikni na tlačítko níže pro vytvoření hlášení pro FIA/MIA.\n\n**Co nahlásit:**\n• Kolize a nebezpečná jízda\n• Porušení pravidel (track limits, modré vlajky)\n• Nesportovní chování",
        color=config.EMBED_COLOR_ERROR
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="MIA - Race Control System")
    
    await interaction.channel.send(embed=embed, view=IncidentReportView())
    await interaction.response.send_message("✅ Panel pro hlášení incidentů vytvořen!", ephemeral=True)



@bot.tree.command(name="rc-nahlasit", description="Nahlásit incident (MIA) příkazem")
async def report_incident(interaction: discord.Interaction):
    # This just opens a modal, it shouldn't timeout, but we leave it as is 
    # since Modal doesn't need defer logic (it's a direct response)
    # But wait, did I provide correct Modal logic? 
    await interaction.response.send_modal(MIAReportModal())

@bot.tree.command(name="rc-registrace", description="Zobrazit registrační panel")
async def send_registration(interaction: discord.Interaction):

# ... (inside the file, I will apply multiple chunks or just one if they are close, but they are scattered)

    """Send original registration embed with dropdown"""
    embed = discord.Embed(
        title="🏆 Registrační systém ligy",
        description="Vyber si svou roli a vyplň registrační formulář.\n\n📌 **Dostupné role:**\n",
        color=config.EMBED_COLOR_PRIMARY
    )
    for role in config.LEAGUE_ROLES:
        embed.description += f"• {role['name']} - {role['description']}\n"
    embed.set_footer(text="⬇️ Vyber roli níže pro otevření formuláře")
    await interaction.channel.send(embed=embed, view=LeagueRegistrationView())
    await interaction.response.send_message("✅ Registrační panel odeslán!", ephemeral=True)


@bot.tree.command(name="rc-info", description="Odeslat informační embedy ligy")
async def send_info(interaction: discord.Interaction):
    """Send all information embeds to the channel"""
    
    # MODULE 7 & 9: Dynamic race countdown + weather
    race_time_display = f"{config.RACE_DAY_DEFAULT} {config.RACE_TIME_DEFAULT}"
    if config.NEXT_RACE_TIMESTAMP:
        race_time_display = f"<t:{config.NEXT_RACE_TIMESTAMP}:F>\n**Odpočet:** <t:{config.NEXT_RACE_TIMESTAMP}:R>"
    
    # MODULE 9: Random weather (or use stored value from attendance setup)
    import random
    weather_options = ["Jasno (Clear)", "Zataženo (Overcast)", "Lehký déšť (Light Rain)", "Déšť (Rain)", "Dynamické (Dynamic)"]
    current_weather = random.choice(weather_options)
    
    # --- 🏎️ RACE INFO EMBED ---
    race_embed = discord.Embed(
        title=f"🏎️ {config.NEXT_RACE_NAME if config.NEXT_RACE_NAME else 'Informace o Závodech'}",
        description=(
            f"**Kdy:** {race_time_display}\n"
            "**Lobby:** Otevírá 10 minut před startem. *Kdo není včas, nezávodí!*\n\n"
            "🛠️ **Nastavení Lobby:**\n"
            "• **Limity tratě:** Přísné (Strict)\n"
            "• **Safety Car:** Standard\n"
            "• **Asistenti:** Vše povoleno\n"
            "• **Parc Fermé:** Vypnuto\n"
            "• **Poškození:** Standard\n"
            "• **Zahřívací kolo:** Zapnuto\n"
            f"• **Počasí:** {current_weather}"
        ),
        color=0x3498DB # Blue
    )
    
    # --- ⚖️ FIA & RULES EMBED ---
    fia_embed = discord.Embed(
        title="⚖️ FIA & Pravidla",
        description=(
            f"Pokud máš incident k nahlášení, vytvoř ticket v <#{config.INCIDENT_REPORT_CHANNEL_ID}>\n\n"
            "📝 **Postup nahlášení:**\n"
            "1. Vytvoř ticket v kanálu pro stewardy.\n"
            "2. Pošli klip incidentu.\n"
            "3. Incidenty budou přezkoumány FIA.\n\n"
            "🔄 **Odvolání:**\n"
            "Pokud věříš, že penalizace byla nespravedlivá, vytvoř nový ticket s odůvodněním."
        ),
        color=0xE74C3C # Red
    )
    
    # --- ❗ SIGNUPS EMBED ---
    signup_info_embed = discord.Embed(
        title="❗ Jak se zapsat",
        description=(
            "**Zápis Jezdce:**\n"
            f"Vytvoř **Driver Signup** ticket v <#{config.REGISTRATION_CHANNEL_ID}> a odpověz:\n"
            "• Jméno\n• Číslo\n• Tým\n\n"
            "**Zápis Admina:**\n"
            "Vytvoř **Admin Signup** ticket a odpověz:\n"
            "• Jaké máš zkušenosti?\n"
            "• S čím chceš pomoct?\n"
            "• Co přineseš do ligy?\n\n"
            f"🔍 *Zkontroluj channel (Čísla) a (Sestavy) pro volná místa!*"
        ),
        color=0x2ECC71 # Green
    )
    
    # --- 📊 POINTS SYSTEM EMBED ---
    points_embed = discord.Embed(
        title="📊 Bodovací systém",
        description=(
            "1️⃣ **1.:** 25 b\n"
            "2️⃣ **2.:** 18 b\n"
            "3️⃣ **3.:** 15 b\n"
            "4️⃣ **4.:** 12 b\n"
            "5️⃣ **5.:** 10 b\n"
            "6️⃣ **6.:** 8 b\n"
            "7️⃣ **7.:** 6 b\n"
            "8️⃣ **8.:** 4 b\n"
            "9️⃣ **9.:** 2 b\n"
            "🔟 **10.:** 1 b"
        ),
        color=0xF1C40F # Yellow
    )

    # Set thumbnails/footers for all
    if interaction.guild and interaction.guild.icon:
        race_embed.set_thumbnail(url=interaction.guild.icon.url)
    
    footer_text = "Race Control | Formula 1 League"
    race_embed.set_footer(text=footer_text)
    fia_embed.set_footer(text=footer_text)
    signup_info_embed.set_footer(text=footer_text)
    points_embed.set_footer(text=footer_text)
    
    # Send all embeds
    await interaction.channel.send(embeds=[race_embed, fia_embed, signup_info_embed, points_embed])
    await interaction.response.send_message("✅ Informační panely byly odeslány!", ephemeral=True)



@bot.tree.command(name="rc-hraci", description="Zobrazit seznam registrovaných hráčů")
async def list_players(interaction: discord.Interaction):
    try:
        players = database.get_all_players()
        if not players:
            await interaction.response.send_message("📭 Zatím žádné přihlášky.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Seznam přihlášek", color=config.EMBED_COLOR_PRIMARY)
        for role in config.LEAGUE_ROLES:
            role_players = database.get_players_by_role(role["value"])
            if role_players:
                player_list = "\n".join([f"• {p['username']}" for p in role_players])
                embed.add_field(name=f"{role['name']} ({len(role_players)})", value=player_list[:1024], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Chyba při výpisu: {e}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Chyba při výpisu: {e}")

@bot.tree.command(name="rc-profil", description="Zobrazit detaily tvé přihlášky")
async def my_profile(interaction: discord.Interaction):
    try:
        player = database.get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message("❌ Žádná přihláška nenalezena.", ephemeral=True)
            return
        ans = player.get("answers", {})
        embed = discord.Embed(title="👤 Tvůj profil přihlášky", color=config.EMBED_COLOR_PRIMARY)
        embed.add_field(name="Uživatel", value=interaction.user.mention, inline=True)
        embed.add_field(name="Role", value=player["role"].title(), inline=True)
        for k, v in ans.items():
            embed.add_field(name=k.replace('_', ' ').title(), value=v, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Chyba při zobrazení profilu: {e}", ephemeral=True)

@bot.tree.command(name="rc-unregister", description="Stáhnout svou přihlášku")
async def unregister(interaction: discord.Interaction):
    try:
        if database.unregister_player(interaction.user.id):
            await interaction.response.send_message("👋 Přihláška stažena.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Žádná přihláška nenalezena.", ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Chyba při odhlašování: {e}", ephemeral=True)


@bot.tree.command(name="rc-hledat-hrace", description="Vyhledat hráče v databázi")
@app_commands.describe(uzivatel="Hráč k vyhledání")
async def search_player(interaction: discord.Interaction, uzivatel: discord.Member):
    try:
        player = database.get_player(uzivatel.id)
        if not player:
            await interaction.response.send_message(f"❌ Hráč {uzivatel.mention} nemá žádnou přihlášku.", ephemeral=True)
            return
        
        ans = player.get("answers", {})
        embed = discord.Embed(
            title=f"👤 Profil: {uzivatel.display_name}",
            color=config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=uzivatel.display_avatar.url)
        embed.add_field(name="Uživatel", value=uzivatel.mention, inline=True)
        embed.add_field(name="Role", value=player["role"].title(), inline=True)
        embed.add_field(name="EA ID", value=f"`{ans.get('ea_id', 'N/A')}`", inline=True)
        
        # MODULE 1 & 5: Add penalty and championship info
        embed.add_field(name="Trestné body", value=f"`{player.get('penalties', {}).get('total_points', 0)}`", inline=True)
        embed.add_field(name="Body v šampionátu", value=f"`{player.get('total_points', 0)}`", inline=True)
        
        for k, v in ans.items():
            if k != "ea_id" and v:
                embed.add_field(name=k.replace('_', ' ').title(), value=v, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# MODULE 1: PENALTY SYSTEM COMMANDS
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="rc-penalty-info", description="Zobrazit historii trestných bodů jezdce")
@app_commands.describe(jezdec="Jezdec k zobrazení")
async def penalty_info(interaction: discord.Interaction, jezdec: discord.Member):
    try:
        total = database.get_penalty_points(jezdec.id)
        history = database.get_penalty_history(jezdec.id)
        
        embed = discord.Embed(
            title=f"⚠️ Trestné body: {jezdec.display_name}",
            description=f"**Celkem:** {total}/{config.PENALTY_POINTS_LIMIT} bodů",
            color=config.EMBED_COLOR_ERROR if total >= config.PENALTY_POINTS_LIMIT else config.EMBED_COLOR_PRIMARY
        )
        embed.set_thumbnail(url=jezdec.display_avatar.url)
        
        if history:
            for i, entry in enumerate(history[-5:], 1):  # Last 5 penalties
                date = entry.get("date", "N/A")[:10]  # YYYY-MM-DD
                embed.add_field(
                    name=f"{i}. {entry.get('points', 0)} bodů ({date})",
                    value=f"**Důvod:** {entry.get('reason', 'N/A')}",
                    inline=False
                )
        else:
            embed.add_field(name="Historie", value="_Žádné tresty_", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


@bot.tree.command(name="rc-penalty-reset", description="Resetovat trestné body jezdce (Admin)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(jezdec="Jezdec k resetování")
async def penalty_reset(interaction: discord.Interaction, jezdec: discord.Member):
    if database.reset_penalty_points(jezdec.id):
        await interaction.response.send_message(f"✅ Trestné body pro {jezdec.mention} byly resetovány!", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Hráč {jezdec.mention} nenalezen v databázi.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# MODULE 2: DYNAMIC LINEUP
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="rc-lineup", description="Generovat startovní listinu pro F1 lobby")
@app_commands.default_permissions(administrator=True)
async def generate_lineup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        lineup = database.get_race_lineup()
        
        if not lineup:
            await interaction.followup.send("📭 Žádní jezdci nejsou přihlášeni na závod.")
            return
        
        # Create embed
        embed = discord.Embed(
            title="🏁 Startovní Listina",
            description=f"Celkem **{len(lineup)}** jezdců",
            color=config.EMBED_COLOR_SUCCESS
        )
        
        # Add driver list
        driver_list = "\n".join([f"{i+1}. {d['mention']} - `{d['ea_id']}`" for i, d in enumerate(lineup)])
        embed.add_field(name="Jezdci", value=driver_list[:1024], inline=False)
        
        # Create text file with EA IDs
        ea_ids = "\n".join([d['ea_id'] for d in lineup])
        file = discord.File(fp=io.BytesIO(ea_ids.encode('utf-8')), filename="lineup.txt")
        
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Chyba: {e}")


# ═══════════════════════════════════════════════════════════════
# MODULE 4: DATA EXPORT
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="rc-export-databaze", description="Exportovat databázi hráčů do CSV")
@app_commands.default_permissions(administrator=True)
async def export_db(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        csv_string = database.export_to_csv_string()
        if not csv_string:
            await interaction.followup.send("📭 Databáze je prázdná.")
            return
        
        file = discord.File(fp=io.BytesIO(csv_string.encode('utf-8-sig')), filename="players_export.csv")
        await interaction.followup.send("✅ Tady je export databáze (včetně penalty points):", file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Chyba při exportu: {e}")


# ═══════════════════════════════════════════════════════════════
# MODULE 5: RACE RESULTS & STANDINGS
# ═══════════════════════════════════════════════════════════════

class RaceResultsModal(Modal):
    """Modal for submitting race results"""
    def __init__(self):
        super().__init__(title="Výsledky závodu")
    
    race_name = TextInput(label="Název závodu", placeholder="Bahrain GP", required=True)
    results = TextInput(
        label="Pořadí (mentions, řádek po řádku)",
        placeholder="@User1\n@User2\n@User3",
        style=discord.TextStyle.paragraph,
        required=True
    )
    fastest_lap_driver = TextInput(label="Nejrychlejší kolo (mention)", placeholder="@Username", required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parse results
            lines = self.results.value.strip().split('\n')
            participant_ids = []
            results_summary = []
            
            for position, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Extract user ID from mention
                if line.startswith("<@") and line.endswith(">"):
                    user_id_str = line.replace("<@!", "").replace("<@", "").replace(">", "")
                    try:
                        user_id = int(user_id_str)
                        participant_ids.append(user_id)
                        
                        # Check if this driver gets the fastest lap bonus
                        is_fastest = False
                        if self.fastest_lap_driver.value:
                            fl_mention = self.fastest_lap_driver.value.strip()
                            if fl_mention == line:
                                is_fastest = True
                        
                        # Add race result
                        result = database.add_race_result(
                            user_id=user_id,
                            race_name=self.race_name.value,
                            position=position,
                            fastest_lap=is_fastest
                        )
                        
                        if result["success"]:
                            results_summary.append(
                                f"{position}. <@{user_id}> - {result['points_awarded']} bodů"
                                + (" 🏁" if is_fastest else "")
                            )
                    except ValueError:
                        continue
            
            # MODULE 6: Track attendance
            database.track_race_attendance(self.race_name.value, participant_ids)
            
            # Send confirmation
            embed = discord.Embed(
                title=f"🏁 {self.race_name.value} - Výsledky uloženy!",
                description=f"Zpracováno **{len(results_summary)}** výsledků",
                color=config.EMBED_COLOR_SUCCESS
            )
            embed.add_field(name="Body přiděleny:", value="\n".join(results_summary[:10]), inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Update standings embed
            await update_standings_embed(interaction.client, interaction.guild)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Chyba: {e}")


async def update_standings_embed(bot, guild):
    """Update or create the championship standings embed"""
    try:
        standings = database.get_championship_standings()
        if not standings:
            return
        
        embed = discord.Embed(
            title="🏆 Championship Standings",
            description=f"Top {min(len(standings), 20)} jezdců",
            color=0xF1C40F,  # Gold
            timestamp=discord.utils.utcnow()
        )
        
        for i, entry in enumerate(standings[:20], 1):
            prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(
                name=f"{prefix} {entry['username']}",
                value=f"{entry['total_points']} bodů ({entry['races_completed']} závodů)",
                inline=False
            )
        
        embed.set_footer(text="Race Control | Championship Standings")
        
        # Try to edit existing message or create new one
        channel = bot.get_channel(int(config.STANDINGS_CHANNEL_ID))
        if not channel:
            channel = await bot.fetch_channel(int(config.STANDINGS_CHANNEL_ID))
        
        # For simplicity, just send a new message (you could store message ID in database)
        await channel.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error updating standings: {e}")


@bot.tree.command(name="rc-add-results", description="Zadat výsledky závodu (Admin)")
@app_commands.default_permissions(administrator=True)
async def add_race_results(interaction: discord.Interaction):
    await interaction.response.send_modal(RaceResultsModal())


@bot.tree.command(name="rc-standings", description="Zobrazit aktuální standings šampionátu")
async def show_standings(interaction: discord.Interaction):
    try:
        standings = database.get_championship_standings()
        if not standings:
            await interaction.response.send_message("📭 Zatím žádné výsledky.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Championship Standings",
            color=0xF1C40F,
            timestamp=discord.utils.utcnow()
        )
        
        for i, entry in enumerate(standings[:10], 1):
            prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(
                name=f"{prefix} {entry['username']}",
                value=f"{entry['total_points']} bodů",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# MODULE 6: ACTIVITY TRACKING
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="rc-check-activity", description="Zkontrolovat neaktivní členy (Admin)")
@app_commands.default_permissions(administrator=True)
async def check_activity(interaction: discord.Interaction):
    try:
        inactive = database.get_inactive_users()
        
        if not inactive:
            await interaction.response.send_message("✅ Všichni členové jsou aktivní!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚠️ Neaktivní členové",
            description=f"Jezdci s {config.INACTIVITY_THRESHOLD}+ vynechanými závody",
            color=config.EMBED_COLOR_ERROR
        )
        
        for user_data in inactive[:15]:
            embed.add_field(
                name=f"<@{user_data['user_id']}>",
                value=f"Vynecháno: **{user_data['missed_races']}** závodů\nPoslední aktivita: {user_data['last_activity'][:10]}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# MODULE 7: DYNAMIC RACE COUNTDOWN
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="rc-set-next-race", description="Nastavit datum a čas příštího závodu (Admin)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    nazev="Název závodu (např. Bahrain GP)",
    datum="Datum ve formátu DD.MM.YYYY",
    cas="Čas ve formátu HH:MM"
)
async def set_next_race(interaction: discord.Interaction, nazev: str, datum: str, cas: str):
    try:
        # Parse date and time
        from datetime import datetime as dt
        import time
        
        date_str = f"{datum} {cas}"
        race_datetime = dt.strptime(date_str, "%d.%m.%Y %H:%M")
        
        # Convert to Unix timestamp  
        timestamp = int(time.mktime(race_datetime.timetuple()))
        
        # NOTE: In production, you'd save this to database or config file
        # For now, we'll just show a confirmation
        
        embed = discord.Embed(
            title="✅ Příští závod nastaven!",
            description=f"**{nazev}**",
            color=config.EMBED_COLOR_SUCCESS
        )
        embed.add_field(name="Kdy", value=f"<t:{timestamp}:F>", inline=False)
        embed.add_field(name="Odpočet", value=f"<t:{timestamp}:R>", inline=False)
        embed.add_field(name="Timestamp (pro config)", value=f"`{timestamp}`", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # You would update config.NEXT_RACE_NAME and config.NEXT_RACE_TIMESTAMP here
        
    except ValueError:
        await interaction.response.send_message("❌ Neplatný formát data/času! Použij DD.MM.YYYY a HH:MM", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# MODULE 10: NOTIFICATION HUB (Automated Notifications)
# ═══════════════════════════════════════════════════════════════

@tasks.loop(hours=1)  # Check every hour
async def race_reminder_task():
    """Send reminders to 'Maybe' users 24 hours before race"""
    try:
        if not config.NEXT_RACE_TIMESTAMP:
            return
        
        import time
        current_time = int(time.time())
        time_until_race = config.NEXT_RACE_TIMESTAMP - current_time
        
        # Check if we're between 24-23 hours before race
        if 82800 <= time_until_race <= 86400:  # 23-24 hours in seconds
            attendance = database.get_attendance()
            
            for user_id_str, entry in attendance.items():
                if entry.get('status') == 'Maybe':
                    try:
                        user = await bot.fetch_user(int(user_id_str))
                        await user.send(
                            f"🏁 **Připomínka závodu!**\n\n"
                            f"Závod začíná <t:{config.NEXT_RACE_TIMESTAMP}:R>!\n"
                            f"Prosím rozhodň se, zda se zúčastníš nebo ne. 🏎️"
                        )
                        print(f"✅ Sent race reminder to {user}")
                    except:
                        pass  # DM failed or user not found
        
    except Exception as e:
        print(f"❌ Error in race_reminder_task: {e}")


@race_reminder_task.before_loop
async def before_race_reminder():
    """Wait until bot is ready before starting the task"""
    await bot.wait_until_ready()


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
