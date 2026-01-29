"""
Simple JSON-based database for storing player registrations
"""
import json
import os
from datetime import datetime
from typing import Optional
import config

DATABASE_FILE = "players.json"


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
