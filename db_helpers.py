import os
import sys
import uuid
import random
import json
import csv
import urllib.request
import urllib.error
import datetime

# Ensure UTF-8 output on Windows terminal
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Workspace directories & files
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.path.dirname(os.path.abspath(__file__)))

# CSV mappings
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

GROUPS_CSV_PATH = os.path.join(WORKSPACE_DIR, "groups_mock_data.csv")
MEMBERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_members_mock_data.csv")
MESSAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "group_messages_mock_data.csv")
EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "events_mock_data.csv")
ANNOUNCEMENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "announcements_mock_data.csv")
GROUP_PLAYLIST_TRACKS_CSV = os.path.join(WORKSPACE_DIR, "group_playlist_tracks_mock_data.csv")

ROOMS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_rooms_mock_data.csv")
PARTICIPANTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_participants_mock_data.csv")
DUAL_MESSAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_messages_mock_data.csv")
CALLS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_calls_mock_data.csv")
MATCHES_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_matches_mock_data.csv")
DUAL_SONGS_CSV_PATH = os.path.join(WORKSPACE_DIR, "dual_song_requests_mock_data.csv")

MUSIC_CHANNELS_CSV = os.path.join(WORKSPACE_DIR, "music_channels_mock_data.csv")
MUSIC_TRACKS_CSV = os.path.join(WORKSPACE_DIR, "music_tracks_mock_data.csv")
PLAYLISTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "channel_playlists_mock_data.csv")
PLAYLIST_TRACKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "playlist_tracks_mock_data.csv")
CURRENT_PLAYING_CSV_PATH = os.path.join(WORKSPACE_DIR, "current_playing_mock_data.csv")
HISTORY_CSV_PATH = os.path.join(WORKSPACE_DIR, "listening_history_mock_data.csv")
MUSIC_EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_events_mock_data.csv")
FAVORITES_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_favorites_mock_data.csv")
MUSIC_SESSIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_listener_sessions_mock_data.csv")
NOTIFICATIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "notifications_mock_data.csv")
LANGUAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "languages_mock_data.csv")
BADGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "badges_mock_data.csv")
STATES_CSV_PATH = os.path.join(WORKSPACE_DIR, "states_mock_data.csv")
USER_ACTIVITY_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_activity_mock_data.csv")
USER_BADGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_badges_mock_data.csv")
USER_FOLLOWING_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_following_mock_data.csv")
USER_PROFILES_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_profiles_mock_data.csv")

PODCASTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcasts_mock_data.csv")
EPISODES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_episodes_mock_data.csv")
PODCAST_FOLLOWERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_followers_mock_data.csv")
PODCAST_LIKES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_likes_mock_data.csv")
PODCAST_COMMENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_comments_mock_data.csv")
PODCAST_SHARES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_shares_mock_data.csv")
PODCAST_BOOKMARKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_bookmarks_mock_data.csv")
PODCAST_SESSIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_listener_sessions_mock_data.csv")
PODCAST_COMPLETION_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_completion_mock_data.csv")
PODCAST_EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_events_mock_data.csv")
LIVE_SESS_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_sessions_mock_data.csv")
LIVE_LIST_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_listeners_mock_data.csv")
LIVE_CHAT_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_chat_mock_data.csv")
LIVE_QUEST_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_questions_mock_data.csv")
LIVE_REACT_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_reactions_mock_data.csv")
CONTENT_REPORTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "content_reports_mock_data.csv")
ASSIGN_CSV_PATH = os.path.join(WORKSPACE_DIR, "operator_assignments_mock_data.csv")
FLAGGED_CSV_PATH = os.path.join(WORKSPACE_DIR, "flagged_content_mock_data.csv")
LISTENER_ANALYTICS_CSV_PATH = os.path.join(WORKSPACE_DIR, "listener_analytics_mock_data.csv")
ROOM_PARTICIPANTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "room_participants_mock_data.csv")
RJ_CHANNELS_CSV = os.path.join(WORKSPACE_DIR, "rj_channels_mock_data.csv")
OPERATORS_CSV_PATH = os.path.join(WORKSPACE_DIR, "operators_mock_data.csv")
AUDIT_LOGS_CSV_PATH = os.path.join(WORKSPACE_DIR, "audit_logs_mock_data.csv")
REPORTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "reports_mock_data.csv")
MOD_ACTIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "moderation_actions_mock_data.csv")
RJS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rjs_mock_data.csv")
RJ_SHOWS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_live_shows_mock_data.csv")
RJ_CHAT_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_chat_messages_mock_data.csv")
RJ_FOLLOWERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_followers_mock_data.csv")
RJ_LISTENER_SESS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_listener_sessions_mock_data.csv")
SONG_REQ_CSV_PATH = os.path.join(WORKSPACE_DIR, "song_requests_mock_data.csv")
SONG_LIKES_CSV_PATH = os.path.join(WORKSPACE_DIR, "song_likes_mock_data.csv")

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

