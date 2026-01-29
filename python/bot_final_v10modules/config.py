"""
Configuration file for the Discord League Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from Discord Developer Portal
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Channel where registration embed will be posted (přihlášky na role)
REGISTRATION_CHANNEL_ID = 1460350268519481404

# Channel where admin notifications will be sent
ADMIN_CHANNEL_ID = 1466531002712199432

# Channel IDs
ATTENDANCE_CHANNEL_ID = 1463998898384142340  # Sestavy (Lineups)
INCIDENT_REPORT_CHANNEL_ID = 1464333840536436820  # Hlášení incidentů (Admin view)
MIA_DOCS_CHANNEL_ID = 1460722063210709082  # Verdikty (Public decision post)
STANDINGS_CHANNEL_ID = 1460722390588723271  # Championship Standings (Modul 5)
RESULTS_CHANNEL_ID = 1463998898384142340 # Sestavy

# Roles to ping for MIA Verdicts (Posted in public channel)
MIA_PING_ROLES = [1460693651872026821, 1460693696143167663, 1460675411238457491]

# Roles to ping for NEW Incident Reports (Marshals - Admin View)
MIA_REPORT_PING_ROLES = [1460693651872026821, 1460693696143167663, 1460675411238457491]

# Role ID to automatically assign to new members
AUTO_JOIN_ROLE_ID = os.getenv("AUTO_JOIN_ROLE_ID")

# Advanced League Role IDs
ROLE_DRIVER = os.getenv("ROLE_DRIVER")
ROLE_STEWARD = os.getenv("ROLE_STEWARD")
ROLE_COMMENTATOR = os.getenv("ROLE_COMMENTATOR")

ROLE_DRIVER_APPLICANT = os.getenv("ROLE_DRIVER_APPLICANT")
ROLE_STEWARD_APPLICANT = os.getenv("ROLE_STEWARD_APPLICANT")
ROLE_COMMENTATOR_APPLICANT = os.getenv("ROLE_COMMENTATOR_APPLICANT")

# Admin role to ping
ROLE_ADMIN_ID = 1455952224315506942

# Trial / Intermediate Roles
ROLE_UNDER_REVIEW = os.getenv("ROLE_UNDER_REVIEW")
ROLE_UNDER_TESTING = os.getenv("ROLE_UNDER_TESTING")

# ═══════════════════════════════════════════════════════════════
# MODULE 1: PENALTY SYSTEM
# ═══════════════════════════════════════════════════════════════
PENALTY_POINTS_LIMIT = 18  # Maximální povolené trestné body
PENALTY_AUTO_BAN = True  # Automaticky přidělit banned role při překročení
ROLE_BANNED_DRIVER = "1465093640677363775"  # Role pro zabanované jezdce

# ═══════════════════════════════════════════════════════════════
# MODULE 3: RESERVE PRIORITY
# ═══════════════════════════════════════════════════════════════
ROLE_RESERVE = "1465093808612970527"  # Role ID pro náhradníky
MAX_MAIN_GRID_SIZE = 20  # Maximální kapacita hlavního gridu

# ═══════════════════════════════════════════════════════════════
# MODULE 5: RACE RESULTS & STANDINGS
# ═══════════════════════════════════════════════════════════════
POINTS_SYSTEM = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]  # Body pro pozice 1-10
FASTEST_LAP_BONUS = 1  # Extra bod za nejrychlejší kolo
FASTEST_LAP_MIN_POSITION = 10  # Fastest lap bonus pouze pokud dojede v top 10
STANDINGS_MESSAGE_ID = None  # ID standings embedu (bot automaticky uloží)

# ═══════════════════════════════════════════════════════════════
# MODULE 6: ACTIVITY TRACKING
# ═══════════════════════════════════════════════════════════════
INACTIVITY_THRESHOLD = 3  # Počet vynechaných závodů = neaktivní
AUTO_REMOVE_INACTIVE_ROLE = False  # Automaticky odebrat driver role?

# ═══════════════════════════════════════════════════════════════
# MODULE 7: DYNAMIC RACE COUNTDOWN
# ═══════════════════════════════════════════════════════════════
NEXT_RACE_NAME = "Bahrain GP"  # Název příštího závodu
NEXT_RACE_TIMESTAMP = None  # Unix timestamp (nastavíš přes /rc-set-next-race)
RACE_DAY_DEFAULT = "Saturday"  # Default race day
RACE_TIME_DEFAULT = "18:00"  # Default race time

# ═══════════════════════════════════════════════════════════════
# MODULE 12: TEAM MANAGEMENT
# ═══════════════════════════════════════════════════════════════
TEAMS = {
    "ferrari": {"name": "🔴 Scuderia Ferrari", "max_drivers": 2, "color": 0xDC0000},
    "mercedes": {"name": "⚪ Mercedes-AMG Petronas", "max_drivers": 2, "color": 0x00D2BE},
    "redbull": {"name": "🔵 Oracle Red Bull Racing", "max_drivers": 2, "color": 0x0600EF},
    "mclaren": {"name": "🟠 McLaren F1 Team", "max_drivers": 2, "color": 0xFF8700},
    "alpine": {"name": "💙 Alpine F1 Team", "max_drivers": 2, "color": 0x0090FF},
    "aston": {"name": "🟢 Aston Martin F1", "max_drivers": 2, "color": 0x006F62},
    "williams": {"name": "🔷 Williams Racing", "max_drivers": 2, "color": 0x005AFF},
    "haas": {"name": "⚪ MoneyGram Haas F1", "max_drivers": 2, "color": 0xFFFFFF},
    "rb": {"name": "🟦 Visa Cash App RB", "max_drivers": 2, "color": 0x0032FF},
    "sauber": {"name": "⬛ Stake F1 Sauber", "max_drivers": 2, "color": 0x00E400},
}

# ═══════════════════════════════════════════════════════════════
# MODULE 13: PRE-RACE BRIEFING
# ═══════════════════════════════════════════════════════════════
TRACKS = {
    "bahrain": {
        "name": "Bahrain International Circuit",
        "flag": "🇧🇭",
        "code": "BHR",
        "location": "Bahrain",
        "laps": 57,
        "length_km": 5.412,
        "pitlane_time": "~22s",
        "strategy": "1-stop (Medium → Hard)",
        "key_corners": "Turn 1 (heavy braking), Turn 10-11 (chicane)",
        "briefing_video": "https://www.youtube.com/watch?v=BAHRAIN_GUIDE",
        "track_map": "https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Bahrain_Circuit.png"
    },
    "jeddah": {
        "name": "Jeddah Corniche Circuit",
        "flag": "🇸🇦",
        "code": "KSA",
        "location": "Jeddah",
        "laps": 50,
        "length_km": 6.174,
        "pitlane_time": "~20s",
        "strategy": "1-stop (Medium → Hard)",
        "key_corners": "Turn 13 (blind corner), Turn 27 (final corner)",
        "briefing_video": "https://www.youtube.com/watch?v=JEDDAH_GUIDE",
        "track_map": "https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Saudi_Arabia_Circuit.png"
    },
    "australia": {
        "name": "Albert Park Circuit",
        "flag": "🇦🇺",
        "code": "AUS",
        "location": "Melbourne",
        "laps": 58,
        "length_km": 5.278,
        "pitlane_time": "~23s",
        "strategy": "1-stop (Medium → Hard) or 2-stop",
        "key_corners": "Turn 1-3 (high-speed), Turn 11-12 (chicane)",
        "briefing_video": "",
        "track_map": ""
    },
    "barcelona": {
        "name": "Circuit de Barcelona-Catalunya",
        "flag": "🇪🇸",
        "code": "ESP",
        "location": "Barcelona",
        "laps": 66,
        "length_km": 4.675,
        "pitlane_time": "~21s",
        "strategy": "2-stop (Medium → Medium → Soft)",
        "key_corners": "Turn 3 (high-speed), Turn 9 (chicane)",
        "briefing_video": "",
        "track_map": ""
    },
    "mexico": {
        "name": "Autódromo Hermanos Rodríguez",
        "flag": "🇲🇽",
        "code": "MEX",
        "location": "Mexico City",
        "laps": 71,
        "length_km": 4.304,
        "pitlane_time": "~19s",
        "strategy": "1-stop (Medium → Hard)",
        "key_corners": "Turn 1 (Stadium section), Turn 12-15 (Esses)",
        "briefing_video": "",
        "track_map": ""
    },
    # Add more tracks as needed
}

CURRENT_TRACK = "bahrain"  # Current track for this weekend

# ═══════════════════════════════════════════════════════════════
# MODULE 15: MEDIA & PRESS ROOM
# ═══════════════════════════════════════════════════════════════
PRESS_ROOM_CHANNEL_ID = None  # News channel ID

# League roles for the dropdown
LEAGUE_ROLES = [
    {"name": "⚖️ FIA", "value": "steward", "description": "Incident reviewing and rule enforcement"},
    # {"name": "🎙️ Commentator", "value": "commentator", "description": "Live commentary and race broadcasting"},
    # {"name": "🏎️ Driver", "value": "driver", "description": "Racing on track in our leagues"},
]

# Embed colors
EMBED_COLOR_PRIMARY = 0x5865F2  # Discord Blurple
EMBED_COLOR_SUCCESS = 0x57F287  # Green
EMBED_COLOR_ERROR = 0xED4245    # Red

