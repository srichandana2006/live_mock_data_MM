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

GROUPS_CSV_PATH = os.path.join(WORKSPACE_DIR, "groups_mock_data.csv")
MEMBERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_members_mock_data.csv")
MESSAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_messages_mock_data.csv")
EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "events_mock_data.csv")
ANNOUNCEMENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "announcements_mock_data.csv")

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

# Seed data pools
group_names = [
    "Lo-Fi Beats Study Hub", "Bollywood Retro Classics", "Techno & Trance Rave", 
    "Hip Hop Cypher Room", "Acoustic Indie Sessions", "Metalheads Corner", 
    "Sunday Jazz Brunch", "K-Pop Stans Gathering", "Telugu Folk Vibez", 
    "Late Night Coding Tracks", "Classical Symphony Hall"
]

group_descriptions = [
    "A cozy space to hang out, share tracks, and vibe together.",
    "Throwback playlist and real-time discussion about retro tracks.",
    "High energy beats, raves, and electronic dance music discussion.",
    "A community playlist of the dopest tracks in hip hop history.",
    "Chill acoustic vibes, indie singer-songwriters, and deep talks.",
    "Heavy riffs, double bass, and all things metal. Rock on!",
    "Smooth sax, swing music, and Sunday morning relaxation playlist.",
    "Discussing releases, sharing choreographies, and streaming favorite hits.",
    "Traditional, modern folk, and vernacular musical heritage.",
    "Focus music, synthewave, and lo-fi tracks to write code to.",
    "Masterpieces, orchestra discussions, and calm symphonies."
]

message_templates = [
    "Yo, check out this track I just found!",
    "Who is up for a listening party tonight?",
    "That transition was absolutely seamless.",
    "Rate this song out of 10! 🔥",
    "Welcome to the group room, everyone!",
    "Did anyone listen to the new album that dropped today?",
    "Vibing hard to this playlist right now.",
    "Can we queue some electronic tracks next?",
    "🙌 absolute masterpiece",
    "I'm scheduling an event for this weekend.",
    "Let's vote on the next genre highlight.",
    "Hey! Share your Spotify wrapped summaries here.",
    "This room is always so chill.",
    "Summoning all active listeners!"
]

announcement_titles = [
    "Listening Party Summons", "Weekly Album Spotlight", "New Moderator Welcome", 
    "Upcoming Live Stream", "Room Rule Updates", "Collaboration Queue Open"
]

announcement_contents = [
    "We are starting a live listening session in 5 minutes. Hop in!",
    "This week we are reviewing the newest album release. Details in the events section.",
    "Let's welcome our new moderator to the group! Keep it friendly.",
    "We have a special RJ guest coming to host a live broadcast tomorrow at 6 PM.",
    "Please remember to keep the queue collaborative and avoid double-queueing tracks.",
    "The playlist queue is now open to all members. Add your favorite tracks!"
]

# Track active rooms, members, and events to maintain state
active_groups = []  # dict: {id, creator_id, members: [user_id]}
active_events = []  # dict: {id, group_id, status}

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
        users = [str(uuid.uuid4()) for _ in range(100)]
    else:
        print(f"Loaded {len(users)} users for group simulation.")
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