# Database / Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Fallback credentials
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVoaGx1ZG15dmVvaXh6a25xd250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1NjIyOTQsImV4cCI6MjA5NzEzODI5NH0.2zVm9zF1CA9SDwUvTUiXSE4fiN5adqFL4Sg29a6W1TE"

# Table schema routing dictionary
TABLE_SCHEMAS = {
    # app_auth
    "users": "app_auth",
    "devices": "app_auth",
    "app_installations": "app_auth",
    "login_history": "app_auth",
    "module_usage": "app_auth",
    "otp_verifications": "app_auth",
    "user_roles": "app_auth",
    "permissions": "app_auth",
    "role_permissions": "app_auth",
    "user_role_mapping": "app_auth",
    "user_activity_log": "app_auth",
    "user_presence": "app_auth",
    "user_sessions": "app_auth",
    
    # app_group
    "groups": "app_group",
    "group_members": "app_group",
    "group_messages": "app_group",
    "group_events": "app_group",
    "announcements": "app_group",
    "group_playlist_tracks": "app_group",
    
    # app_dual
    "dual_rooms": "app_dual",
    "dual_participants": "app_dual",
    "dual_messages": "app_dual",
    "dual_calls": "app_dual",
    "dual_matches": "app_dual",
    "dual_song_requests": "app_dual",
    
    # app_podcast (Routed to app_operator to match database catalog)
    "podcasts": "app_operator",
    "podcast_episodes": "app_operator",
    "podcast_followers": "app_operator",
    "podcast_likes": "app_operator",
    "podcast_comments": "app_operator",
    "podcast_shares": "app_operator",
    "podcast_bookmarks": "app_operator",
    "podcast_listener_sessions": "app_operator",
    "podcast_completion": "app_operator",
    "podcast_events": "app_operator",
    "live_podcast_sessions": "app_operator",
    "live_podcast_listeners": "app_operator",
    "live_podcast_chat": "app_operator",
    "live_podcast_questions": "app_operator",
    "live_podcast_reactions": "app_operator",
    "content_reports": "app_operator",
    "operator_assignments": "app_operator",
    "flagged_content": "app_operator",
    "listener_analytics": "app_operator",
    "room_participants": "app_operator",
    
    # app_operator
    "operators": "app_operator",
    "audit_logs": "app_operator",
    "reports": "app_operator",
    "moderation_actions": "app_operator",
    "rjs": "app_operator",
    "rj_channels": "app_operator",
    "rj_live_shows": "app_operator",
    "rj_chat_messages": "app_operator",
    "rj_followers": "app_operator",
    "rj_listener_sessions": "app_operator",
    "song_requests": "app_operator",
    "song_likes": "app_operator",
    
    # app_open
    "languages": "app_open",
    "badges": "app_open",
    "states": "app_open",
    "user_profiles": "app_open",
    "music_tracks": "app_open",
    "music_channels": "app_open",
    "channel_playlists": "app_open",
    "playlist_tracks": "app_open",
    "user_activity": "app_open",
    "current_playing": "app_open",
    "listening_history": "app_open",
    "music_events": "app_open",
    "music_favorites": "app_open",
    "music_listener_sessions": "app_open",
    "notifications": "app_open",
    "user_badges": "app_open",
    "user_following": "app_open",
}

# Music genres pool
GENRES = ["Rock", "Pop", "Bollywood", "Telugu", "Tamil", "K-Pop", "Jazz", "Classical", "Hip Hop", "Devotional", "Lo-Fi"]

USER_PROFILES_CACHE = {}

