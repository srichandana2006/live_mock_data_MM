import os
import sys
import time
import uuid
import random
import datetime
import csv
import urllib.request
import json

# Define paths
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.path.dirname(os.path.abspath(__file__)))
USERS_CSV = os.path.join(WORKSPACE_DIR, "users_mock_data.csv")
DEVICES_CSV = os.path.join(WORKSPACE_DIR, "devices_mock_data.csv")
INSTALLS_CSV = os.path.join(WORKSPACE_DIR, "app_installations_mock_data.csv")
UNINSTALLS_CSV = os.path.join(WORKSPACE_DIR, "app_uninstallations_mock_data.csv")
LOGINS_CSV = os.path.join(WORKSPACE_DIR, "login_history_mock_data.csv")
USAGE_CSV = os.path.join(WORKSPACE_DIR, "module_usage_mock_data.csv")
OTP_CSV = os.path.join(WORKSPACE_DIR, "otp_verification_mock_data.csv")
PERMISSIONS_CSV = os.path.join(WORKSPACE_DIR, "permissions_mock_data.csv")
ROLES_CSV = os.path.join(WORKSPACE_DIR, "user_roles_mock_data.csv")
ROLE_PERM_CSV = os.path.join(WORKSPACE_DIR, "role_permission_mock_data.csv")
ROLE_MAP_CSV = os.path.join(WORKSPACE_DIR, "user_role_mapping_mock_data.csv")
SESSIONS_CSV = os.path.join(WORKSPACE_DIR, "user_sessions_mock_data.csv")
ACTIVITY_CSV = os.path.join(WORKSPACE_DIR, "user_activity_log_mock_data.csv")
PRESENCE_CSV = os.path.join(WORKSPACE_DIR, "user_presence_mock_data.csv")

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

# Configuration
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

def to_bigint(uuid_str):
    if not uuid_str:
        return None
    try:
        return uuid.UUID(uuid_str).int & 0x7FFFFFFFFFFFFFFF
    except (ValueError, TypeError):
        return random.randint(1, 9223372036854775807)

# Sample Data Pools
first_names = ["Arjun", "Aditya", "Tharun", "Srinivas", "Neha", "Priya", "Rahul", "Anjali", "Vikram", "Sneha", "Karan", "Rohan", "Pooja", "Divya", "Sandeep", "Vijay", "Aisha", "Kabir", "Meera", "Sameer"]
last_names = ["Sharma", "Verma", "Reddy", "Rao", "Patel", "Kumar", "Singh", "Joshi", "Nair", "Choudhury", "Gupta", "Mehta", "Iyer", "Rao", "Naidu", "Sen", "Das", "Roy", "Bose", "Chatterjee"]
genders = ["Male", "Female", "Non-Binary"]

device_catalog = {
    "Mobile": [
        ("iPhone 14", "iOS"), ("iPhone 15", "iOS"), ("Samsung Galaxy S23", "Android"),
        ("Google Pixel 8", "Android"), ("OnePlus 11", "Android"), ("Xiaomi 13", "Android")
    ],
    "Tablet": [
        ("iPad Pro", "iOS"), ("iPad Air", "iOS"), ("Samsung Galaxy Tab S9", "Android")
    ],
    "Desktop": [
        ("MacBook Pro", "macOS"), ("iMac", "macOS"), ("Windows PC", "Windows"),
        ("Dell XPS 15", "Windows"), ("Linux Workstation", "Linux")
    ]
}

app_versions = ["v2.4.1", "v2.5.0", "v2.5.1", "v2.6.0"]
login_methods = ["Password", "OTP", "Google Login", "Apple Sign-In"]
uninstall_reasons = [
    "App crashing on startup", "Switching to web app", "No longer using this service",
    "Freeing up device space", "Cleaning old apps", "Too many notifications"
]

# Static Roles and Permissions configuration mapping
ROLES = {
    "Admin": {
        "id": "11111111-1111-1111-1111-111111111111",
        "desc": "Full administrative access to all system settings and user management."
    },
    "Moderator": {
        "id": "22222222-2222-2222-2222-222222222222",
        "desc": "Moderate public vibe rooms, messages, and enforce community guidelines."
    },
    "User": {
        "id": "33333333-3333-3333-3333-333333333333",
        "desc": "Standard user access to create rooms, listen to music, and chat."
    }
}

