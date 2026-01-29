"""
Simple JSON-based database for storing player registrations
"""
import json
import os
from datetime import datetime
from typing import Optional
import config

# Path to shared data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_FILE = os.path.join(DATA_DIR, "players.json")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)


def load_database() -> dict:
    """Load the player database from JSON file"""
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                if not isinstance(db, dict): db = {}
                if "players" not in db: db["players"] = {}
                if "attendance" not in db: db["attendance"] = {}
                if "races_history" not in db: db["races_history"] = []  # MODULE 6
                return db
        except (json.JSONDecodeError, Exception):
            print(f"⚠️ Warning: Corrupted database file. Resetting...")
            return {"players": {}, "attendance": {}, "races_history": []}
    return {"players": {}, "attendance": {}, "races_history": []}


def save_database(data: dict) -> None:
    """Save the player database to JSON file"""
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def initialize_player_structure(player_data: dict) -> dict:
    """Ensure player has all required fields for new modules"""
    defaults = {
        "total_points": 0,  # MODULE 5
        "championship_history": [],  # MODULE 5
        "penalties": {"total_points": 0, "history": []},  # MODULE 1
        "last_activity": datetime.now().isoformat(),  # MODULE 6
        "missed_races": 0,  # MODULE 6
    }
    for key, value in defaults.items():
        if key not in player_data:
            player_data[key] = value
    return player_data


def register_player(user_id: int, username: str, role: str, answers: dict = None) -> dict:
    """
    Register a new player or update existing registration with form answers
    
    Returns:
        dict with 'success', 'message', and 'is_update' keys
    """
    db = load_database()
    user_id_str = str(user_id)
    
    is_update = user_id_str in db["players"]
    
    player_data = {
        "username": username,
        "role": role,
        "answers": answers or {},
        "registered_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat() if is_update else None
    }
    
    # Initialize with new module fields
    player_data = initialize_player_structure(player_data)
    
    db["players"][user_id_str] = player_data
    save_database(db)
    
    return {
        "success": True,
        "message": "Application updated!" if is_update else "Successfully applied!",
        "is_update": is_update
    }


def get_player(user_id: int) -> Optional[dict]:
    """Get player data by user ID"""
    db = load_database()
    player = db["players"].get(str(user_id))
    if player:
        # Ensure structure is up-to-date
        player = initialize_player_structure(player)
    return player


def get_all_players() -> dict:
    """Get all registered players"""
    db = load_database()
    # Ensure all players have correct structure
    for uid in db["players"]:
        db["players"][uid] = initialize_player_structure(db["players"][uid])
    return db["players"]


def get_players_by_role(role: str) -> list:
    """Get all players in a specific role"""
    db = load_database()
    return [
        {"user_id": uid, **initialize_player_structure(data)}
        for uid, data in db["players"].items()
        if data["role"] == role
    ]


def unregister_player(user_id: int) -> bool:
    """Remove a player from the database"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str in db["players"]:
        del db["players"][user_id_str]
        save_database(db)
        return True
    return False


def update_attendance(user_id: int, username: str, status: str) -> None:
    """Update attendance status for a user for current race"""
    db = load_database()
    db["attendance"][str(user_id)] = {
        "username": username,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    save_database(db)
    
    # MODULE 6: Update last activity
    update_last_activity(user_id)


def get_attendance() -> dict:
    """Get current attendance"""
    db = load_database()
    return db["attendance"]


def reset_attendance() -> None:
    """Clear attendance for a new race"""
    db = load_database()
    db["attendance"] = {}
    save_database(db)


# ═══════════════════════════════════════════════════════════════
# MODULE 1: PENALTY SYSTEM
# ═══════════════════════════════════════════════════════════════

def add_penalty_points(user_id: int, points: int, reason: str, incident_id: str = None) -> dict:
    """Add penalty points to a player"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str not in db["players"]:
        return {"success": False, "message": "Player not found"}
    
    player = initialize_player_structure(db["players"][user_id_str])
    
    # Add to history
    penalty_entry = {
        "date": datetime.now().isoformat(),
        "points": points,
        "reason": reason,
        "incident_id": incident_id
    }
    player["penalties"]["history"].append(penalty_entry)
    player["penalties"]["total_points"] += points
    
    db["players"][user_id_str] = player
    save_database(db)
    
    total = player["penalties"]["total_points"]
    exceeded = total >= config.PENALTY_POINTS_LIMIT
    
    return {
        "success": True,
        "total_points": total,
        "limit_exceeded": exceeded
    }


