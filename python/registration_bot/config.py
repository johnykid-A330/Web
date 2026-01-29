"""
Configuration file for the Standalone Registration Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot token (This will be the NEW bot token)
DISCORD_TOKEN = "SEM_VLOZ_TVUJ_NOVY_TOKEN"

# ---------------------------------------------------------
# ⚙️ NASTAVENÍ PRO NOVÝ SERVER (To musíte vyplnit vy!)
# Zapněte si na Discordu "Developer Mode" (User Settings -> Advanced)
# Pak klikněte pravým na kanál/roli a dejte "Copy ID".
# ---------------------------------------------------------

# ID Kanálu, kam se pošle ta velká zpráva s výběrem rolí (Jezdec/Komentátor...)
REGISTRATION_CHANNEL_ID = 0  # <--- SEM VLOŽ ID KANÁLU

# ID Kanálu, kam budou chodit adminům upozornění na nové přihlášky
ADMIN_CHANNEL_ID = 0  # <--- SEM VLOŽ ID KANÁLU

# ID Role, kterou dostane každý hned po odeslání přihlášky (Volitelné)
# Např. role "Čeká na schválení"
AUTO_JOIN_ROLE_ID = None 

# ---------------------------------------------------------
# 🎭 ROLE ID (Přiřazují se po schválení)
# Vyplňte ID rolí na vašem novém serveru
# ---------------------------------------------------------

ROLE_DRIVER = 0       # Role pro schváleného Jezdce
ROLE_STEWARD = 0      # Role pro Stewarda
ROLE_COMMENTATOR = 0  # Role pro Komentátora

# 🚦 APPLICANT ROLES (Role "Žadatel o...") - Volitelné, pokud nepoužíváte, nechte 0 nebo None
ROLE_DRIVER_APPLICANT = 0
ROLE_STEWARD_APPLICANT = 0
ROLE_COMMENTATOR_APPLICANT = 0

# Role Admina (kdo má být označen, když přijde nová přihláška)
ROLE_ADMIN_ID = 0

# Trial / Intermediate Roles (Mezistupně)
ROLE_UNDER_REVIEW = 0   # Role "V přezkumu"
ROLE_UNDER_TESTING = 0  # Role "V testování"

# Embed colors
EMBED_COLOR_PRIMARY = 0x5865F2
EMBED_COLOR_SUCCESS = 0x57F287
EMBED_COLOR_ERROR = 0xED4245

# League roles configuration
LEAGUE_ROLES = [
    {"name": "⚖️ Steward", "value": "steward", "description": "Incident review and rules enforcement"},
    {"name": "🎙️ Commentator", "value": "commentator", "description": "Live commentary and race broadcasting"},
    {"name": "🏎️ Driver", "value": "driver", "description": "Racing on track in our leagues"},
]

# Team Definitions
TEAMS = {
    "ferrari": {"name": "🔴 Scuderia Ferrari"},
    "mercedes": {"name": "⚪ Mercedes-AMG Petronas"},
    "redbull": {"name": "🔵 Oracle Red Bull Racing"},
    "mclaren": {"name": "🟠 McLaren F1 Team"},
    "alpine": {"name": "💙 Alpine F1 Team"},
    "aston": {"name": "🟢 Aston Martin F1"},
    "williams": {"name": "🔷 Williams Racing"},
    "haas": {"name": "⚪ MoneyGram Haas F1"},
    "rb": {"name": "🟦 Visa Cash App RB"},
    "sauber": {"name": "⬛ Stake F1 Sauber"},
}
