import os
import sys
import time
import uuid
import random
import datetime
import csv
import urllib.request
import json

# Ensure UTF-8 output on Windows terminal to prevent UnicodeEncodeError with emojis
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Define paths
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.path.dirname(os.path.abspath(__file__)))
GROUPS_CSV_PATH = os.path.join(WORKSPACE_DIR, "groups_mock_data.csv")
USERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "users_mock_data.csv")
TRACKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_playlist_tracks_mock_data.csv")

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

# Simulator settings
TICK_INTERVAL = 5.0

# Database / Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Fallback credentials if not in env
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVoaGx1ZG15dmVvaXh6a25xd250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1NjIyOTQsImV4cCI6MjA5NzEzODI5NH0.2zVm9zF1CA9SDwUvTUiXSE4fiN5adqFL4Sg29a6W1TE"

# Popular track IDs pool
popular_tracks = [
    "spotify:track:4pt5sziL6SnwDtV8b8b8b8", "spotify:track:3ybr7s4G8SdwDtV2c2c2c2", 
    "spotify:track:7p5Szil7snwdtv8b8b8b8b", "spotify:track:2tp5sziL6SnwDtV8b8b8b8",
    "spotify:track:1pt5sziL6SnwDtV8b8b8b8", "spotify:track:5pt5sziL6SnwDtV8b8b8b8", 
    "spotify:track:6pt5sziL6SnwDtV8b8b8b8", "spotify:track:8pt5sziL6SnwDtV8b8b8b8",
    "spotify:track:9pt5sziL6SnwDtV8b8b8b8", "spotify:track:0pt5sziL6SnwDtV8b8b8b8", 
    "spotify:track:7tVo52gK8SdwDtV8b8b8b8"
]

# Track play order trackers per group
group_play_orders = {}  # group_id -> last play_order index
active_tracks = []  # track lists to simulate active queue status transitions

def load_groups():
    """Load existing groups to link tracks to, ensuring foreign key integrity"""
    groups = []
    if SUPABASE_URL and SUPABASE_KEY:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/groups?select=id"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept-Profile": "app_group"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                groups = [g["id"] for g in data]
                if groups:
                    print(f"Loaded {len(groups)} groups from Supabase API.")
                    return groups
        except Exception as e:
            print(f"Warning: Could not fetch groups from Supabase: {e}", file=sys.stderr)

    if os.path.exists(GROUPS_CSV_PATH):
        try:
            with open(GROUPS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("id"):
                        groups.append(r["id"])
        except Exception as e:
            print(f"Warning: Could not parse groups CSV: {e}", file=sys.stderr)
            
    if not groups:
        print("[Warning] No groups found in groups_mock_data.csv. Generating a fallback group ID list.")
        groups = [str(uuid.uuid4()) for _ in range(10)]
    return groups

def load_users():
    """Load existing users to link as added_by"""
    users = []
    if SUPABASE_URL and SUPABASE_KEY:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/users?select=id"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept-Profile": "app_auth"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                users = [u["id"] for u in data]
                if users:
                    print(f"Loaded {len(users)} users from Supabase API.")
                    return users
        except Exception as e:
            print(f"Warning: Could not fetch users from Supabase: {e}", file=sys.stderr)

    if os.path.exists(USERS_CSV_PATH):
        try:
            with open(USERS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("id"):
                        users.append(r["id"])
        except Exception as e:
            print(f"Warning: Could not parse users CSV: {e}", file=sys.stderr)
            
    if not users:
        users = [str(uuid.uuid4()) for _ in range(50)]
    return users

# Helper to write rows to local CSV files
def append_to_csv(filepath, headers, data):
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)

# Dispatcher for Supabase REST API
def send_supabase_post(table_name, payload):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": "app_group",
        "Content-Profile": "app_group"
    }
    body = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = "(could not read body)"
        print(f"[Supabase API Error] POST {table_name} failed: HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[Supabase API Error] POST {table_name} failed: {e}", file=sys.stderr)
        return False

# Dispatcher for direct PostgreSQL connection
def insert_postgres_row(query, params):
    if not DATABASE_URL or not HAS_PG:
        return False
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[PostgreSQL Error] query failed: {e}", file=sys.stderr)
        return False