def get_penalty_points(user_id: int) -> int:
    """Get total penalty points for a player"""
    player = get_player(user_id)
    if not player:
        return 0
    return player.get("penalties", {}).get("total_points", 0)


def get_penalty_history(user_id: int) -> list:
    """Get penalty history for a player"""
    player = get_player(user_id)
    if not player:
        return []
    return player.get("penalties", {}).get("history", [])


def reset_penalty_points(user_id: int) -> bool:
    """Reset penalty points for a player"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str not in db["players"]:
        return False
    
    db["players"][user_id_str]["penalties"] = {
        "total_points": 0,
        "history": []
    }
    save_database(db)
    return True


# ═══════════════════════════════════════════════════════════════
# MODULE 2: DYNAMIC LINEUP
# ═══════════════════════════════════════════════════════════════

def get_race_lineup() -> list:
    """Get list of drivers registered for current race with their EA IDs"""
    db = load_database()
    lineup = []
    
    for user_id_str, attendance_data in db["attendance"].items():
        if attendance_data.get("status") == "Driver":
            # Get player data for EA ID
            player = db["players"].get(user_id_str, {})
            ea_id = player.get("answers", {}).get("ea_id", "N/A")
            
            lineup.append({
                "user_id": user_id_str,
                "username": attendance_data.get("username", "Unknown"),
                "ea_id": ea_id,
                "mention": f"<@{user_id_str}>"
            })
    
    return lineup


# ═══════════════════════════════════════════════════════════════
# MODULE 5: RACE RESULTS & STANDINGS
# ═══════════════════════════════════════════════════════════════

def add_race_result(user_id: int, race_name: str, position: int, fastest_lap: bool = False) -> dict:
    """Add race result and calculate championship points"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str not in db["players"]:
        return {"success": False, "message": "Player not found"}
    
    player = initialize_player_structure(db["players"][user_id_str])
    
    # Calculate points
    points = 0
    if 1 <= position <= len(config.POINTS_SYSTEM):
        points = config.POINTS_SYSTEM[position - 1]
    
    # Add fastest lap bonus
    if fastest_lap and position <= config.FASTEST_LAP_MIN_POSITION:
        points += config.FASTEST_LAP_BONUS
    
    # Add to history
    race_entry = {
        "race_name": race_name,
        "position": position,
        "points": points,
        "fastest_lap": fastest_lap,
        "date": datetime.now().isoformat()
    }
    player["championship_history"].append(race_entry)
    player["total_points"] += points
    
    db["players"][user_id_str] = player
    save_database(db)
    
    return {
        "success": True,
        "points_awarded": points,
        "new_total": player["total_points"]
    }


def get_championship_standings() -> list:
    """Get championship standings sorted by total points"""
    db = load_database()
    standings = []
    
    for user_id, player in db["players"].items():
        if player.get("role") == "driver":  # Only drivers in standings
            player = initialize_player_structure(player)
            standings.append({
                "user_id": user_id,
                "username": player.get("username", "Unknown"),
                "total_points": player.get("total_points", 0),
                "races_completed": len(player.get("championship_history", []))
            })
    
    # Sort by points (descending)
    standings.sort(key=lambda x: x["total_points"], reverse=True)
    return standings


def get_user_race_history(user_id: int) -> list:
    """Get race history for a specific user"""
    player = get_player(user_id)
    if not player:
        return []
    return player.get("championship_history", [])


# ═══════════════════════════════════════════════════════════════
# MODULE 6: ACTIVITY TRACKING
# ═══════════════════════════════════════════════════════════════

