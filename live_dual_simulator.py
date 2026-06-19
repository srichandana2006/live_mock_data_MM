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
USERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "users_mock_data.csv")

ROOMS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_rooms_mock_data.csv")
PARTICIPANTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_participants_mock_data.csv")
MESSAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_messages_mock_data.csv")
CALLS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_calls_mock_data.csv")
MATCHES_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_matches_mock_data.csv")
SONGS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_song_requests_mock_data.csv")

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

# Simulator settings
TICK_INTERVAL = 5.0

# Database / Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Fallback credentials from test script if not in env
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVoaGx1ZG15dmVvaXh6a25xd250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1NjIyOTQsImV4cCI6MjA5NzEzODI5NH0.2zVm9zF1CA9SDwUvTUiXSE4fiN5adqFL4Sg29a6W1TE"

# Seed data pools
room_names = [
    "Acoustic Cozy Space", "Bollywood Duet", "K-Pop Fan Hangout", "Telugu Melodies Vibe",
    "Rock Duo Jam", "Jazz Corner Session", "Lo-Fi Focus Partners", "Coding duo",
    "EDM Rhythm Match", "Indie Chill Room", "Late Night Melodies"
]

interests = ['Lo-Fi', 'Bollywood', 'EDM', 'Rock', 'Jazz', 'Acoustic', 'K-Pop', 'Classical']

messages_pool = [
    "Hey! Love this track.", "Vibing so hard right now.", "Which song should we request next?",
    "🔥", "🙌", "This is pure gold.", "Awesome playlist!", "Arijit Singh hits different.",
    "Check out this cover.", "Is anyone else listening?", "Let's queue some techno.",
    "Can we do a call?", "Sure, start the call!", "Let's rock this room."
]

songs_pool = [
    ("Kesariya", "Arijit Singh"),
    ("Dynamite", "BTS"),
    ("Starboy", "The Weeknd"),
    ("Naatu Naatu", "M. M. Keeravani"),
    ("In the End", "Linkin Park"),
    ("Take Five", "Dave Brubeck"),
    ("Get Lucky", "Daft Punk"),
    ("Lofi Rain", "Chillhop Music"),
    ("Fix You", "Coldplay"),
    ("Blinding Lights", "The Weeknd")
]

# Track active elements to preserve relationships during ticks
active_rooms = []
active_calls = []

def load_user_pool():
    """Load existing users from CSV to maintain proper referential integrity"""
    users = []
    if os.path.exists(USERS_CSV_PATH):
        try:
            with open(USERS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("id"):
                        users.append(row["id"])
        except Exception as e:
            print(f"Warning: Could not parse users CSV: {e}", file=sys.stderr)
            
    if not users:
        print("[Warning] No user pool loaded from users_mock_data.csv. Generating local mock user list.")
        users = [str(uuid.uuid4()) for _ in range(500)]
    else:
        print(f"Successfully loaded {len(users)} users for matched operations.")
    return users

def generate_room_code():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(6))

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
        "Accept-Profile": "app_dual",
        "Content-Profile": "app_dual"
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

