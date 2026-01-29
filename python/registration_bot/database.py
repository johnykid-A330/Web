import json
import os
import datetime

DB_FILE = "players.json"

def load_database():
    if not os.path.exists(DB_FILE):
        return {"players": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return {"players": {}}

def save_database(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving database: {e}")

def register_player(user_id, username, role, answers):
    db = load_database()
    user_id_str = str(user_id)
    
    db["players"][user_id_str] = {
        "username": username,
        "role": role,
        "answers": answers,
        "registered_at": datetime.datetime.now().isoformat()
    }
    save_database(db)
    return True

def get_player(user_id):
    db = load_database()
    return db["players"].get(str(user_id))

def unregister_player(user_id):
    db = load_database()
    if str(user_id) in db["players"]:
        del db["players"][str(user_id)]
        save_database(db)
        return True
    return False

def get_all_players():
    db = load_database()
    # Convert dict to list
    return list(db["players"].values())

def get_players_by_role(role_name):
    db = load_database()
    return [p for p in db["players"].values() if p.get("role") == role_name]

def is_team_full(team_id):
    # This bot might not have the full live Grid awareness if it's separate, 
    # but we can check the local json DB for admitted drivers.
    # However, 'is_team_full' usually relies on knowing the MAX drivers.
    # We will verify against config.
    from config import TEAMS
    
    max_drivers = TEAMS.get(team_id, {}).get("max_drivers", 2) # Default 2 if not strict
    
    db = load_database()
    count = 0
    for p in db["players"].values():
        if p.get("role") == "driver":
            # Check team in their answers
            p_team = p.get("answers", {}).get("team")
            if p_team == team_id:
                count += 1
    
    return count >= max_drivers