def update_last_activity(user_id: int) -> None:
    """Update last activity timestamp for a user"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str in db["players"]:
        db["players"][user_id_str]["last_activity"] = datetime.now().isoformat()
        save_database(db)


def track_race_attendance(race_name: str, participant_ids: list) -> None:
    """Track which users participated in a race"""
    db = load_database()
    
    # Add race to history
    race_entry = {
        "race_name": race_name,
        "date": datetime.now().isoformat(),
        "participants": participant_ids
    }
    db["races_history"].append(race_entry)
    
    # Update missed races counter
    for user_id_str, player in db["players"].items():
        if player.get("role") == "driver":
            user_id = int(user_id_str)
            if user_id in participant_ids:
                # Reset missed races
                db["players"][user_id_str]["missed_races"] = 0
            else:
                # Increment missed races
                current = db["players"][user_id_str].get("missed_races", 0)
                db["players"][user_id_str]["missed_races"] = current + 1
    
    save_database(db)


def get_inactive_users(threshold: int = None) -> list:
    """Get list of inactive users based on missed races threshold"""
    if threshold is None:
        threshold = config.INACTIVITY_THRESHOLD
    
    db = load_database()
    inactive = []
    
    for user_id, player in db["players"].items():
        if player.get("role") == "driver":
            missed = player.get("missed_races", 0)
            if missed >= threshold:
                inactive.append({
                    "user_id": user_id,
                    "username": player.get("username", "Unknown"),
                    "missed_races": missed,
                    "last_activity": player.get("last_activity", "N/A")
                })
    
    return inactive


def reset_missed_races(user_id: int) -> bool:
    """Reset missed races counter for a user"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str in db["players"]:
        db["players"][user_id_str]["missed_races"] = 0
        save_database(db)
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# MODULE 4: DATA EXPORT
# ═══════════════════════════════════════════════════════════════

def export_to_csv_string() -> str:
    """Export all player data to CSV string"""
    import csv
    import io
    
    players = get_all_players()
    if not players:
        return ""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Gather all possible keys
    base_headers = ["User ID", "Username", "Role", "Total Points", "Penalty Points", "Missed Races", "Last Activity"]
    answer_keys = set()
    for uid, p in players.items():
        ans = p.get("answers", {})
        if ans:
            answer_keys.update(ans.keys())
    
    sorted_keys = sorted(list(answer_keys))
    writer.writerow(base_headers + sorted_keys)
    
    # Write rows
    for uid, p in players.items():
        row = [
            uid,
            p.get('username', 'Unknown'),
            p.get('role', 'unknown'),
            p.get('total_points', 0),
            p.get('penalties', {}).get('total_points', 0),
            p.get('missed_races', 0),
            p.get('last_activity', 'N/A')
        ]
        ans = p.get("answers", {})
        for k in sorted_keys:
            row.append(ans.get(k, ""))
        writer.writerow(row)
    
    output.seek(0)
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════
# LEGACY IMPORT FUNCTION (kept for compatibility)
# ═══════════════════════════════════════════════════════════════

def import_from_csv(csv_content: str) -> dict:
    """
    Import player data from CSV content (as exported by rc-export-databaze).
    
    Returns:
        dict with 'success', 'imported_count', 'errors' keys
    """
    import csv
    import io
    
    db = load_database()
    imported = 0
    errors = []
    
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        base_keys = {"User ID", "Username", "Role", "Total Points", "Penalty Points", "Missed Races", "Last Activity"}
        
        for row in reader:
            try:
                user_id = row.get("User ID")
                username = row.get("Username", "Unknown")
                role = row.get("Role", "driver")
                
                if not user_id:
                    errors.append(f"Missing User ID in row: {row}")
                    continue
                
                # Reconstruct answers from remaining columns
                answers = {}
                for key, value in row.items():
                    if key not in base_keys and value:
                        answers[key.lower().replace(" ", "_")] = value
                
                player_data = {
                    "username": username,
                    "role": role,
                    "answers": answers,
                    "total_points": int(row.get("Total Points", 0)),
                    "penalties": {"total_points": int(row.get("Penalty Points", 0)), "history": []},
                    "missed_races": int(row.get("Missed Races", 0)),
                    "last_activity": row.get("Last Activity", datetime.now().isoformat()),
                    "registered_at": datetime.now().isoformat(),
                    "updated_at": None
                }
                
                db["players"][str(user_id)] = initialize_player_structure(player_data)
                imported += 1
                
            except Exception as e:
                errors.append(f"Error processing row: {e}")
        
        save_database(db)
        
        return {
            "success": True,
            "imported_count": imported,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "imported_count": 0,
            "errors": [str(e)]
        }


# ═══════════════════════════════════════════════════════════════
# MODULE 11: HALL OF FAME (Records Tracking)
# ═══════════════════════════════════════════════════════════════