def get_user_preferences(user_id):
    """
    Derives user's music preferences deterministically from their UUID string.
    Returns a list of 3 genres.
    """
    if not user_id:
        return ["Lo-Fi", "Pop", "Rock"]
    try:
        val = int(uuid.UUID(str(user_id)).int)
    except Exception:
        val = hash(str(user_id))
    primary = GENRES[val % len(GENRES)]
    secondary = GENRES[(val // len(GENRES)) % len(GENRES)]
    if secondary == primary:
        secondary = GENRES[(val + 1) % len(GENRES)]
    third = GENRES[(val + 2) % len(GENRES)]
    if third in (primary, secondary):
        third = GENRES[(val + 3) % len(GENRES)]
    return [primary, secondary, third]

def get_user_interests(user_id, bio_text=None):
    if not user_id:
        return ["Lo-Fi", "Pop", "Rock"]
    if user_id in USER_PROFILES_CACHE:
        return USER_PROFILES_CACHE[user_id]
    
    if bio_text and "Interests: " in bio_text:
        try:
            parts = bio_text.split("Interests: ")[1].split(".")[0].split(",")
            genres = [g.strip() for g in parts if g.strip() in GENRES]
            if genres:
                USER_PROFILES_CACHE[user_id] = genres
                return genres
        except Exception:
            pass
            
    prefs = get_user_preferences(user_id)
    USER_PROFILES_CACHE[user_id] = prefs
    return prefs

group_genres_map = {
    "Lo-Fi Beats Study Hub": "Lo-Fi",
    "Bollywood Retro Classics": "Bollywood",
    "Techno & Trance Rave": "Rock",
    "Hip Hop Cypher Room": "Hip Hop",
    "Acoustic Indie Sessions": "Pop",
    "Metalheads Corner": "Rock",
    "Sunday Jazz Brunch": "Jazz",
    "K-Pop Stans Gathering": "K-Pop",
    "Telugu Folk Vibez": "Telugu",
    "Late Night Coding Tracks": "Lo-Fi",
    "Classical Symphony Hall": "Classical"
}

def get_group_genre(gname):
    if not gname:
        return "Lo-Fi"
    for prefix, gen in group_genres_map.items():
        if gname.startswith(prefix):
            return gen
    return "Lo-Fi"

# Caches
USERS = []
GROUPS = []
CHANNELS = []
PODCASTS = []
ROOMS = []
TRACKS = []

def send_supabase_get(table_name, select="*"):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    schema = TABLE_SCHEMAS.get(table_name, "public")
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}?select={select}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": schema
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"[Supabase API] GET {table_name} failed: {e}", file=sys.stderr)
        return None