# =====================================================================
# MODIFIED SECTION: Added send_supabase_patch helper for PATCH/UPDATE
# =====================================================================
def send_supabase_patch(table_name, payload, query_params):
    """Dispatcher for Supabase REST API updates (PATCH)"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    query_str = "&".join(f"{k}=eq.{v}" for k, v in query_params.items())
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}?{query_str}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": "app_dual",
        "Content-Profile": "app_dual"
    }
    body = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201, 204)
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = "(could not read body)"
        print(f"[Supabase API Error] PATCH {table_name} failed: HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[Supabase API Error] PATCH {table_name} failed: {e}", file=sys.stderr)
        return False
# =====================================================================
# MODIFIED SECTION END
# =====================================================================

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

def simulate_step(users):
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    now_tz_str = now_dt.isoformat()
    
    actions = []

    # 1. Action: Create a Room & matched dual participants (15% chance)
    if random.random() < 0.15 or len(active_rooms) < 2:
        room_id = str(uuid.uuid4())
        creator_id = random.choice(users)
        partner_id = random.choice([u for u in users if u != creator_id])
        
        room_name = random.choice(room_names)
        room_code = generate_room_code()
        room_type = random.choice(["public", "private"])
        max_p = random.choice([2, 4])
        track_id = f"spotify:track:{''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(22))}"
        
        # dual_rooms payload
        room_row = {
            "id": room_id,
            "room_code": room_code,
            "room_name": room_name,
            "room_type": room_type,
            "status": "active",
            "created_at": now_str,
            "created_by": creator_id,
            "ended_at": None,
            "max_participants": max_p,
            "music_track": track_id
        }
        
        append_to_csv(ROOMS_CSV_PATH, [
            "id", "room_code", "room_name", "room_type", "status", "created_at", "created_by", "ended_at", "max_participants", "music_track"
        ], [
            room_row["id"], room_row["room_code"], room_row["room_name"], room_row["room_type"], room_row["status"],
            room_row["created_at"], room_row["created_by"], room_row["ended_at"], room_row["max_participants"], room_row["music_track"]
        ])
        send_supabase_post("dual_rooms", room_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_dual.dual_rooms (id, room_code, room_name, room_type, status, created_at, created_by, ended_at, max_participants, music_track) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (room_id, room_code, room_name, room_type, "active", now_dt, creator_id, None, max_p, track_id)
            )
            
        # dual_participants (Creator / Host)
        p1_id = str(uuid.uuid4())
        p1_row = {
            "id": p1_id,
            "room_id": room_id,
            "user_id": creator_id,
            "joined_at": now_str,
            "left_at": None,
            "is_host": True,
            "device_type": random.choice(["mobile", "web", "desktop"])
        }
        append_to_csv(PARTICIPANTS_CSV_PATH, [
            "id", "room_id", "user_id", "joined_at", "left_at", "is_host", "device_type"
        ], [
            p1_row["id"], p1_row["room_id"], p1_row["user_id"], p1_row["joined_at"], p1_row["left_at"], p1_row["is_host"], p1_row["device_type"]
        ])
        send_supabase_post("dual_participants", p1_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_dual.dual_participants (id, room_id, user_id, joined_at, left_at, is_host, device_type) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (p1_id, room_id, creator_id, now_dt, None, True, p1_row["device_type"])
            )

        # dual_participants (Partner / Guest)
        p2_id = str(uuid.uuid4())
        p2_row = {
            "id": p2_id,
            "room_id": room_id,
            "user_id": partner_id,
            "joined_at": now_str,
            "left_at": None,
            "is_host": False,
            "device_type": random.choice(["mobile", "web", "desktop"])
        }
        append_to_csv(PARTICIPANTS_CSV_PATH, [
            "id", "room_id", "user_id", "joined_at", "left_at", "is_host", "device_type"
        ], [
            p2_row["id"], p2_row["room_id"], p2_row["user_id"], p2_row["joined_at"], p2_row["left_at"], p2_row["is_host"], p2_row["device_type"]
        ])
        send_supabase_post("dual_participants", p2_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_dual.dual_participants (id, room_id, user_id, joined_at, left_at, is_host, device_type) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (p2_id, room_id, partner_id, now_dt, None, False, p2_row["device_type"])
            )

        # Cache active room mapping
        active_rooms.append({
            "id": room_id,
            "creator": creator_id,
            "partner": partner_id,
            "participants": [creator_id, partner_id]
        })
        actions.append(f"ROOM CREATED: '{room_name}' ({room_code}) | Matched users {creator_id[:8]}... & {partner_id[:8]}...")

    # Ensure we have active rooms to continue other operations
    if active_rooms:
        room = random.choice(active_rooms)
        room_id = room["id"]
        
        # 2. Action: Chat Message in Room (40% chance)
        if random.random() < 0.40:
            msg_id = str(uuid.uuid4())
            sender_id = random.choice(room["participants"])
            msg_text = random.choice(messages_pool)
            msg_type = random.choice(["text", "emoji", "image", "gif"])
            
            message_row = {
                "id": msg_id,
                "room_id": room_id,
                "sender_user_id": sender_id,
                "message": msg_text,
                "message_type": msg_type,
                "sent_at": now_tz_str
            }
            append_to_csv(MESSAGES_CSV_PATH, [
                "id", "room_id", "sender_user_id", "message", "message_type", "sent_at"
            ], [
                message_row["id"], message_row["room_id"], message_row["sender_user_id"], message_row["message"], message_row["message_type"], message_row["sent_at"]
            ])
            send_supabase_post("dual_messages", message_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_dual.dual_messages (id, room_id, sender_user_id, message, message_type, sent_at) VALUES (%s,%s,%s,%s,%s::app_dual.message_type_enum,%s)",
                    (msg_id, room_id, sender_id, msg_text, msg_type, now_dt)
                )
            actions.append(f"MESSAGE sent by {sender_id[:8]}... inside Room {room_id[:8]}... ('{msg_text[:15]}')")

        # 3. Action: Call Activity (20% chance)
        # If no active call, initiate one. If active call exists, end it.
        if active_calls and random.random() < 0.50:
            ended_call = active_calls.pop(0)
            ended_at = now_dt
            dur = int((ended_at - ended_call["start_time"]).total_seconds())
            
            # Update CSV details
            call_row_csv = [
                ended_call["id"], ended_call["room_id"], ended_call["type"],
                ended_call["start_time"].strftime("%Y-%m-%d %H:%M:%S"), ended_at.strftime("%Y-%m-%d %H:%M:%S"),
                "completed", dur
            ]
            append_to_csv(CALLS_CSV_PATH, [
                "id", "room_id", "call_type", "started_at", "ended_at", "call_status", "duration_seconds"
            ], call_row_csv)
            
# =====================================================================
# MODIFIED SECTION: Converted duplicate POST to PATCH update
# =====================================================================
            call_update_payload = {
                "ended_at": ended_at.strftime("%Y-%m-%d %H:%M:%S"),
                "call_status": "completed",
                "duration_seconds": dur
            }
            send_supabase_patch("dual_calls", call_update_payload, {"id": ended_call["id"]})
# =====================================================================
# MODIFIED SECTION END
# =====================================================================
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_dual.dual_calls SET ended_at = %s, call_status = 'completed', duration_seconds = %s WHERE id = %s",
                    (ended_at, dur, ended_call["id"])
                )
            actions.append(f"CALL ENDED inside Room {ended_call['room_id'][:8]}... | Duration: {dur}s")
        elif random.random() < 0.20:
            call_id = str(uuid.uuid4())
            call_type = random.choice(["audio", "video"])
            
            call_row = {
                "id": call_id,
                "room_id": room_id,
                "call_type": call_type,
                "started_at": now_str,
                "ended_at": None,
                "call_status": "connected",
                "duration_seconds": None
            }
            append_to_csv(CALLS_CSV_PATH, [
                "id", "room_id", "call_type", "started_at", "ended_at", "call_status", "duration_seconds"
            ], [
                call_row["id"], call_row["room_id"], call_row["call_type"], call_row["started_at"], call_row["ended_at"], call_row["call_status"], call_row["duration_seconds"]
            ])
            send_supabase_post("dual_calls", call_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_dual.dual_calls (id, room_id, call_type, started_at, ended_at, call_status, duration_seconds) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (call_id, room_id, call_type, now_dt, None, "connected", None)
                )
            active_calls.append({
                "id": call_id,
                "room_id": room_id,
                "type": call_type,
                "start_time": now_dt
            })
            actions.append(f"CALL CONNECTED inside Room {room_id[:8]}... (Type: {call_type})")

        # 4. Action: Song Request (25% chance)
        if random.random() < 0.25:
            req_id = str(uuid.uuid4())
            req_by = random.choice(room["participants"])
            song = random.choice(songs_pool)
            status = random.choice(["pending", "accepted", "played", "skipped", "rejected"])
            played_at = now_str if status == "played" else None
            
            song_row = {
                "id": req_id,
                "room_id": room_id,
                "requested_by": req_by,
                "song_name": song[0],
                "artist_name": song[1],
                "requested_at": now_str,
                "request_status": status,
                "played_at": played_at
            }
            append_to_csv(SONGS_CSV_PATH, [
                "id", "room_id", "requested_by", "song_name", "artist_name", "requested_at", "request_status", "played_at"
            ], [
                song_row["id"], song_row["room_id"], song_row["requested_by"], song_row["song_name"], song_row["artist_name"],
                song_row["requested_at"], song_row["request_status"], song_row["played_at"]
            ])
            send_supabase_post("dual_song_requests", song_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_dual.dual_song_requests (id, room_id, requested_by, song_name, artist_name, requested_at, request_status, played_at) VALUES (%s,%s,%s,%s,%s,%s,%s::app_dual.request_status_enum,%s)",
                    (req_id, room_id, req_by, song[0], song[1], now_dt, status, now_dt if played_at else None)
                )
            actions.append(f"SONG REQUEST: '{song[0]}' by {song[1]} inside Room {room_id[:8]}... (Status: {status})")

    # 5. Action: New Match between Users (20% chance)
    if random.random() < 0.20:
        match_id = str(uuid.uuid4())
        u1 = random.choice(users)
        u2 = random.choice([u for u in users if u != u1])
        status = random.choice(["pending", "connected", "expired"])
        interest = random.choice(interests)
        duration = random.randint(30, 3600)
        
        match_row = {
            "id": match_id,
            "user_one": u1,
            "user_two": u2,
            "match_status": status,
            "created_at": now_str,
            "matched_on_interest": interest,
            "match_duration": duration
        }
        append_to_csv(MATCHES_CSV_PATH, [
            "id", "user_one", "user_two", "match_status", "created_at", "matched_on_interest", "match_duration"
        ], [
            match_row["id"], match_row["user_one"], match_row["user_two"], match_row["match_status"],
            match_row["created_at"], match_row["matched_on_interest"], match_row["match_duration"]
        ])
        send_supabase_post("dual_matches", match_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_dual.dual_matches (id, user_one, user_two, match_status, created_at, matched_on_interest, match_duration) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (match_id, u1, u2, status, now_dt, interest, duration)
            )
        actions.append(f"NEW MATCH: {u1[:8]}... & {u2[:8]}... on '{interest}' (Status: {status})")

    # Clean up older active rooms (keep pool bounded to active simulation)
    if len(active_rooms) > 15:
        old_room = active_rooms.pop(0)
        # Randomly flag it ended in CSV/DB
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "UPDATE app_dual.dual_rooms SET ended_at = %s, status = 'inactive' WHERE id = %s",
                (now_dt, old_room["id"])
            )

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
    print("        MELODYMEET DUAL MODULE LIVE DATA SIMULATOR")
    print("=" * 60)
    
    users = load_user_pool()
    
    if DATABASE_URL:
        if HAS_PG:
            print("[INFO] PostgreSQL connection detected in environment.")
        else:
            print("[WARNING] DATABASE_URL detected, but 'psycopg2' is not installed. Defaulting to local files & Supabase REST API.")
            
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API target active.")
        
    print(f"[INFO] CSV Mode: Enabled (Appends to dual_*_mock_data.csv files)")
    print("-" * 60)
    print("Simulator started. Running step actions every 5 seconds.")
    print("Press Ctrl+C to terminate cleanly.\n")

    tick = 0
    try:
        while True:
            tick += 1
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            actions = simulate_step(users)
            
            print(f"[{now_str}] Tick #{tick} | Simulated {len(actions)} event actions:")
            for action in actions:
                print(f"  - {action}")
            print()
            
            if max_ticks is not None and tick >= max_ticks:
                print(f"Reached max ticks ({max_ticks}). Simulator exiting cleanly.")
                break
                
            # Sleep exact interval
            time.sleep(TICK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
        print(f"Total simulated steps: {tick}")

if __name__ == "__main__":
    main()