def get_records() -> dict:
    """Get all league records"""
    db = load_database()
    if "records" not in db:
        db["records"] = {
            "most_wins": {"user_id": None, "count": 0, "username": "N/A"},
            "most_poles": {"user_id": None, "count": 0, "username": "N/A"},
            "most_podiums": {"user_id": None, "count": 0, "username": "N/A"},
            "most_fastest_laps": {"user_id": None, "count": 0, "username": "N/A"},
            "highest_single_season_points": {"user_id": None, "points": 0, "username": "N/A"}
        }
        save_database(db)
    return db["records"]


def update_records() -> None:
    """Update all records based on current player data"""
    db = load_database()
    
    # Initialize records if not exist
    if "records" not in db:
        db["records"] = {}
    
    # Track stats for all drivers
    stats = {}
    for user_id, player in db["players"].items():
        if player.get("role") != "driver":
            continue
            
        history = player.get("championship_history", [])
        if not history:
            continue
        
        stats[user_id] = {
            "username": player.get("username", "Unknown"),
            "wins": sum(1 for r in history if r.get("position") == 1),
            "poles": player.get("pole_positions", 0),  # Real pole positions from qualifying
            "podiums": sum(1 for r in history if r.get("position", 99) <= 3),
            "fastest_laps": sum(1 for r in history if r.get("fastest_lap")),
            "total_points": player.get("total_points", 0)
        }
    
    if not stats:
        return
    
    # Find record holders
    most_wins = max(stats.items(), key=lambda x: x[1]["wins"])
    most_poles = max(stats.items(), key=lambda x: x[1]["poles"])
    most_podiums = max(stats.items(), key=lambda x: x[1]["podiums"])
    most_fastest_laps = max(stats.items(), key=lambda x: x[1]["fastest_laps"])
    highest_points = max(stats.items(), key=lambda x: x[1]["total_points"])
    
    db["records"] = {
        "most_wins": {
            "user_id": most_wins[0],
            "count": most_wins[1]["wins"],
            "username": most_wins[1]["username"]
        },
        "most_poles": {
            "user_id": most_poles[0],
            "count": most_poles[1]["poles"],
            "username": most_poles[1]["username"]
        },
        "most_podiums": {
            "user_id": most_podiums[0],
            "count": most_podiums[1]["podiums"],
            "username": most_podiums[1]["username"]
        },
        "most_fastest_laps": {
            "user_id": most_fastest_laps[0],
            "count": most_fastest_laps[1]["fastest_laps"],
            "username": most_fastest_laps[1]["username"]
        },
        "highest_single_season_points": {
            "user_id": highest_points[0],
            "points": highest_points[1]["total_points"],
            "username": highest_points[1]["username"]
        }
    }
    
    save_database(db)


def get_driver_stats(user_id: int) -> dict:
    """Get comprehensive statistics for a driver"""
    player = get_player(user_id)
    if not player or player.get("role") != "driver":
        return {}
    
    history = player.get("championship_history", [])
    
    return {
        "total_races": len(history),
        "wins": sum(1 for r in history if r.get("position") == 1),
        "podiums": sum(1 for r in history if r.get("position", 99) <= 3),
        "fastest_laps": sum(1 for r in history if r.get("fastest_lap")),
        "total_points": player.get("total_points", 0),
        "average_position": sum(r.get("position", 99) for r in history) / len(history) if history else 0,
        "best_finish": min((r.get("position", 99) for r in history), default=99)
    }


# ═══════════════════════════════════════════════════════════════
# QUALIFYING RESULTS (For Pole Position Tracking)
# ═══════════════════════════════════════════════════════════════

