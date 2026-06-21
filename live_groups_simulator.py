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

GROUPS_CSV_PATH = os.path.join(WORKSPACE_DIR, "groups_mock_data.csv")
MEMBERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_members_mock_data.csv")
MESSAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_messages_mock_data.csv")
EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "events_mock_data.csv")
ANNOUNCEMENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "announcements_mock_data.csv")
ROOMS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rooms_mock_data.csv")

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

def disable_rls_if_possible():
    if not DATABASE_URL or not HAS_PG:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            tables = [
                "app_group.groups",
                "app_group.group_members",
                "app_group.group_messages",
                "app_group.group_events",
                "app_group.announcements",
                "app_group.group_playlist_tracks"
            ]
            for table in tables:
                try:
                    cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
                except Exception:
                    pass
        conn.close()
    except Exception:
        pass

# Fallback credentials if not in env
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_ODOA-yehp7PShmNy1J5YhA_gtP2EiMD"

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

def load_group_pool():
    """Load existing groups from Supabase or CSV to maintain proper referential integrity"""
    groups = []
    if SUPABASE_URL and SUPABASE_KEY:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/groups?select=id,created_by"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept-Profile": "app_group"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                for g in data:
                    groups.append({
                        "id": g["id"],
                        "creator": g.get("created_by") or str(uuid.uuid4()),
                        "members": [g.get("created_by")] if g.get("created_by") else [],
                        "rooms": []
                    })
                if groups:
                    print(f"Successfully loaded {len(groups)} groups from Supabase API.")
                    return groups
        except Exception as e:
            print(f"Warning: Could not fetch groups from Supabase: {e}", file=sys.stderr)

    if os.path.exists(GROUPS_CSV_PATH):
        try:
            with open(GROUPS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("id"):
                        creator = row.get("created_by") or str(uuid.uuid4())
                        groups.append({
                            "id": row["id"],
                            "creator": creator,
                            "members": [creator],
                            "rooms": []
                        })
                if groups:
                    print(f"Successfully loaded {len(groups)} groups from CSV.")
                    return groups
        except Exception as e:
            print(f"Warning: Could not parse groups CSV: {e}", file=sys.stderr)
            
    return groups

def load_group_rooms():
    """Load existing rooms and map them to their group_id"""
    group_rooms = {}
    if SUPABASE_URL and SUPABASE_KEY:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/rooms?select=id,group_id"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept-Profile": "app_group"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                for r in data:
                    gid = r.get("group_id")
                    rid = r.get("id")
                    if gid and rid:
                        if gid not in group_rooms:
                            group_rooms[gid] = []
                        group_rooms[gid].append(rid)
                if group_rooms:
                    print(f"Loaded {sum(len(v) for v in group_rooms.values())} rooms from Supabase API.")
                    return group_rooms
        except Exception as e:
            print(f"Warning: Could not fetch rooms from Supabase: {e}", file=sys.stderr)

    ROOMS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rooms_mock_data.csv")
    if os.path.exists(ROOMS_CSV_PATH):
        try:
            with open(ROOMS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    gid = r.get("group_id")
                    rid = r.get("id")
                    if gid and rid:
                        if gid not in group_rooms:
                            group_rooms[gid] = []
                        group_rooms[gid].append(rid)
        except Exception as e:
            print(f"Warning: Could not parse rooms CSV: {e}", file=sys.stderr)
            
    return group_rooms


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
        return True
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

def simulate_step():
    users = [u["id"] for u in db_helpers.USERS]
    if not users:
        print("[WARNING] Skipping simulation step: No active users in Supabase cache.", file=sys.stderr)
        return []
        
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
        
        # Only proceed to create child records if parent group creation succeeded
        group_insert_success = send_supabase_post("groups", group_row)
        if group_insert_success:
            append_to_csv(GROUPS_CSV_PATH, [
                "id", "group_name", "description", "group_type", "status", "created_by", "created_at"
            ], [
                group_row["id"], group_row["group_name"], group_row["description"], group_row["group_type"],
                group_row["status"], group_row["created_by"], group_row["created_at"]
            ])
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_group.groups (id, group_name, description, group_type, status, created_by, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (group_id, name, desc, group_type, status, creator_id, now_dt)
                )
                
            # Precompute left_at for the creator group member (never NULL)
            duration_days = random.randint(1, 30)
            left_dt = now_dt + datetime.timedelta(days=duration_days, hours=random.randint(0, 23))
            left_str = left_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Add creator as Admin member
            member_id = str(uuid.uuid4())
            member_row = {
                "id": member_id,
                "group_id": group_id,
                "user_id": creator_id,
                "role": "admin",
                "status": "active",
                "joined_at": now_str,
                "left_at": left_str,
                "time_spent": 0
            }
            member_success = send_supabase_post("group_members", member_row)
            if member_success:
                append_to_csv(MEMBERS_CSV_PATH, [
                    "id", "group_id", "user_id", "role", "status", "joined_at", "left_at", "time_spent"
                ], [
                    member_row["id"], member_row["group_id"], member_row["user_id"], member_row["role"],
                    member_row["status"], member_row["joined_at"], member_row["left_at"], member_row["time_spent"]
                ])
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_group.group_members (id, group_id, user_id, role, status, joined_at, left_at, time_spent) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (member_id, group_id, creator_id, "admin", "active", now_dt, left_dt, 0)
                    )

            # Create 1-5 rooms for this group
            room_names_pool = ["Chill Zone", "Music Lovers Hub", "Podcast Lounge", "Late Night Vibes", "Private Jam Room", "Community Room", "Gaming Corner"]
            num_rooms = random.randint(1, 5)
            group_rooms = []
            for _ in range(num_rooms):
                room_id = str(uuid.uuid4())
                room_name = random.choice(room_names_pool) + f" #{random.randint(10, 99)}"
                room_type = random.choice(["public", "private", "friends"])
                room_status = random.choice(["active", "closed"])
                room_member_count = random.randint(1, 10)
                
                room_row = {
                    "id": room_id,
                    "group_id": group_id,
                    "name": room_name,
                    "room_type": room_type,
                    "status": room_status,
                    "created_by": creator_id,
                    "created_at": now_str,
                    "member_count": room_member_count
                }
                
                append_to_csv(ROOMS_CSV_PATH, [
                    "id", "group_id", "name", "room_type", "status", "created_by", "created_at", "member_count"
                ], [
                    room_row["id"], room_row["group_id"], room_row["name"], room_row["room_type"],
                    room_row["status"], room_row["created_by"], room_row["created_at"], room_row["member_count"]
                ])
                send_supabase_post("rooms", room_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_group.rooms (id, group_id, name, room_type, status, created_by, created_at, member_count) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (room_id, group_id, room_name, room_type, room_status, creator_id, now_dt, room_member_count)
                    )
                group_rooms.append(room_id)

            active_groups.append({
                "id": group_id,
                "creator": creator_id,
                "members": [creator_id],
                "rooms": group_rooms
            })
            actions.append(f"GROUP CREATED: '{name}' by {creator_id[:8]}... with {num_rooms} rooms")
        else:
            actions.append(f"GROUP CREATION SKIPPED (Supabase insert failed for '{name}')")

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
                
                # Precompute left_at (never NULL)
                duration_days = random.randint(1, 30)
                left_dt = now_dt + datetime.timedelta(days=duration_days, hours=random.randint(0, 23))
                left_str = left_dt.strftime("%Y-%m-%d %H:%M:%S")

                member_row = {
                    "id": member_id,
                    "group_id": group_id,
                    "user_id": user_id,
                    "role": role,
                    "status": "active",
                    "joined_at": now_str,
                    "left_at": left_str,
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
                        (member_id, group_id, user_id, role, "active", now_dt, left_dt, member_row["time_spent"])
                    )
                
                group["members"].append(user_id)
                actions.append(f"MEMBER ADDED: User {user_id[:8]}... joined group {group_id[:8]}... as '{role}'")

        # 3. Action: Send Group Chat Message (40% chance)
        if random.random() < 0.40 and group["members"] and group.get("rooms"):
            sender_id = random.choice(group["members"])
            msg_text = random.choice(message_templates)
            msg_id = str(uuid.uuid4())
            read_count = random.randint(1, len(group["members"]))
            room_id = random.choice(group["rooms"])
            
            group_col = db_helpers.DETECTED_COLUMNS.get("group_messages_group_column", "group_id")
            message_row = {
                "id": msg_id,
                "user_id": sender_id,
                "message": msg_text,
                "read_count": read_count,
                "sent_at": now_str
            }
            if group_col == "room_id":
                message_row["room_id"] = room_id
            else:
                message_row["group_id"] = room_id
            
            append_to_csv(MESSAGES_CSV_PATH, [
                "id", group_col, "user_id", "message", "read_count", "sent_at"
            ], [
                message_row["id"], message_row[group_col], message_row["user_id"], message_row["message"],
                message_row["read_count"], message_row["sent_at"]
            ])
            send_supabase_post("group_messages", message_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    f"INSERT INTO app_group.group_messages (id, {group_col}, user_id, message, read_count, sent_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (msg_id, room_id, sender_id, msg_text, read_count, now_dt)
                )
            actions.append(f"MESSAGE inside group {group_id[:8]}... room {room_id[:8]}... by {sender_id[:8]}... ('{msg_text[:15]}')")

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
            
            event_names = ["Weekend Music Jam", "Karaoke Night", "Friday Chill Session", "Open Mic Evening", "Community Meetup", "DJ Night", "Podcast Discussion", "Late Night Vibes", "Music Battle", "Gaming Hangout"]
            e_name = random.choice(event_names)

            event_row = {
                "id": event_id,
                "group_id": group_id,
                "event_name": e_name,
                "event_date": e_date,
                "start_time": s_time,
                "end_time": e_time,
                "event_status": status,
                "attendees_count": attendees,
                "created_by": creator_id
            }
            
            append_to_csv(EVENTS_CSV_PATH, [
                "id", "group_id", "event_name", "event_date", "start_time", "end_time", "event_status", "attendees_count", "created_by"
            ], [
                event_row["id"], event_row["group_id"], event_row["event_name"], event_row["event_date"], event_row["start_time"],
                event_row["end_time"], event_row["event_status"], event_row["attendees_count"], event_row["created_by"]
            ])
            send_supabase_post("group_events", event_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_group.group_events (id, group_id, event_name, event_date, start_time, end_time, event_status, attendees_count, created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (event_id, group_id, e_name, e_date, start_time_dt, end_time_dt, status, attendees, creator_id)
                )
            
            active_events.append({
                "id": event_id,
                "group_id": group_id,
                "status": status
            })
            actions.append(f"EVENT SCHEDULED: Event '{e_name}' in group {group_id[:8]}... on {e_date}")

        # 5. Action: Create Announcements / Summons (20% chance)
        if random.random() < 0.20:
            if not group.get("rooms"):
                # Skip
                pass
            else:
                ann_id = str(uuid.uuid4())
                creator_id = random.choice(group["members"])
                ann_type = random.choice(["summon", "broadcast", "event"])
                title = random.choice(ann_titles_if_needed(ann_type))
                content = random.choice(ann_contents_if_needed(ann_type))
                room_id = random.choice(group["rooms"])
                
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
                    "created_at": now_str,
                    "room_id": room_id
                }
                
                append_to_csv(ANNOUNCEMENTS_CSV_PATH, [
                    "id", "group_id", "created_by", "target_user_ids", "announcement_type", "title", "content", "created_at", "room_id"
                ], [
                    ann_row["id"], ann_row["group_id"], ann_row["created_by"], targets_csv, ann_row["announcement_type"],
                    ann_row["title"], ann_row["content"], ann_row["created_at"], ann_row["room_id"]
                ])
                send_supabase_post("announcements", ann_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_group.announcements (id, group_id, created_by, target_user_ids, announcement_type, title, content, created_at, room_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (ann_id, group_id, creator_id, targets, ann_type, title, content, now_dt, room_id)
                    )
                actions.append(f"ANNOUNCEMENT: '{title}' ({ann_type}) broadcasted in group {group_id[:8]}... room {room_id[:8]}...")

    # 6. Action: Generate a room (100% chance, every tick / 5 seconds)
    if active_groups:
        group = random.choice(active_groups)
        group_id = group["id"]
        creator_id = group.get("creator") or random.choice(users)
        
        room_id = str(uuid.uuid4())
        room_names_pool = ["Chill Zone", "Music Lovers Hub", "Podcast Lounge", "Late Night Vibes", "Private Jam Room", "Community Room", "Gaming Corner"]
        room_name = random.choice(room_names_pool) + f" #{random.randint(10, 99)}"
        # Strictly handles 'public', 'private', or 'friends'
        room_type = random.choice(["public", "private", "friends"])
        room_status = random.choice(["active", "closed"])
        room_member_count = random.randint(1, 10)
        
        room_row = {
            "id": room_id,
            "group_id": group_id,
            "name": room_name,
            "room_type": room_type,
            "status": room_status,
            "created_by": creator_id,
            "created_at": now_str,
            "member_count": room_member_count
        }
        
        append_to_csv(ROOMS_CSV_PATH, [
            "id", "group_id", "name", "room_type", "status", "created_by", "created_at", "member_count"
        ], [
            room_row["id"], room_row["group_id"], room_row["name"], room_row["room_type"],
            room_row["status"], room_row["created_by"], room_row["created_at"], room_row["member_count"]
        ])
        
        send_supabase_post("rooms", room_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_group.rooms (id, group_id, name, room_type, status, created_by, created_at, member_count) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (room_id, group_id, room_name, room_type, room_status, creator_id, now_dt, room_member_count)
            )
            
        if "rooms" not in group:
            group["rooms"] = []
        group["rooms"].append(room_id)
        actions.append(f"ROOM GENERATED (5s periodic): '{room_name}' ({room_type}) in group {group_id[:8]}... status: {room_status}")

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
    
    # Disable RLS on startup if direct database connection is active
    disable_rls_if_possible()
    
    # Users are dynamically resolved from db_helpers.USERS in simulate_step()
    global active_groups
    active_groups = load_group_pool()
    group_rooms = load_group_rooms()
    for g in active_groups:
        g["rooms"] = group_rooms.get(g["id"], [])
    
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
                
            time.sleep(TICK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
        print(f"Total simulated steps: {tick}")

if __name__ == "__main__":
    main()