def simulate_step(groups, users):
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    actions = []

    # 1. Action: Transition status of currently active track rows (30% chance)
    if active_tracks and random.random() < 0.30:
        track = active_tracks[0]
        if track["status"] == "queued":
            track["status"] = "playing"
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_group.group_playlist_tracks SET status = 'playing' WHERE id = %s",
                    (track["id"],)
                )
            actions.append(f"TRACK PLAYING: Track {track['track_id']} is now playing in group {track['group_id'][:8]}...")
        elif track["status"] == "playing":
            track["status"] = "played"
            active_tracks.pop(0)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_group.group_playlist_tracks SET status = 'played' WHERE id = %s",
                    (track["id"],)
                )
            actions.append(f"TRACK PLAYED: Track {track['track_id']} finished playing in group {track['group_id'][:8]}...")

    # 2. Action: Queue a new track in a group (40% chance)
    if random.random() < 0.40 and groups:
        group_id = random.choice(groups)
        added_by = random.choice(users)
        track_id = random.choice(popular_tracks)
        
        # Track index play order
        if group_id not in group_play_orders:
            group_play_orders[group_id] = 0
        group_play_orders[group_id] += 1
        play_order = group_play_orders[group_id]
        
        track_row_id = str(uuid.uuid4())
        status = "queued"
        
        track_row = {
            "id": track_row_id,
            "group_id": group_id,
            "track_id": track_id,
            "added_by": added_by,
            "play_order": play_order,
            "status": status,
            "added_at": now_str
        }
        
        append_to_csv(TRACKS_CSV_PATH, [
            "id", "group_id", "track_id", "added_by", "play_order", "status", "added_at"
        ], [
            track_row["id"], track_row["group_id"], track_row["track_id"], track_row["added_by"],
            track_row["play_order"], track_row["status"], track_row["added_at"]
        ])
        send_supabase_post("group_playlist_tracks", track_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_group.group_playlist_tracks (id, group_id, track_id, added_by, play_order, status, added_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (track_row_id, group_id, track_id, added_by, play_order, status, now_dt)
            )
            
        active_tracks.append({
            "id": track_row_id,
            "group_id": group_id,
            "track_id": track_id,
            "status": status
        })
        actions.append(f"TRACK QUEUED: Track {track_id} queued by {added_by[:8]}... in group {group_id[:8]}... (order: {play_order})")

    # Limit track pool size
    if len(active_tracks) > 20:
        active_tracks.pop(0)

    return actions

def main():
    max_ticks = None
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg in ("--ticks", "-t") and i + 1 < len(sys.argv):
                try:
                    max_ticks = int(sys.argv[i + 1])
                except ValueError:
                    pass

    print("=" * 60)
    print("        MELODYMEET TRACKS MODULE LIVE DATA SIMULATOR")
    print("=" * 60)
    
    # Pre-load files
    groups = load_groups()
    users = load_users()
    
    if DATABASE_URL:
        if HAS_PG:
            print("[INFO] PostgreSQL connection detected.")
        else:
            print("[WARNING] DATABASE_URL detected, but 'psycopg2' not installed. Defaulting to local CSV & Supabase REST API.")
            
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API target active.")
        
    print("[INFO] CSV Mode: Enabled (Appends to group_playlist_tracks_mock_data.csv)")
    print("-" * 60)
    print("Simulator started. Running playlist tracks step actions every 5 seconds.")
    print("Press Ctrl+C to terminate cleanly.\n")

    tick = 0
    try:
        while True:
            tick += 1
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Reload groups/users periodically to check if groups simulator added any
            if tick % 5 == 0:
                groups = load_groups()
                users = load_users()
                
            actions = simulate_step(groups, users)
            
            print(f"[{now_str}] Tick #{tick} | Simulated {len(actions)} event actions:")
            for action in actions:
                print(f"  - {action}")
            print()
            
            if max_ticks is not None and tick >= max_ticks:
                print(f"Reached max ticks ({max_ticks}). Simulator exiting cleanly.")
                break
                
            time.sleep(TICK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
        print(f"Total simulated steps: {tick}")

if __name__ == "__main__":
    main()