def add_qualifying_result(user_id: int, race_name: str, position: int) -> dict:
    """Add qualifying result and track pole positions"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str not in db["players"]:
        return {"success": False, "message": "Player not found"}
    
    player = initialize_player_structure(db["players"][user_id_str])
    
    # Initialize qualifying history if not exists
    if "qualifying_history" not in player:
        player["qualifying_history"] = []
    if "pole_positions" not in player:
        player["pole_positions"] = 0
    
    # Track pole position
    if position == 1:
        player["pole_positions"] += 1
    
    # Add to history
    quali_entry = {
        "race_name": race_name,
        "position": position,
        "date": datetime.now().isoformat()
    }
    player["qualifying_history"].append(quali_entry)
    
    db["players"][user_id_str] = player
    save_database(db)
    
    return {
        "success": True,
        "position": position,
        "is_pole": position == 1,
        "total_poles": player["pole_positions"]
    }


def get_qualifying_history(user_id: int) -> list:
    """Get qualifying history for a player"""
    player = get_player(user_id)
    if not player:
        return []
    return player.get("qualifying_history", [])



# ═══════════════════════════════════════════════════════════════
# MODULE 12: TEAM MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def assign_team(user_id: int, team_id: str) -> dict:
    """Assign a driver to a team"""
    db = load_database()
    user_id_str = str(user_id)
    
    if user_id_str not in db["players"]:
        return {"success": False, "message": "Player not found"}
    
    # Check if team exists
    if team_id not in config.TEAMS:
        return {"success": False, "message": "Team not found"}
    
    # Check if team is full
    if is_team_full(team_id):
        return {"success": False, "message": "Team is full"}
    
    db["players"][user_id_str]["team"] = team_id
    save_database(db)
    
    return {"success": True, "team": team_id}


def get_team_drivers(team_id: str) -> list:
    """Get all drivers in a specific team"""
    db = load_database()
    drivers = []
    
    for user_id, player in db["players"].items():
        if player.get("team") == team_id and player.get("role") == "driver":
            drivers.append({
                "user_id": user_id,
                "username": player.get("username", "Unknown"),
                "total_points": player.get("total_points", 0)
            })
    
    return drivers


def is_team_full(team_id: str) -> bool:
    """Check if a team has reached its driver limit"""
    if team_id not in config.TEAMS:
        return True
    
    max_drivers = config.TEAMS[team_id]["max_drivers"]
    current_drivers = len(get_team_drivers(team_id))
    
    return current_drivers >= max_drivers


def get_constructor_standings() -> list:
    """Get constructor championship standings"""
    db = load_database()
    team_points = {}
    
    # Calculate points for each team
    for team_id, team_data in config.TEAMS.items():
        drivers = get_team_drivers(team_id)
        total_points = sum(d["total_points"] for d in drivers)
        
        team_points[team_id] = {
            "name": team_data["name"],
            "points": total_points,
            "drivers": drivers,
            "color": team_data["color"]
        }
    
    # Sort by points
    standings = sorted(team_points.items(), key=lambda x: x[1]["points"], reverse=True)
    
    return [{"team_id": tid, **data} for tid, data in standings]


# ═══════════════════════════════════════════════════════════════
# MODULE 14: DYNAMIC RACE CALENDAR
# ═══════════════════════════════════════════════════════════════

def get_calendar() -> list:
    """Get the full race calendar"""
    db = load_database()
    if "calendar" not in db:
        db["calendar"] = []
        save_database(db)
    return db["calendar"]


def add_race_to_calendar(round_num: int, race_name: str, track: str, timestamp: int) -> bool:
    """Add a race to the calendar"""
    db = load_database()
    if "calendar" not in db:
        db["calendar"] = []
    
    race_entry = {
        "round": round_num,
        "race_name": race_name,
        "track": track,
        "date_timestamp": timestamp,
        "status": "upcoming"
    }
    
    db["calendar"].append(race_entry)
    save_database(db)
    return True


def get_next_race() -> Optional[dict]:
    """Get the next upcoming race"""
    calendar = get_calendar()
    upcoming = [r for r in calendar if r.get("status") == "upcoming"]
    
    if not upcoming:
        return None
    
    # Sort by timestamp
    upcoming.sort(key=lambda x: x.get("date_timestamp", 0))
    return upcoming[0] if upcoming else None


def mark_race_completed(round_number: int) -> bool:
    """Mark a race as completed"""
    db = load_database()
    if "calendar" not in db:
        return False
    
    for race in db["calendar"]:
        if race.get("round") == round_number:
            race["status"] = "completed"
            save_database(db)
            return True
    
    return False


def get_completed_races() -> list:
    """Get all completed races"""
    calendar = get_calendar()
    return [r for r in calendar if r.get("status") == "completed"]


def get_upcoming_races() -> list:
    """Get all upcoming races"""
    calendar = get_calendar()
    upcoming = [r for r in calendar if r.get("status") == "upcoming"]
    upcoming.sort(key=lambda x: x.get("date_timestamp", 0))
    return upcoming