def send_supabase_post(table_name, payload):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    schema = TABLE_SCHEMAS.get(table_name, "public")
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": schema,
        "Content-Profile": schema
    }
    body = json.dumps(payload).encode("utf-8")
    import time
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 201)
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print(f"[Supabase API Warning] POST {table_name} returned 409 Conflict. Handled as success.", file=sys.stderr)
                return True
            try:
                error_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                error_body = "(could not read body)"
            print(f"[Supabase API Error] POST {table_name} failed (attempt {attempt+1}): HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
            if e.code >= 500 and attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
        except Exception as e:
            print(f"[Supabase API Error] POST {table_name} failed (attempt {attempt+1}): {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
    return False

def send_supabase_patch(table_name, payload, query_params):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    schema = TABLE_SCHEMAS.get(table_name, "public")
    query_str = "&".join(f"{k}=eq.{v}" for k, v in query_params.items())
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}?{query_str}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": schema,
        "Content-Profile": schema
    }
    body = json.dumps(payload).encode("utf-8")
    import time
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 201, 204)
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                error_body = "(could not read body)"
            print(f"[Supabase API Error] PATCH {table_name} failed (attempt {attempt+1}): HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
            if e.code >= 500 and attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
        except Exception as e:
            print(f"[Supabase API Error] PATCH {table_name} failed (attempt {attempt+1}): {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
    return False

def send_supabase_upsert(table_name, payload, conflict_target="id"):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    schema = TABLE_SCHEMAS.get(table_name, "public")
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}?on_conflict={conflict_target}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
        "Accept-Profile": schema,
        "Content-Profile": schema
    }
    body = json.dumps(payload).encode("utf-8")
    import time
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 201, 204)
        except urllib.error.HTTPError as e:
            if e.code in (401, 409):
                print(f"[Supabase API Warning] UPSERT {table_name} returned HTTP {e.code}. Handled as success.", file=sys.stderr)
                return True
            try:
                error_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                error_body = "(could not read body)"
            print(f"[Supabase API Error] UPSERT {table_name} failed (attempt {attempt+1}): HTTP {e.code} ({e.reason})\nResponse Body: {error_body}", file=sys.stderr)
            if e.code >= 500 and attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
        except Exception as e:
            print(f"[Supabase API Error] UPSERT {table_name} failed (attempt {attempt+1}): {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
    return False

def insert_postgres_row(query, params):
    if not DATABASE_URL or not HAS_PG:
        return False
    import time
    for attempt in range(3):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                cur.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            err_str = str(e)
            if "unique constraint" in err_str or "23505" in err_str:
                print(f"[PostgreSQL Warning] Unique constraint violation: {e}", file=sys.stderr)
                return True
            print(f"[PostgreSQL Error] query failed (attempt {attempt+1}): {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1 * (2 ** attempt))
                continue
            return False
    return False

# Reusable cache getters
def get_users():
    global USERS
    res = send_supabase_get("users", "id,user_name,email")
    if res is not None and len(res) > 0:
        USERS = [{"id": u["id"], "user_name": u.get("user_name", "Anonymous"), "email": u.get("email", "user@example.com")} for u in res]
    else:
        USERS = []
        if os.path.exists(USERS_CSV):
            try:
                with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            USERS.append({
                                "id": row["id"],
                                "user_name": row.get("user_name", "Anonymous"),
                                "email": row.get("email", "user@example.com")
                            })
            except Exception as e:
                print(f"Error reading users CSV: {e}", file=sys.stderr)
    return USERS

def get_groups():
    global GROUPS
    res = send_supabase_get("groups", "id,group_name,created_by")
    if res is not None:
        GROUPS = [{"id": g["id"], "group_name": g.get("group_name", "Group"), "created_by": g.get("created_by")} for g in res]
    else:
        GROUPS = []
        if os.path.exists(GROUPS_CSV_PATH):
            try:
                with open(GROUPS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            GROUPS.append({
                                "id": row["id"],
                                "group_name": row.get("group_name", "Group"),
                                "created_by": row.get("created_by")
                            })
            except Exception as e:
                print(f"Error reading groups CSV: {e}", file=sys.stderr)
    return GROUPS

def get_channels():
    global CHANNELS
    res_music = send_supabase_get("music_channels", "id,channel_code,channel_name")
    res_rj = send_supabase_get("rj_channels", "id,channel_code,channel_name")
    
    channels_dict = {}
    if res_music is not None:
        for c in res_music:
            channels_dict[c["id"]] = {
                "id": c["id"],
                "channel_code": c.get("channel_code"),
                "channel_name": c.get("channel_name"),
                "type": "music"
            }
    if res_rj is not None:
        for c in res_rj:
            channels_dict[c["id"]] = {
                "id": c["id"],
                "channel_code": c.get("channel_code"),
                "channel_name": c.get("channel_name"),
                "type": "rj"
            }
            
    if res_music is None and res_rj is None:
        CHANNELS = []
        if os.path.exists(MUSIC_CHANNELS_CSV):
            try:
                with open(MUSIC_CHANNELS_CSV, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            CHANNELS.append({
                                "id": row["id"],
                                "channel_code": row.get("channel_code"),
                                "channel_name": row.get("channel_name"),
                                "type": "music"
                            })
            except Exception as e:
                print(f"Error reading music channels CSV: {e}", file=sys.stderr)
        if os.path.exists(RJ_CHANNELS_CSV):
            try:
                with open(RJ_CHANNELS_CSV, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            CHANNELS.append({
                                "id": row["id"],
                                "channel_code": row.get("channel_code"),
                                "channel_name": row.get("channel_name"),
                                "type": "rj"
                            })
            except Exception as e:
                print(f"Error reading rj channels CSV: {e}", file=sys.stderr)
    else:
        CHANNELS = list(channels_dict.values())
    return CHANNELS

def get_podcasts():
    global PODCASTS
    res = send_supabase_get("podcasts", "id,podcast_code,title,host_name,category")
    if res is not None:
        PODCASTS = [{"id": p["id"], "podcast_code": p.get("podcast_code"), "title": p.get("title"), "host_name": p.get("host_name"), "category": p.get("category", "music")} for p in res]
    else:
        PODCASTS = []
        if os.path.exists(PODCASTS_CSV_PATH):
            try:
                with open(PODCASTS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            PODCASTS.append({
                                "id": row["id"],
                                "podcast_code": row.get("podcast_code"),
                                "title": row.get("title"),
                                "host_name": row.get("host_name"),
                                "category": row.get("category", "music")
                            })
            except Exception as e:
                print(f"Error reading podcasts CSV: {e}", file=sys.stderr)
    return PODCASTS

def get_rooms():
    global ROOMS
    res = send_supabase_get("dual_rooms", "id,room_code,room_name,created_by")
    if res is not None:
        ROOMS = [{"id": r["id"], "room_code": r.get("room_code"), "room_name": r.get("room_name"), "created_by": r.get("created_by")} for r in res]
    else:
        ROOMS = []
        if os.path.exists(ROOMS_CSV_PATH):
            try:
                with open(ROOMS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            ROOMS.append({
                                "id": row["id"],
                                "room_code": row.get("room_code"),
                                "room_name": row.get("room_name"),
                                "created_by": row.get("created_by")
                            })
            except Exception as e:
                print(f"Error reading rooms CSV: {e}", file=sys.stderr)
    return ROOMS

def get_tracks():
    global TRACKS
    res = send_supabase_get("music_tracks", "id,track_code,title,artist,genre")
    if res is not None:
        TRACKS = [{"id": t["id"], "track_code": t.get("track_code"), "title": t.get("title"), "artist": t.get("artist"), "genre": t.get("genre", "Lo-Fi")} for t in res]
    else:
        TRACKS = []
        if os.path.exists(MUSIC_TRACKS_CSV):
            try:
                with open(MUSIC_TRACKS_CSV, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("id"):
                            TRACKS.append({
                                "id": row["id"],
                                "track_code": row.get("track_code"),
                                "title": row.get("title"),
                                "artist": row.get("artist"),
                                "genre": row.get("genre", "Lo-Fi")
                            })
            except Exception as e:
                print(f"Error reading tracks CSV: {e}", file=sys.stderr)
    return TRACKS

DETECTED_COLUMNS = {
    "group_messages_group_column": "group_id",
    "group_playlist_tracks_group_column": "group_id",
    "dual_messages_sender_column": "sender_user_id"
}

def detect_database_schema():
    global DETECTED_COLUMNS
    # Detect group_messages column
    if send_supabase_get("group_messages", "group_id") is not None:
        DETECTED_COLUMNS["group_messages_group_column"] = "group_id"
    else:
        DETECTED_COLUMNS["group_messages_group_column"] = "room_id"
        
    # Detect group_playlist_tracks column
    if send_supabase_get("group_playlist_tracks", "group_id") is not None:
        DETECTED_COLUMNS["group_playlist_tracks_group_column"] = "group_id"
    else:
        DETECTED_COLUMNS["group_playlist_tracks_group_column"] = "room_id"
        
    # Detect dual_messages column
    if send_supabase_get("dual_messages", "sender_user_id") is not None:
        DETECTED_COLUMNS["dual_messages_sender_column"] = "sender_user_id"
    else:
        DETECTED_COLUMNS["dual_messages_sender_column"] = "sender_id"
        
    print(f"[Schema Detector] Detected DB columns: {DETECTED_COLUMNS}", file=sys.stderr)

def refresh_all_caches(tick=None):
    if tick is None or tick % 30 == 0:
        detect_database_schema()
    if tick is None or tick % 5 == 0:
        get_users()
        get_groups()
        get_channels()
        get_podcasts()
        get_rooms()
        get_tracks()
        print(f"[Cache Synchronizer] Loaded active cache entities: USERS={len(USERS)}, GROUPS={len(GROUPS)}, CHANNELS={len(CHANNELS)}, PODCASTS={len(PODCASTS)}, ROOMS={len(ROOMS)}, TRACKS={len(TRACKS)}")