PERMISSIONS = {
    "access_admin_panel": ("44444444-4444-4444-4444-444444444444", "AdminPanel"),
    "moderate_messages": ("55555555-5555-5555-5555-555555555555", "Moderation"),
    "create_room": ("66666666-6666-6666-6666-666666666666", "RoomManager"),
    "queue_track": ("77777777-7777-7777-7777-777777777777", "Playlist"),
    "send_message": ("88888888-8888-8888-8888-888888888888", "Chat")
}

ROLE_PERMISSIONS_MAPPING = {
    "Admin": ["access_admin_panel", "moderate_messages", "create_room", "queue_track", "send_message"],
    "Moderator": ["moderate_messages", "create_room", "queue_track", "send_message"],
    "User": ["create_room", "queue_track", "send_message"]
}

# Helper to generate random IP
def generate_ip():
    return f"{random.randint(24, 220)}.{random.randint(10, 254)}.{random.randint(0, 254)}.{random.randint(1, 254)}"

# File Appender
def append_row_to_csv(filepath, headers, row):
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)

# REST API POST dispatcher (configured for app_auth schema)
def send_supabase_post(table_name, payload):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": "app_auth",
        "Content-Profile": "app_auth"
    }
    body = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except urllib.error.HTTPError as e:
        # Gracefully handle 409 conflicts for configuration seeding
        if e.code == 409 and table_name in ("user_roles", "permissions", "role_permissions"):
            return True
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = "(could not read body)"
        print(f"[Supabase API Error] POST {table_name} failed: HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[Supabase API Error] POST {table_name} failed: {e}", file=sys.stderr)
        return False

# Direct Postgres DB Executor
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

# Fetch existing users directly from database if available (Referential Integrity)
def fetch_users_from_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/users?select=id,user_name"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": "app_auth"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"[Supabase API] Discovered {len(data)} existing user profiles in app_auth schema.")
            return [{"id": u["id"], "user_name": u["user_name"]} for u in data]
    except Exception as e:
        print(f"Warning: Could not fetch active users from Supabase API: {e}. Starting fresh.")
        return []

# Fetch existing devices directly from database if available (Referential Integrity)
def fetch_devices_from_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {}
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/devices?select=device_id,user_id"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": "app_auth"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            user_devices = {}
            for d in data:
                uid = d.get("user_id")
                did = d.get("device_id")
                if uid and did:
                    if uid not in user_devices:
                        user_devices[uid] = []
                    user_devices[uid].append(did)
            print(f"[Supabase API] Discovered {len(data)} existing devices in app_auth schema.")
            return user_devices
    except Exception as e:
        print(f"Warning: Could not fetch active devices from Supabase API: {e}.")
        return {}