def simulate_step(users):
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    actions = []

    # 1. Action: Create a Group (15% chance or if active groups is empty)
    if random.random() < 0.15 or len(active_groups) < 2:
        group_id = str(uuid.uuid4())
        creator_id = random.choice(users)
        
        name = random.choice(group_names) + f" #{random.randint(10, 99)}"
        desc = random.choice(group_descriptions)
        group_type = random.choice(["public", "private"])
        status = "active"
        
        # groups table payload
        group_row = {
            "id": group_id,
            "group_name": name,
            "description": desc,
            "group_type": group_type,
            "status": status,
            "created_by": creator_id,
            "created_at": now_str
        }
        
        append_to_csv(GROUPS_CSV_PATH, [
            "id", "group_name", "description", "group_type", "status", "created_by", "created_at"
        ], [
            group_row["id"], group_row["group_name"], group_row["description"], group_row["group_type"],
            group_row["status"], group_row["created_by"], group_row["created_at"]
        ])
        send_supabase_post("groups", group_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_group.groups (id, group_name, description, group_type, status, created_by, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (group_id, name, desc, group_type, status, creator_id, now_dt)
            )
            
        # Add creator as Admin member
        member_id = str(uuid.uuid4())
        member_row = {
            "id": member_id,
            "group_id": group_id,
            "user_id": creator_id,
            "role": "admin",
            "status": "active",
            "joined_at": now_str,
            "left_at": None,
            "time_spent": 0
        }
        append_to_csv(MEMBERS_CSV_PATH, [
            "id", "group_id", "user_id", "role", "status", "joined_at", "left_at", "time_spent"
        ], [
            member_row["id"], member_row["group_id"], member_row["user_id"], member_row["role"],
            member_row["status"], member_row["joined_at"], member_row["left_at"], member_row["time_spent"]
        ])
        send_supabase_post("group_members", member_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_group.group_members (id, group_id, user_id, role, status, joined_at, left_at, time_spent) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (member_id, group_id, creator_id, "admin", "active", now_dt, None, 0)
            )

        active_groups.append({
            "id": group_id,
            "creator": creator_id,
            "members": [creator_id]
        })
        actions.append(f"GROUP CREATED: '{name}' by {creator_id[:8]}...")

    # Ensure we have groups for other operations
    if active_groups:
        group = random.choice(active_groups)
        group_id = group["id"]

        # 2. Action: Add a Member to a Group (25% chance)
        if random.random() < 0.25:
            # Find a user who is not already in this group
            non_members = [u for u in users if u not in group["members"]]
            if non_members:
                user_id = random.choice(non_members)
                role = random.choices(["moderator", "member"], weights=[0.15, 0.85])[0]
                member_id = str(uuid.uuid4())
                
                member_row = {
                    "id": member_id,
                    "group_id": group_id,
                    "user_id": user_id,
                    "role": role,
                    "status": "active",
                    "joined_at": now_str,
                    "left_at": None,
                    "time_spent": random.randint(0, 120)
                }
                
                append_to_csv(MEMBERS_CSV_PATH, [
                    "id", "group_id", "user_id", "role", "status", "joined_at", "left_at", "time_spent"
                ], [
                    member_row["id"], member_row["group_id"], member_row["user_id"], member_row["role"],
                    member_row["status"], member_row["joined_at"], member_row["left_at"], member_row["time_spent"]
                ])
                send_supabase_post("group_members", member_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_group.group_members (id, group_id, user_id, role, status, joined_at, left_at, time_spent) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (member_id, group_id, user_id, role, "active", now_dt, None, member_row["time_spent"])
                    )
                
                group["members"].append(user_id)
                actions.append(f"MEMBER ADDED: User {user_id[:8]}... joined group {group_id[:8]}... as '{role}'")

        # 3. Action: Send Group Chat Message (40% chance)
        if random.random() < 0.40 and group["members"]:
            sender_id = random.choice(group["members"])
            msg_text = random.choice(message_templates)
            msg_id = str(uuid.uuid4())
            read_count = random.randint(1, len(group["members"]))
            
            message_row = {
                "id": msg_id,
                "group_id": group_id,
                "user_id": sender_id,
                "message": msg_text,
                "read_count": read_count,
                "sent_at": now_str
            }
            
            append_to_csv(MESSAGES_CSV_PATH, [
                "id", "group_id", "user_id", "message", "read_count", "sent_at"
            ], [
                message_row["id"], message_row["group_id"], message_row["user_id"], message_row["message"],
                message_row["read_count"], message_row["sent_at"]
            ])
            send_supabase_post("group_messages", message_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_group.group_messages (id, group_id, user_id, message, read_count, sent_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (msg_id, group_id, sender_id, msg_text, read_count, now_dt)
                )
            actions.append(f"MESSAGE inside group {group_id[:8]}... by {sender_id[:8]}... ('{msg_text[:15]}')")

        # 4. Action: Create/Update Event (15% chance)
        if active_events and random.random() < 0.30:
            # Complete or cancel an existing event
            ended_event = active_events.pop(0)
            status = random.choice(["completed", "cancelled"])
            
            # Postgres updates existing event; REST API simulates final state creation
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_group.group_events SET event_status = %s WHERE id = %s",
                    (status, ended_event["id"])
                )
            actions.append(f"EVENT Concluded: Event {ended_event['id'][:8]}... marked as '{status}'")
        elif random.random() < 0.15:
            event_id = str(uuid.uuid4())
            creator_id = random.choice(group["members"])
            
            event_date_dt = now_dt + datetime.timedelta(days=random.randint(0, 5))
            start_time_dt = event_date_dt + datetime.timedelta(hours=random.randint(1, 4))
            end_time_dt = event_date_dt + datetime.timedelta(hours=random.randint(5, 8))

            e_date = event_date_dt.strftime("%Y-%m-%d")
            s_time = start_time_dt.strftime("%Y-%m-%d %H:%M:%S")
            e_time = end_time_dt.strftime("%Y-%m-%d %H:%M:%S")
            status = "scheduled"
            attendees = random.randint(1, len(group["members"]) + 5)
            
            event_row = {
                "id": event_id,
                "group_id": group_id,
                "event_date": e_date,
                "start_time": s_time,
                "end_time": e_time,
                "event_status": status,
                "attendees_count": attendees,
                "created_by": creator_id
            }
            
            append_to_csv(EVENTS_CSV_PATH, [
                "id", "group_id", "event_date", "start_time", "end_time", "event_status", "attendees_count", "created_by"
            ], [
                event_row["id"], event_row["group_id"], event_row["event_date"], event_row["start_time"],
                event_row["end_time"], event_row["event_status"], event_row["attendees_count"], event_row["created_by"]
            ])
            send_supabase_post("group_events", event_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_group.group_events (id, group_id, event_date, start_time, end_time, event_status, attendees_count, created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (event_id, group_id, e_date, start_time_dt, end_time_dt, status, attendees, creator_id)
                )
            
            active_events.append({
                "id": event_id,
                "group_id": group_id,
                "status": status
            })
            actions.append(f"EVENT SCHEDULED: Event in group {group_id[:8]}... on {e_date} starting at {s_time}")

        # 5. Action: Create Announcements / Summons (20% chance)
        if random.random() < 0.20:
            ann_id = str(uuid.uuid4())
            creator_id = random.choice(group["members"])
            ann_type = random.choice(["summon", "broadcast", "event"])
            title = random.choice(ann_titles_if_needed(ann_type))
            content = random.choice(ann_contents_if_needed(ann_type))
            
            targets = None
            targets_csv = ""
            if ann_type == "summon":
                # Select random target users from pool
                target_count = min(3, len(users) - 1)
                selected_targets = random.sample([u for u in users if u != creator_id], target_count)
                targets = selected_targets
                targets_csv = "{" + ",".join(selected_targets) + "}" # Postgres array format
                
            ann_row = {
                "id": ann_id,
                "group_id": group_id,
                "created_by": creator_id,
                "target_user_ids": targets,
                "announcement_type": ann_type,
                "title": title,
                "content": content,
                "created_at": now_str
            }
            
            append_to_csv(ANNOUNCEMENTS_CSV_PATH, [
                "id", "group_id", "created_by", "target_user_ids", "announcement_type", "title", "content", "created_at"
            ], [
                ann_row["id"], ann_row["group_id"], ann_row["created_by"], targets_csv, ann_row["announcement_type"],
                ann_row["title"], ann_row["content"], ann_row["created_at"]
            ])
            send_supabase_post("announcements", ann_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_group.announcements (id, group_id, created_by, target_user_ids, announcement_type, title, content, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (ann_id, group_id, creator_id, targets, ann_type, title, content, now_dt)
                )
            actions.append(f"ANNOUNCEMENT: '{title}' ({ann_type}) broadcasted in group {group_id[:8]}...")

    # Bounded group lists
    if len(active_groups) > 10:
        active_groups.pop(0)

    return actions

def ann_titles_if_needed(atype):
    if atype == "summon":
        return ["Action Required: Attendance Summons", "URGENT: Jump in Now", "Vibe Room Summon Request"]
    return announcement_titles

def ann_contents_if_needed(atype):
    if atype == "summon":
        return ["You are being summoned to participate in the collaborative room session.", "Your presence is requested immediately for voting.", "Come listen and queue track favorites with the group."]
    return announcement_contents

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
    print("        MELODYMEET GROUPS MODULE LIVE DATA SIMULATOR")
    print("=" * 60)
    
    users = load_user_pool()
    
    if DATABASE_URL:
        if HAS_PG:
            print("[INFO] PostgreSQL connection detected.")
        else:
            print("[WARNING] DATABASE_URL detected, but 'psycopg2' not installed. Defaulting to local CSV & Supabase REST API.")
            
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API target active.")
        
    print("[INFO] CSV Mode: Enabled (Appends to group_*_mock_data.csv files)")
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
                
            time.sleep(TICK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
        print(f"Total simulated steps: {tick}")

if __name__ == "__main__":
    main()
