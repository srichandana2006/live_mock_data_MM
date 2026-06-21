import os
import sys
import time
import uuid
import random
import datetime
import csv
import urllib.request
import json
import db_helpers


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
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
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
    """Load existing users from Supabase or CSV to maintain proper referential integrity"""
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
                    print(f"Successfully loaded {len(users)} users from Supabase API.")
                    return users
        except Exception as e:
            print(f"Warning: Could not fetch users from Supabase: {e}", file=sys.stderr)

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
        print("[Warning] No user pool loaded. Generating local mock user list.")
        users = [str(uuid.uuid4()) for _ in range(500)]
    else:
        print(f"Successfully loaded {len(users)} users for matched operations.")
    return users

def generate_room_code():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(6))

def to_bigint(uuid_str):
    if not uuid_str:
        return None
    try:
        return uuid.UUID(uuid_str).int & 0x7FFFFFFFFFFFFFFF
    except (ValueError, TypeError):
        return random.randint(1, 9223372036854775807)

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

def simulate_step():
    users = [u["id"] for u in db_helpers.USERS]
    if not users:
        print("[WARNING] Skipping simulation step: No active users in Supabase cache.", file=sys.stderr)
        return []
        
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
        room_dur = random.randint(10, 480)
        ended_dt = now_dt + datetime.timedelta(minutes=room_dur)
        ended_str = ended_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        room_row = {
            "id": room_id,
            "room_code": room_code,
            "room_name": room_name,
            "room_type": room_type,
            "status": "ended",
            "created_at": now_str,
            "created_by": creator_id,
            "ended_at": ended_str,
            "music_track": track_id
        }
        
        append_to_csv(ROOMS_CSV_PATH, [
            "id", "room_code", "room_name", "room_type", "status", "created_at", "created_by", "ended_at", "music_track"
        ], [
            room_row["id"], room_row["room_code"], room_row["room_name"], room_row["room_type"], room_row["status"],
            room_row["created_at"], room_row["created_by"], room_row["ended_at"], room_row["music_track"]
        ])
        room_supabase_success = send_supabase_post("dual_rooms", room_row)
        room_pg_success = True
        if DATABASE_URL and HAS_PG:
            room_pg_success = insert_postgres_row(
                "INSERT INTO app_dual.dual_rooms (id, room_code, room_name, room_type, status, created_at, created_by, ended_at, music_track) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (room_id, room_code, room_name, room_type, "ended", now_dt, creator_id, ended_dt, track_id)
            )
            
        if room_supabase_success and room_pg_success:
            # dual_participants (Creator / Host)
            p1_dur = random.randint(5, 240)
            p1_left_dt = now_dt + datetime.timedelta(minutes=p1_dur)
            p1_left_str = p1_left_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            p1_id = str(uuid.uuid4())
            p1_row = {
                "id": p1_id,
                "room_id": room_id,
                "user_id": creator_id,
                "joined_at": now_str,
                "left_at": p1_left_str,
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
                    (p1_id, room_id, creator_id, now_dt, p1_left_dt, True, p1_row["device_type"])
                )
     
            # dual_participants (Partner / Guest)
            p2_dur = random.randint(5, 240)
            p2_left_dt = now_dt + datetime.timedelta(minutes=p2_dur)
            p2_left_str = p2_left_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            p2_id = str(uuid.uuid4())
            p2_row = {
                "id": p2_id,
                "room_id": room_id,
                "user_id": partner_id,
                "joined_at": now_str,
                "left_at": p2_left_str,
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
                    (p2_id, room_id, partner_id, now_dt, p2_left_dt, False, p2_row["device_type"])
                )
     
            # Cache active room mapping
            active_rooms.append({
                "id": room_id,
                "creator": creator_id,
                "partner": partner_id,
                "participants": [creator_id, partner_id]
            })
            actions.append(f"ROOM CREATED: '{room_name}' ({room_code}) | Matched users {creator_id[:8]}... & {partner_id[:8]}...")
        else:
            print(f"[ERROR] Failed to create dual_rooms {room_id}", file=sys.stderr)
    if active_rooms:
        room = random.choice(active_rooms)
        room_id = room["id"]
        
        # Verify room exists in database before proceeding with child events
        existing_rooms = {r["id"] for r in db_helpers.ROOMS}.union({r["id"] for r in active_rooms})
        
        # 2. Action: Chat Message in Room (40% chance)
        if random.random() < 0.40:
            if room_id not in existing_rooms:
                print(f"[WARNING] Skipping message insertion: Parent room {room_id} does not exist in Supabase.", file=sys.stderr)
            else:
                msg_id = str(uuid.uuid4())
                sender_uuid = random.choice(room["participants"])
                receiver_uuid = room["partner"] if sender_uuid == room["creator"] else room["creator"]
                sender_id_bigint = to_bigint(sender_uuid)
                receiver_id_bigint = to_bigint(receiver_uuid)
                msg_text = random.choice(messages_pool)
                msg_type = random.choice(["text", "emoji", "image", "gif", "audio", "sticker"])
                edited = random.random() < 0.15
                created_dt = now_dt
                if edited:
                    edited_dt = created_dt + datetime.timedelta(minutes=random.randint(1, 60))
                else:
                    edited_dt = created_dt
                
                created_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")
                edited_str = edited_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                sender_col = db_helpers.DETECTED_COLUMNS.get("dual_messages_sender_column", "sender_user_id")
                message_row = {
                    "id": msg_id,
                    "room_id": room_id,
                    sender_col: sender_id_bigint,
                    "receiver_id": receiver_id_bigint,
                    "message": msg_text,
                    "message_type": msg_type,
                    "sent_at": created_str,
                    "edited": edited,
                    "edited_at": edited_str
                }
                append_to_csv(MESSAGES_CSV_PATH, [
                    "id", "room_id", sender_col, "receiver_id", "message", "message_type", "sent_at", "edited", "edited_at"
                ], [
                    message_row["id"], message_row["room_id"], message_row[sender_col], message_row["receiver_id"],
                    message_row["message"], message_row["message_type"], message_row["sent_at"], message_row["edited"], message_row["edited_at"]
                ])
                send_supabase_post("dual_messages", message_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        f"INSERT INTO app_dual.dual_messages (id, room_id, {sender_col}, receiver_id, message, message_type, sent_at, edited, edited_at) VALUES (%s,%s,%s,%s,%s,%s::app_dual.message_type_enum,%s,%s,%s)",
                        (msg_id, room_id, sender_id_bigint, receiver_id_bigint, msg_text, msg_type, created_dt, edited, edited_dt)
                    )
                actions.append(f"MESSAGE sent by {sender_uuid[:8]}... to {receiver_uuid[:8]}... inside Room {room_id[:8]}... ('{msg_text[:15]}')")
 
        # 3. Action: Call Activity (20% chance)
        if random.random() < 0.20:
            if room_id not in existing_rooms:
                print(f"[WARNING] Skipping call connection: Parent room {room_id} does not exist in Supabase.", file=sys.stderr)
            else:
                call_id = str(uuid.uuid4())
                call_type = random.choice(["audio", "video"])
                duration = random.randint(30, 7200)
                started_dt = now_dt
                ended_dt = started_dt + datetime.timedelta(seconds=duration)
                started_str = started_dt.strftime("%Y-%m-%d %H:%M:%S")
                ended_str = ended_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                caller_id = room["creator"]
                receiver_id = room["partner"]
                
                call_row = {
                    "id": call_id,
                    "room_id": room_id,
                    "call_type": call_type,
                    "started_at": started_str,
                    "ended_at": ended_str,
                    "call_status": "completed",
                    "duration_seconds": duration,
                    "caller_id": caller_id,
                    "receiver_id": receiver_id
                }
                append_to_csv(CALLS_CSV_PATH, [
                    "id", "room_id", "call_type", "started_at", "ended_at", "call_status", "duration_seconds", "caller_id", "receiver_id"
                ], [
                    call_row["id"], call_row["room_id"], call_row["call_type"], call_row["started_at"], call_row["ended_at"],
                    call_row["call_status"], call_row["duration_seconds"], call_row["caller_id"], call_row["receiver_id"]
                ])
                send_supabase_post("dual_calls", call_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_dual.dual_calls (id, room_id, call_type, started_at, ended_at, call_status, duration_seconds, caller_id, receiver_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (call_id, room_id, call_type, started_dt, ended_dt, "completed", duration, caller_id, receiver_id)
                    )
                actions.append(f"CALL COMPLETED inside Room {room_id[:8]}... | Caller: {caller_id[:8]}... | Receiver: {receiver_id[:8]}... | Duration: {duration}s")
 
        # 4. Action: Song Request (25% chance)
        if random.random() < 0.25:
            if room_id not in existing_rooms:
                print(f"[WARNING] Skipping song request: Parent room {room_id} does not exist in Supabase.", file=sys.stderr)
            else:
                req_id = str(uuid.uuid4())
                req_by = random.choice(room["participants"])
                song = random.choice(songs_pool)
                
                status_choices = ["pending", "approved", "playing", "completed", "rejected", "cancelled"]
                status_weights = [0.20, 0.20, 0.10, 0.35, 0.10, 0.05]
                status = random.choices(status_choices, weights=status_weights)[0]
                played_at = now_str if status == "completed" else None
                
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
        is_active = random.random() < 0.70
        
        match_row = {
            "id": match_id,
            "user_one": u1,
            "user_two": u2,
            "match_status": status,
            "created_at": now_str,
            "matched_on_interest": interest,
            "match_duration": duration,
            "is_active": is_active
        }
        append_to_csv(MATCHES_CSV_PATH, [
            "id", "user_one", "user_two", "match_status", "created_at", "matched_on_interest", "match_duration", "is_active"
        ], [
            match_row["id"], match_row["user_one"], match_row["user_two"], match_row["match_status"],
            match_row["created_at"], match_row["matched_on_interest"], match_row["match_duration"], match_row["is_active"]
        ])
        send_supabase_post("dual_matches", match_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_dual.dual_matches (id, user_one, user_two, match_status, created_at, matched_on_interest, match_duration, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (match_id, u1, u2, status, now_dt, interest, duration, is_active)
            )
        actions.append(f"NEW MATCH: {u1[:8]}... & {u2[:8]}... on '{interest}' (Status: {status}, Active: {is_active})")

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
    
    # Users are dynamically resolved from db_helpers.USERS in simulate_step()
    
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
            db_helpers.refresh_all_caches(tick)
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            actions = simulate_step()
            
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