# Config Seeding Function
def seed_static_tables():
    print("Seeding roles and permissions configuration tables...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Seed Roles
    for role_name, info in ROLES.items():
        role_row = {
            "role_id": info["id"],
            "role_name": role_name,
            "created_at": now_str,
            "description": info["desc"]
        }
        append_row_to_csv(ROLES_CSV, ["role_id", "role_name", "created_at", "description"], [
            role_row["role_id"], role_row["role_name"], role_row["created_at"], role_row["description"]
        ])
        send_supabase_post("user_roles", role_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_auth.user_roles (role_id, role_name, created_at, description) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (role_row["role_id"], role_row["role_name"], role_row["created_at"], role_row["description"])
            )
            
    # 2. Seed Permissions
    for perm_name, (perm_id, mod_name) in PERMISSIONS.items():
        perm_row = {
            "permission_id": perm_id,
            "permission_name": perm_name,
            "module_name": mod_name,
            "created_at": now_str
        }
        append_row_to_csv(PERMISSIONS_CSV, ["permission_id", "permission_name", "module_name", "created_at"], [
            perm_row["permission_id"], perm_row["permission_name"], perm_row["module_name"], perm_row["created_at"]
        ])
        send_supabase_post("permissions", perm_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_auth.permissions (permission_id, permission_name, module_name, created_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (perm_row["permission_id"], perm_row["permission_name"], perm_row["module_name"], perm_row["created_at"])
            )
            
    # 3. Seed Role-Permissions Map
    for role_name, perm_list in ROLE_PERMISSIONS_MAPPING.items():
        role_id = ROLES[role_name]["id"]
        for perm_name in perm_list:
            perm_id = PERMISSIONS[perm_name][0]
            # Deterministic mapping UUID
            mapping_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{role_name}-{perm_name}"))
            
            map_row = {
                "id": mapping_id,
                "role_id": role_id,
                "permission_id": perm_id,
                "assigned_at": now_str
            }
            append_row_to_csv(ROLE_PERM_CSV, ["id", "role_id", "permission_id", "assigned_at"], [
                map_row["id"], map_row["role_id"], map_row["permission_id"], map_row["assigned_at"]
            ])
            send_supabase_post("role_permissions", map_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_auth.role_permissions (id, role_id, permission_id, assigned_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (map_row["id"], map_row["role_id"], map_row["permission_id"], map_row["assigned_at"])
                )
    print("[INFO] Static configurations tables checked/seeded.")

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
    print("         MELODYMEET REAL-TIME AUTHENTICATION SIMULATOR")
    print("=" * 60)
    
    # Pre-seed configuration metadata tables
    seed_static_tables()


    # Load users pool
    active_users = fetch_users_from_supabase()
    user_devices = fetch_devices_from_supabase()  # user_id -> list of device IDs

    # Detect DB Targets
    if DATABASE_URL and HAS_PG:
        print("[INFO] PostgreSQL connection detected in environment.")
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API credentials detected in environment.")
    
    print("[INFO] CSV Mode: Enabled (Appends to users, devices, installs, uninstalls, logins, usage, otps)")
    print("-" * 60)
    print("Authentication Simulator started. Press Ctrl+C to stop.\n")

    # Seed initial users if database is empty
    if not active_users:
        print("Creating an initial active user and device pool (50 users)...")
        for _ in range(50):
            uid = str(uuid.uuid4())
            uname = f"{random.choice(first_names)} {random.choice(last_names)}"
            gender = random.choice(genders)
            email = f"{uname.lower().replace(' ', '')}{random.randint(10,99)}@example.com"
            
            user_row = {
                "id": uid,
                "uid": f"auth0|{random.randint(100000, 999999)}",
                "user_name": uname,
                "gender": gender,
                "email": email
            }
            append_row_to_csv(USERS_CSV, ["id", "uid", "user_name", "gender", "email"], [
                user_row["id"], user_row["uid"], user_row["user_name"], user_row["gender"], user_row["email"]
            ])
            send_supabase_post("users", user_row)
            
            dtype = random.choices(["Mobile", "Tablet", "Desktop"], weights=[0.70, 0.10, 0.20], k=1)[0]
            dname, os_name = random.choice(device_catalog[dtype])
            did = str(uuid.uuid4())
            app_ver = random.choice(app_versions)
            now_dt = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 10))
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            device_row = {
                "device_id": did,
                "user_id": uid,
                "device_name": dname,
                "device_type": dtype,
                "os_name": os_name,
                "app_version": app_ver,
                "registered_at": now_str,
                "first_seen": now_str,
                "last_seen": now_str
            }
            append_row_to_csv(DEVICES_CSV, ["device_id", "user_id", "device_name", "device_type", "os_name", "app_version", "registered_at", "first_seen", "last_seen"], [
                device_row["device_id"], device_row["user_id"], device_row["device_name"], device_row["device_type"], device_row["os_name"], device_row["app_version"], device_row["registered_at"], device_row["first_seen"], device_row["last_seen"]
            ])
            send_supabase_post("devices", device_row)
            
            inst_row = {
                "installation_id": str(uuid.uuid4()),
                "user_id": uid,
                "device_id": did,
                "installed_at": now_str,
                "app_version": app_ver
            }
            append_row_to_csv(INSTALLS_CSV, ["installation_id", "user_id", "device_id", "installed_at", "app_version"], [
                inst_row["installation_id"], inst_row["user_id"], inst_row["device_id"], inst_row["installed_at"], inst_row["app_version"]
            ])
            send_supabase_post("app_installations", inst_row)
            
            # Role mapping
            mapping_row = {
                "mapping_id": str(uuid.uuid4()),
                "user_id": uid,
                "role_id": ROLES["User"]["id"],
                "assigned_at": now_str
            }
            append_row_to_csv(ROLE_MAP_CSV, ["mapping_id", "user_id", "role_id", "assigned_at"], [
                mapping_row["mapping_id"], mapping_row["user_id"], mapping_row["role_id"], mapping_row["assigned_at"]
            ])
            send_supabase_post("user_role_mapping", mapping_row)
            
            # Activity Log
            act_row = {
                "activity_id": str(uuid.uuid4()),
                "user_id": uid,
                "activity_type": "signup",
                "source_module": "Auth",
                "activity_time": now_str,
                "device_id": to_bigint(did)
            }
            append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
            ])
            send_supabase_post("user_activity_log", act_row)
            
            # Presence
            pres_row = {
                "presence_id": uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF,
                "user_id": uid,
                "status": "Online",
                "current_module": "Auth",
                "last_seen": now_str
            }
            append_row_to_csv(PRESENCE_CSV, ["presence_id", "user_id", "status", "current_module", "last_seen"], [
                pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"]
            ])
            send_supabase_post("user_presence", pres_row)
            
            active_users.append({"id": uid, "user_name": uname})
            user_devices[uid] = [did]
        print("Initial pool created successfully.")

    tick = 0
    try:
        while True:
            tick += 1
            now_dt = datetime.datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            actions = []
            
            # --- 1. ACTION: NEW USER SIGNUP (10% chance) ---
            if random.random() < 0.10:
                uid = str(uuid.uuid4())
                uname = f"{random.choice(first_names)} {random.choice(last_names)}"
                gender = random.choice(genders)
                email = f"{uname.lower().replace(' ', '')}{random.randint(10,99)}@example.com"
                
                user_row = {
                    "id": uid,
                    "uid": f"auth0|{random.randint(100000, 999999)}",
                    "user_name": uname,
                    "gender": gender,
                    "email": email
                }
                append_row_to_csv(USERS_CSV, ["id", "uid", "user_name", "gender", "email"], [
                    user_row["id"], user_row["uid"], user_row["user_name"], user_row["gender"], user_row["email"]
                ])
                send_supabase_post("users", user_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.users (id, uid, user_name, gender, email) VALUES (%s,%s,%s,%s,%s)",
                        (user_row["id"], user_row["uid"], user_row["user_name"], user_row["gender"], user_row["email"])
                    )
                
                dtype = random.choices(["Mobile", "Tablet", "Desktop"], weights=[0.70, 0.10, 0.20], k=1)[0]
                dname, os_name = random.choice(device_catalog[dtype])
                did = str(uuid.uuid4())
                app_ver = random.choice(app_versions)
                
                device_row = {
                    "device_id": did,
                    "user_id": uid,
                    "device_name": dname,
                    "device_type": dtype,
                    "os_name": os_name,
                    "app_version": app_ver,
                    "registered_at": now_str,
                    "first_seen": now_str,
                    "last_seen": now_str
                }
                append_row_to_csv(DEVICES_CSV, ["device_id", "user_id", "device_name", "device_type", "os_name", "app_version", "registered_at", "first_seen", "last_seen"], [
                    device_row["device_id"], device_row["user_id"], device_row["device_name"], device_row["device_type"], device_row["os_name"], device_row["app_version"], device_row["registered_at"], device_row["first_seen"], device_row["last_seen"]
                ])
                send_supabase_post("devices", device_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.devices (device_id, user_id, device_name, device_type, os_name, app_version, registered_at, first_seen, last_seen) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (device_row["device_id"], device_row["user_id"], device_row["device_name"], device_row["device_type"], device_row["os_name"], device_row["app_version"], device_row["registered_at"], device_row["first_seen"], device_row["last_seen"])
                    )

                inst_row = {
                    "installation_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "device_id": did,
                    "installed_at": now_str,
                    "app_version": app_ver
                }
                append_row_to_csv(INSTALLS_CSV, ["installation_id", "user_id", "device_id", "installed_at", "app_version"], [
                    inst_row["installation_id"], inst_row["user_id"], inst_row["device_id"], inst_row["installed_at"], inst_row["app_version"]
                ])
                send_supabase_post("app_installations", inst_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.app_installations (installation_id, user_id, device_id, installed_at, app_version) VALUES (%s,%s,%s,%s,%s)",
                        (inst_row["installation_id"], inst_row["user_id"], inst_row["device_id"], inst_row["installed_at"], inst_row["app_version"])
                    )

                # Role Mapping
                mapping_row = {
                    "mapping_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "role_id": ROLES["User"]["id"],
                    "assigned_at": now_str
                }
                append_row_to_csv(ROLE_MAP_CSV, ["mapping_id", "user_id", "role_id", "assigned_at"], [
                    mapping_row["mapping_id"], mapping_row["user_id"], mapping_row["role_id"], mapping_row["assigned_at"]
                ])
                send_supabase_post("user_role_mapping", mapping_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_role_mapping (mapping_id, user_id, role_id, assigned_at) VALUES (%s,%s,%s,%s)",
                        (mapping_row["mapping_id"], mapping_row["user_id"], mapping_row["role_id"], mapping_row["assigned_at"])
                    )

                # Activity Log
                act_row = {
                    "activity_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "activity_type": "signup",
                    "source_module": "Auth",
                    "activity_time": now_str,
                    "device_id": to_bigint(did)
                }
                append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                    act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                ])
                send_supabase_post("user_activity_log", act_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                        (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                    )

                # Presence
                pres_row = {
                    "presence_id": uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF,
                    "user_id": uid,
                    "status": "Online",
                    "current_module": "Auth",
                    "last_seen": now_str
                }
                append_row_to_csv(PRESENCE_CSV, ["presence_id", "user_id", "status", "current_module", "last_seen"], [
                    pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"]
                ])
                send_supabase_post("user_presence", pres_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_presence (presence_id, user_id, status, current_module, last_seen) VALUES (%s,%s,%s,%s,%s)",
                        (pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"])
                    )

                active_users.append({"id": uid, "user_name": uname})
                user_devices[uid] = [did]
                actions.append(f"SIGNUP: User '{uname}' on '{dname}'")

            # --- 2. ACTION: ADD DEVICE (10% chance) ---
            if random.random() < 0.10 and active_users:
                user = random.choice(active_users)
                uid = user["id"]
                
                dtype = random.choices(["Mobile", "Tablet", "Desktop"], weights=[0.70, 0.10, 0.20], k=1)[0]
                dname, os_name = random.choice(device_catalog[dtype])
                did = str(uuid.uuid4())
                app_ver = random.choice(app_versions)
                
                device_row = {
                    "device_id": did,
                    "user_id": uid,
                    "device_name": dname,
                    "device_type": dtype,
                    "os_name": os_name,
                    "app_version": app_ver,
                    "registered_at": now_str,
                    "first_seen": now_str,
                    "last_seen": now_str
                }
                append_row_to_csv(DEVICES_CSV, ["device_id", "user_id", "device_name", "device_type", "os_name", "app_version", "registered_at", "first_seen", "last_seen"], [
                    device_row["device_id"], device_row["user_id"], device_row["device_name"], device_row["device_type"], device_row["os_name"], device_row["app_version"], device_row["registered_at"], device_row["first_seen"], device_row["last_seen"]
                ])
                send_supabase_post("devices", device_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.devices (device_id, user_id, device_name, device_type, os_name, app_version, registered_at, first_seen, last_seen) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (device_row["device_id"], device_row["user_id"], device_row["device_name"], device_row["device_type"], device_row["os_name"], device_row["app_version"], device_row["registered_at"], device_row["first_seen"], device_row["last_seen"])
                    )

                inst_row = {
                    "installation_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "device_id": did,
                    "installed_at": now_str,
                    "app_version": app_ver
                }
                append_row_to_csv(INSTALLS_CSV, ["installation_id", "user_id", "device_id", "installed_at", "app_version"], [
                    inst_row["installation_id"], inst_row["user_id"], inst_row["device_id"], inst_row["installed_at"], inst_row["app_version"]
                ])
                send_supabase_post("app_installations", inst_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.app_installations (installation_id, user_id, device_id, installed_at, app_version) VALUES (%s,%s,%s,%s,%s)",
                        (inst_row["installation_id"], inst_row["user_id"], inst_row["device_id"], inst_row["installed_at"], inst_row["app_version"])
                    )

                # Activity Log
                act_row = {
                    "activity_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "activity_type": "device_register",
                    "source_module": "Auth",
                    "activity_time": now_str,
                    "device_id": to_bigint(did)
                }
                append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                    act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                ])
                send_supabase_post("user_activity_log", act_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                        (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                    )

                if uid not in user_devices:
                    user_devices[uid] = []
                user_devices[uid].append(did)
                actions.append(f"DEVICE ADD: User '{user['user_name']}' registered '{dname}'")

            # --- 3. ACTION: UNINSTALL DEVICE (5% chance) ---
            if random.random() < 0.05 and active_users:
                user = random.choice(active_users)
                uid = user["id"]
                dids = user_devices.get(uid, [])
                
                if dids:
                    did = random.choice(dids)
                    reason = random.choice(uninstall_reasons)
                    
                    device_id_int = uuid.UUID(did).int & 0x7FFFFFFFFFFFFFFF
                    uninst_row = {
                        "uninstall_id": str(uuid.uuid4()),
                        "user_id": uid,
                        "device_id": device_id_int,
                        "uninstalled_at": now_str,
                        "reason": reason
                    }
                    append_row_to_csv(UNINSTALLS_CSV, ["uninstall_id", "user_id", "device_id", "uninstalled_at", "reason"], [
                        uninst_row["uninstall_id"], uninst_row["user_id"], uninst_row["device_id"], uninst_row["uninstalled_at"], uninst_row["reason"]
                    ])
                    send_supabase_post("app_uninstallations", uninst_row)
                    
                    if DATABASE_URL and HAS_PG:
                        insert_postgres_row(
                            "INSERT INTO app_auth.app_uninstallations (uninstall_id, user_id, device_id, uninstalled_at, reason) VALUES (%s,%s,%s,%s,%s)",
                            (uninst_row["uninstall_id"], uninst_row["user_id"], uninst_row["device_id"], uninst_row["uninstalled_at"], uninst_row["reason"])
                        )
                    
                    # Activity Log
                    act_row = {
                        "activity_id": str(uuid.uuid4()),
                        "user_id": uid,
                        "activity_type": "device_uninstall",
                        "source_module": "Auth",
                        "activity_time": now_str,
                        "device_id": to_bigint(did)
                    }
                    append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                        act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                    ])
                    send_supabase_post("user_activity_log", act_row)
                    if DATABASE_URL and HAS_PG:
                        insert_postgres_row(
                            "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                            (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                        )

                    user_devices[uid].remove(did)
                    actions.append(f"UNINSTALL: User '{user['user_name']}' uninstalled device ({did[:8]}...)")

            # --- 4. ACTION: LOGIN ATTEMPTS (100% chance, 1-3 attempts) ---
            num_logins = random.randint(1, 3)
            for _ in range(num_logins):
                user = random.choice(active_users)
                uid = user["id"]
                
                login_id = str(uuid.uuid4())
                l_method = random.choice(login_methods)
                ip = generate_ip()
                dtype = random.choices(["Mobile", "Tablet", "Desktop"], weights=[0.70, 0.10, 0.20], k=1)[0]
                status = random.choices(["Success", "Failed", "Blocked"], weights=[0.90, 0.08, 0.02], k=1)[0]
                
                login_row = {
                    "login_id": login_id,
                    "user_id": uid,
                    "login_time": now_str,
                    "login_method": l_method,
                    "ip_address": ip,
                    "device_type": dtype,
                    "login_status": status
                }
                append_row_to_csv(LOGINS_CSV, ["login_id", "user_id", "login_time", "login_method", "ip_address", "device_type", "login_status"], [
                    login_row["login_id"], login_row["user_id"], login_row["login_time"], login_row["login_method"], login_row["ip_address"], login_row["device_type"], login_row["login_status"]
                ])
                send_supabase_post("login_history", login_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.login_history (login_id, user_id, login_time, login_method, ip_address, device_type, login_status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (login_row["login_id"], login_row["user_id"], login_row["login_time"], login_row["login_method"], login_row["ip_address"], login_row["device_type"], login_row["login_status"])
                    )

                # Sessions, activity, and presence logging for logins
                dids = user_devices.get(uid, [])
                did = random.choice(dids) if dids else str(uuid.uuid4())
                
                # Activity Log
                act_row = {
                    "activity_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "activity_type": f"login_{status.lower()}",
                    "source_module": "Auth",
                    "activity_time": now_str,
                    "device_id": to_bigint(did)
                }
                append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                    act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                ])
                send_supabase_post("user_activity_log", act_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                        (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                    )

                # Presence
                pres_row = {
                    "presence_id": uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF,
                    "user_id": uid,
                    "status": "Online" if status == "Success" else "Offline",
                    "current_module": "Auth" if status == "Success" else None,
                    "last_seen": now_str
                }
                append_row_to_csv(PRESENCE_CSV, ["presence_id", "user_id", "status", "current_module", "last_seen"], [
                    pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"]
                ])
                send_supabase_post("user_presence", pres_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_presence (presence_id, user_id, status, current_module, last_seen) VALUES (%s,%s,%s,%s,%s)",
                        (pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"])
                    )

                if status == "Success":
                    # Create active session with predetermined logout_time
                    duration_mins = random.randint(5, 480)
                    logout_dt = now_dt + datetime.timedelta(minutes=duration_mins)
                    logout_str = logout_dt.strftime("%Y-%m-%d %H:%M:%S")
                    sess_row = {
                        "session_id": str(uuid.uuid4()),
                        "user_id": uid,
                        "session_token": "sess_" + uuid.uuid4().hex[:20],
                        "session_status": "Active",
                        "login_time": now_str,
                        "logout_time": logout_str
                    }
                    append_row_to_csv(SESSIONS_CSV, ["session_id", "user_id", "session_token", "session_status", "login_time", "logout_time"], [
                        sess_row["session_id"], sess_row["user_id"], sess_row["session_token"], sess_row["session_status"], sess_row["login_time"], sess_row["logout_time"]
                    ])
                    send_supabase_post("user_sessions", sess_row)
                    if DATABASE_URL and HAS_PG:
                        insert_postgres_row(
                            "INSERT INTO app_auth.user_sessions (session_id, user_id, session_token, session_status, login_time, logout_time) VALUES (%s,%s,%s,%s,%s,%s)",
                            (sess_row["session_id"], sess_row["user_id"], sess_row["session_token"], sess_row["session_status"], sess_row["login_time"], logout_dt)
                        )

                actions.append(f"LOGIN: User '{user['user_name']}' via {l_method} ({status})")

            # --- 5. ACTION: MODULE USAGE (40% chance) ---
            if random.random() < 0.40 and active_users:
                user = random.choice(active_users)
                uid = user["id"]
                
                # Fetch random active module
                mod_name = random.choice(list(set(p[1] for p in PERMISSIONS.values())) + ["ProfileSettings", "Dashboard"])
                dur = random.randint(1, 45)  # Session duration in minutes
                start_dt = now_dt - datetime.timedelta(minutes=dur)
                start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                usage_row = {
                    "usage_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "module_name": mod_name,
                    "session_start": start_str,
                    "session_end": now_str
                }
                append_row_to_csv(USAGE_CSV, ["usage_id", "user_id", "module_name", "session_start", "session_end"], [
                    usage_row["usage_id"], usage_row["user_id"], usage_row["module_name"], usage_row["session_start"], usage_row["session_end"]
                ])
                send_supabase_post("module_usage", usage_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.module_usage (usage_id, user_id, module_name, session_start, session_end) VALUES (%s,%s,%s,%s,%s)",
                        (usage_row["usage_id"], usage_row["user_id"], usage_row["module_name"], usage_row["session_start"], usage_row["session_end"])
                    )

                # Activity Log
                dids = user_devices.get(uid, [])
                did = random.choice(dids) if dids else str(uuid.uuid4())
                act_row = {
                    "activity_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "activity_type": "module_access",
                    "source_module": mod_name,
                    "activity_time": now_str,
                    "device_id": to_bigint(did)
                }
                append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                    act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                ])
                send_supabase_post("user_activity_log", act_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                        (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                    )

                # Presence update
                pres_row = {
                    "presence_id": uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF,
                    "user_id": uid,
                    "status": "Online",
                    "current_module": mod_name,
                    "last_seen": now_str
                }
                append_row_to_csv(PRESENCE_CSV, ["presence_id", "user_id", "status", "current_module", "last_seen"], [
                    pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"]
                ])
                send_supabase_post("user_presence", pres_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_presence (presence_id, user_id, status, current_module, last_seen) VALUES (%s,%s,%s,%s,%s)",
                        (pres_row["presence_id"], pres_row["user_id"], pres_row["status"], pres_row["current_module"], pres_row["last_seen"])
                    )

                actions.append(f"USAGE: User '{user['user_name']}' accessed '{mod_name}' for {dur} mins")

            # --- 6. ACTION: OTP REQUEST/VERIFY (30% chance) ---
            if random.random() < 0.30 and active_users:
                user = random.choice(active_users)
                uid = user["id"]
                
                otp_code = f"{random.randint(100000, 999999)}"
                purpose = random.choice(["Login", "Registration", "Password Reset"])
                status = random.choices(["Pending", "Verified", "Expired"], weights=[0.20, 0.70, 0.10], k=1)[0]
                
                # Sent 1-3 minutes ago
                sent_dt = now_dt - datetime.timedelta(minutes=random.randint(1, 3))
                sent_str = sent_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                # Expires in 5 minutes
                exp_dt = sent_dt + datetime.timedelta(minutes=5)
                exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                otp_status_bool = (status == "Verified")
                
                otp_row = {
                    "otp_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "otp_code": otp_code,
                    "verification_type": purpose,
                    "sent_at": sent_str,
                    "expires_id": exp_str,
                    "status": otp_status_bool
                }
                append_row_to_csv(OTP_CSV, ["otp_id", "user_id", "otp_code", "verification_type", "sent_at", "expires_id", "status"], [
                    otp_row["otp_id"], otp_row["user_id"], otp_row["otp_code"], otp_row["verification_type"], otp_row["sent_at"], otp_row["expires_id"], otp_row["status"]
                ])
                send_supabase_post("otp_verifications", otp_row)
                
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.otp_verifications (otp_id, user_id, otp_code, verification_type, sent_at, expires_id, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (otp_row["otp_id"], otp_row["user_id"], otp_row["otp_code"], otp_row["verification_type"], otp_row["sent_at"], otp_row["expires_id"], otp_row["status"])
                    )

                # Activity Log
                dids = user_devices.get(uid, [])
                did = random.choice(dids) if dids else str(uuid.uuid4())
                act_row = {
                    "activity_id": str(uuid.uuid4()),
                    "user_id": uid,
                    "activity_type": "otp_request",
                    "source_module": "Auth",
                    "activity_time": now_str,
                    "device_id": to_bigint(did)
                }
                append_row_to_csv(ACTIVITY_CSV, ["activity_id", "user_id", "activity_type", "source_module", "activity_time", "device_id"], [
                    act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"]
                ])
                send_supabase_post("user_activity_log", act_row)
                if DATABASE_URL and HAS_PG:
                    insert_postgres_row(
                        "INSERT INTO app_auth.user_activity_log (activity_id, user_id, activity_type, source_module, activity_time, device_id) VALUES (%s,%s,%s,%s,%s,%s)",
                        (act_row["activity_id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["activity_time"], act_row["device_id"])
                    )

                actions.append(f"OTP: Sent {purpose} code to '{user['user_name']}' (Result: {status})")

            # Console output summary
            print(f"[{now_str}] Tick #{tick} | Performed {len(actions)} actions:")
            for act in actions:
                print(f"  - {act}")
            print()
            
            if max_ticks is not None and tick >= max_ticks:
                print(f"Reached max ticks ({max_ticks}). Simulator exiting cleanly.")
                break

            time.sleep(TICK_INTERVAL * random.uniform(0.90, 1.10))
            
    except KeyboardInterrupt:
        print("\nAuthentication Simulator stopped by user.")
        print(f"Total loop ticks simulated: {tick}")

if __name__ == "__main__":
    main()
