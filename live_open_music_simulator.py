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

# 17 CSV Paths
LANGUAGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "languages_mock_data.csv")
BADGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "badges_mock_data.csv")
TRACKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_tracks_mock_data.csv")
CHANNELS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_channels_mock_data.csv")
PLAYLISTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "channel_playlists_mock_data.csv")
CURRENT_PLAYING_CSV_PATH = os.path.join(WORKSPACE_DIR, "current_playing_mock_data.csv")
HISTORY_CSV_PATH = os.path.join(WORKSPACE_DIR, "listening_history_mock_data.csv")
EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_events_mock_data.csv")
FAVORITES_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_favorites_mock_data.csv")
SESSIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "music_listener_sessions_mock_data.csv")
NOTIFICATIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "notifications_mock_data.csv")
PLAYLIST_TRACKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "playlist_tracks_mock_data.csv")
STATES_CSV_PATH = os.path.join(WORKSPACE_DIR, "states_mock_data.csv")
USER_ACTIVITY_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_activity_mock_data.csv")
USER_BADGES_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_badges_mock_data.csv")
USER_FOLLOWING_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_following_mock_data.csv")
USER_PROFILES_CSV_PATH = os.path.join(WORKSPACE_DIR, "user_profiles_mock_data.csv")

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

# Fallback credentials if not in env
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVoaGx1ZG15dmVvaXh6a25xd250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1NjIyOTQsImV4cCI6MjA5NzEzODI5NH0.2zVm9zF1CA9SDwUvTUiXSE4fiN5adqFL4Sg29a6W1TE"

# Seed data pools
languages_list = ["English", "Hindi", "Telugu", "Tamil", "Punjabi", "Spanish", "Korean"]

badges_pool = [
    ("First Tune", "Listen to your first track in any music channel."),
    ("Vibe Master", "Follow at least 5 different music channels."),
    ("Party Animal", "Listen to music channels for over 5 cumulative hours."),
    ("Song Collector", "Mark at least 10 different tracks as favorites."),
    ("Night Owl", "Listen to music channels between 12 AM and 4 AM.")
]

states_list = ["California", "Texas", "New York", "Florida", "Illinois", "Telangana", "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi"]
countries_list = ["USA", "India", "UK", "Canada", "Germany"]

channel_genres = ["Lo-Fi", "Bollywood Hits", "Techno", "Hip Hop", "Acoustic", "Jazz", "Classical", "K-Pop", "Devotional"]

track_titles = [
    ("Kesariya", "Arijit Singh", "Brahmastra", "Hindi", "Bollywood Hits"),
    ("Dynamite", "BTS", "Be", "Korean", "K-Pop"),
    ("Starboy", "The Weeknd", "Starboy", "English", "Techno"),
    ("Naatu Naatu", "M. M. Keeravani", "RRR", "Telugu", "Devotional"),
    ("In the End", "Linkin Park", "Hybrid Theory", "English", "Techno"),
    ("Take Five", "Dave Brubeck", "Time Out", "English", "Jazz"),
    ("Get Lucky", "Daft Punk", "Random Access Memories", "English", "Techno"),
    ("Lofi Rain", "Chillhop Music", "Winter Lofi", "English", "Lo-Fi"),
    ("Fix You", "Coldplay", "X&Y", "English", "Acoustic"),
    ("Blinding Lights", "The Weeknd", "After Hours", "English", "Techno"),
    ("Samajavaragamana", "Sid Sriram", "Ala Vaikunthapurramuloo", "Telugu", "Acoustic"),
    ("Butta Bomma", "Armaan Malik", "Ala Vaikunthapurramuloo", "Telugu", "Bollywood Hits"),
    ("Butter", "BTS", "Butter", "Korean", "K-Pop"),
    ("Senorita", "Shawn Mendes", "Shawn Mendes", "Spanish", "Acoustic")
]

# Track states to maintain relations
active_channels = []  # dict: {id, channel_code, name, genre, listeners_count}
active_tracks = []    # dict: {id, title, artist, play_count, likes_count}
active_playlists = [] # dict: {id, channel_id, name}
active_sessions = []  # dict: {id, channel_id, user_id, joined_at}

def load_user_pool():
    """Load existing users from CSV to maintain proper referential integrity"""
    users = []
    if os.path.exists(USERS_CSV_PATH):
        try:
            with open(USERS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("id"):
                        users.append({
                            "id": row["id"],
                            "user_name": row.get("user_name", "Anonymous"),
                            "email": row.get("email", "user@example.com")
                        })
        except Exception as e:
            print(f"Warning: Could not parse users CSV: {e}", file=sys.stderr)
            
    if not users:
        print("[Warning] No user pool loaded from users_mock_data.csv. Generating local mock user list.")
        for _ in range(100):
            uid_str = str(uuid.uuid4())
            users.append({
                "id": uid_str,
                "user_name": f"User_{uid_str[:8]}",
                "email": f"user_{uid_str[:8]}@example.com"
            })
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
        "Accept-Profile": "app_open",
        "Content-Profile": "app_open"
    }
    body = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except urllib.error.HTTPError as e:
        # 409 conflict can happen when seeding unique config values
        if e.code == 409 and table_name in ("languages", "badges", "states", "user_profiles"):
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

def seed_static_tables(users):
    print("Checking static languages, badges, states and profiles...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Seed Languages
    for lang in languages_list:
        lang_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lang-{lang}"))
        lang_row = {
            "id": lang_id,
            "language_name": lang
        }
        append_to_csv(LANGUAGES_CSV_PATH, ["id", "language_name"], [lang_row["id"], lang_row["language_name"]])
        send_supabase_post("languages", lang_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.languages (id, language_name) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (lang_id, lang)
            )

    # 2. Seed Badges
    for b_name, b_desc in badges_pool:
        badge_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"badge-{b_name}"))
        badge_row = {
            "id": badge_id,
            "badge_name": b_name,
            "description": b_desc,
            "created_at": now_str
        }
        append_to_csv(BADGES_CSV_PATH, ["id", "badge_name", "description", "created_at"], [
            badge_row["id"], badge_row["badge_name"], badge_row["description"], badge_row["created_at"]
        ])
        send_supabase_post("badges", badge_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.badges (id, badge_name, description, created_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (badge_id, b_name, b_desc, datetime.datetime.now())
            )

    # 3. Seed States
    for state in states_list:
        state_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"state-{state}"))
        state_row = {
            "id": state_id,
            "state_name": state
        }
        append_to_csv(STATES_CSV_PATH, ["id", "state_name"], [state_row["id"], state_row["state_name"]])
        send_supabase_post("states", state_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.states (id, state_name) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (state_id, state)
            )

    # 4. Seed User Profiles (Limit to first 50 users to avoid initial load overhead)
    for u in users[:50]:
        profile_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"profile-{u['id']}"))
        username = u["user_name"].lower().replace(" ", "_")
        state_val = random.choice(states_list)
        country_val = random.choice(countries_list)
        
        profile_row = {
            "id": profile_id,
            "user_id": u["id"],
            "username": username,
            "display_name": u["user_name"],
            "email": u["email"],
            "language": random.choice(languages_list),
            "state": state_val,
            "country": country_val,
            "profile_image_url": f"https://example.com/avatar/{username}.png",
            "bio": f"Music lover from {state_val}.",
            "followers_count": random.randint(0, 100)
        }
        append_to_csv(USER_PROFILES_CSV_PATH, [
            "id", "user_id", "username", "display_name", "email", "language", "state", "country", "profile_image_url", "bio", "followers_count"
        ], [
            profile_row["id"], profile_row["user_id"], profile_row["username"], profile_row["display_name"], profile_row["email"],
            profile_row["language"], profile_row["state"], profile_row["country"], profile_row["profile_image_url"], profile_row["bio"], profile_row["followers_count"]
        ])
        send_supabase_post("user_profiles", profile_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.user_profiles (id, user_id, username, display_name, email, language, state, country, profile_image_url, bio, followers_count) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (profile_id, u["id"], username, u["user_name"], u["email"], profile_row["language"], state_val, country_val, profile_row["profile_image_url"], profile_row["bio"], profile_row["followers_count"])
            )
    print("Static configurations and profiles verified.")

def seed_initial_music_catalogs():
    print("Checking initial tracks and channels pool...")
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Seed Music Tracks
    for idx, (title, artist, album, language, genre) in enumerate(track_titles):
        track_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"track-{title}-{artist}"))
        track_code = f"TRK-{100000 + idx}"
        duration = random.randint(150, 320)
        release = random.randint(2010, 2026)
        
        track_row = {
            "id": track_id,
            "track_code": track_code,
            "title": title,
            "artist": artist,
            "album": album,
            "language": language,
            "genre": genre,
            "duration_seconds": duration,
            "release_year": release,
            "file_url": f"https://example.com/audio/{track_code}.mp3",
            "cover_image_url": f"https://example.com/images/{track_code}.jpg",
            "play_count": random.randint(100, 5000),
            "likes_count": random.randint(5, 500),
            "created_at": now_str
        }
        
        append_to_csv(TRACKS_CSV_PATH, [
            "id", "track_code", "title", "artist", "album", "language", "genre", "duration_seconds", "release_year", "file_url", "cover_image_url", "play_count", "likes_count", "created_at"
        ], [
            track_row["id"], track_row["track_code"], track_row["title"], track_row["artist"], track_row["album"], track_row["language"], track_row["genre"],
            track_row["duration_seconds"], track_row["release_year"], track_row["file_url"], track_row["cover_image_url"], track_row["play_count"], track_row["likes_count"], track_row["created_at"]
        ])
        send_supabase_post("music_tracks", track_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.music_tracks (id, track_code, title, artist, album, language, genre, duration_seconds, release_year, file_url, cover_image_url, play_count, likes_count, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (track_id, track_code, title, artist, album, language, genre, duration, release, track_row["file_url"], track_row["cover_image_url"], track_row["play_count"], track_row["likes_count"], now_dt)
            )
        active_tracks.append({
            "id": track_id,
            "title": title,
            "artist": artist,
            "play_count": track_row["play_count"],
            "likes_count": track_row["likes_count"]
        })

    # 2. Seed Music Channels & Channel Playlists
    for idx, genre in enumerate(channel_genres):
        channel_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"channel-{genre}"))
        channel_code = f"CHN-{500000 + idx}"
        name = f"MelodyMeet {genre} Station"
        lang = random.choices(["English", "Hindi", "Telugu"], weights=[0.4, 0.4, 0.2])[0]
        listeners = random.randint(10, 150)
        followers = random.randint(100, 1200)
        
        channel_row = {
            "id": channel_id,
            "channel_code": channel_code,
            "channel_name": name,
            "language": lang,
            "genre": genre,
            "description": f"Continuous streaming of top {genre} tunes.",
            "logo_url": f"https://example.com/logo/{channel_code}.png",
            "is_active": True,
            "current_listeners": listeners,
            "followers_count": followers,
            "created_at": now_str
        }
        append_to_csv(CHANNELS_CSV_PATH, [
            "id", "channel_code", "channel_name", "language", "genre", "description", "logo_url", "is_active", "current_listeners", "followers_count", "created_at"
        ], [
            channel_row["id"], channel_row["channel_code"], channel_row["channel_name"], channel_row["language"], channel_row["genre"], channel_row["description"],
            channel_row["logo_url"], channel_row["is_active"], channel_row["current_listeners"], channel_row["followers_count"], channel_row["created_at"]
        ])
        send_supabase_post("music_channels", channel_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.music_channels (id, channel_code, channel_name, language, genre, description, logo_url, is_active, current_listeners, followers_count, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (channel_id, channel_code, name, lang, genre, channel_row["description"], channel_row["logo_url"], True, listeners, followers, now_dt)
            )
        active_channels.append({
            "id": channel_id,
            "channel_code": channel_code,
            "name": name,
            "genre": genre,
            "listeners_count": listeners
        })

        # Seed Playlist for this channel
        playlist_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"playlist-{channel_code}"))
        playlist_row = {
            "id": playlist_id,
            "channel_id": channel_id,
            "playlist_name": f"{genre} Master Selection",
            "description": f"Featured tracks selected dynamically for {name}.",
            "is_active": True,
            "created_at": now_str
        }
        append_to_csv(PLAYLISTS_CSV_PATH, [
            "id", "channel_id", "playlist_name", "description", "is_active", "created_at"
        ], [
            playlist_row["id"], playlist_row["channel_id"], playlist_row["playlist_name"], playlist_row["description"], playlist_row["is_active"], playlist_row["created_at"]
        ])
        send_supabase_post("channel_playlists", playlist_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.channel_playlists (id, channel_id, playlist_name, description, is_active, created_at) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (playlist_id, channel_id, playlist_row["playlist_name"], playlist_row["description"], True, now_dt)
            )
        active_playlists.append({
            "id": playlist_id,
            "channel_id": channel_id,
            "name": playlist_row["playlist_name"]
        })

        # Seed playlist tracks maps (3 tracks per playlist)
        selected_tracks = random.sample(active_tracks, 3)
        for pos, trk in enumerate(selected_tracks, start=1):
            pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"playlist-track-{playlist_id}-{trk['id']}"))
            pt_row = {
                "id": pt_id,
                "playlist_id": playlist_id,
                "track_id": trk["id"],
                "position": pos,
                "added_at": now_str
            }
            append_to_csv(PLAYLIST_TRACKS_CSV_PATH, ["id", "playlist_id", "track_id", "position", "added_at"], [
                pt_row["id"], pt_row["playlist_id"], pt_row["track_id"], pt_row["position"], pt_row["added_at"]
            ])
            send_supabase_post("playlist_tracks", pt_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_open.playlist_tracks (id, playlist_id, track_id, position, added_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (pt_id, playlist_id, trk["id"], pos, now_dt)
                )

    print("Channels, Playlists and Playlist Tracks maps initialized.")

def log_user_activity(user_id, activity_type, source_module, entity_id, now_str, now_dt):
    """Write user activities to the central audit log table"""
    act_id = str(uuid.uuid4())
    act_row = {
        "id": act_id,
        "user_id": user_id,
        "activity_type": activity_type,
        "source_module": source_module,
        "entity_id": entity_id,
        "activity_time": now_str
    }
    append_to_csv(USER_ACTIVITY_CSV_PATH, ["id", "user_id", "activity_type", "source_module", "entity_id", "activity_time"], [
        act_row["id"], act_row["user_id"], act_row["activity_type"], act_row["source_module"], act_row["entity_id"], act_row["activity_time"]
    ])
    send_supabase_post("user_activity", act_row)
    if DATABASE_URL and HAS_PG:
        insert_postgres_row(
            "INSERT INTO app_open.user_activity (id, user_id, activity_type, source_module, entity_id, activity_time) VALUES (%s,%s,%s,%s,%s,%s)",
            (act_id, user_id, activity_type, source_module, entity_id, now_dt)
        )

def simulate_step(users):
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    actions = []

    if not active_channels or not active_tracks:
        return actions

    # Choose random channel, track, and user for simulation actions
    channel = random.choice(active_channels)
    track = random.choice(active_tracks)
    user_dict = random.choice(users)
    user_id = user_dict["id"]

    # 1. Action: Current Playing updates (30% chance)
    if random.random() < 0.30:
        cp_id = str(uuid.uuid4())
        cp_row = {
            "id": cp_id,
            "channel_id": channel["id"],
            "track_id": track["id"],
            "started_at": now_str
        }
        append_to_csv(CURRENT_PLAYING_CSV_PATH, ["id", "channel_id", "track_id", "started_at"], [
            cp_row["id"], cp_row["channel_id"], cp_row["track_id"], cp_row["started_at"]
        ])
        send_supabase_post("current_playing", cp_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.current_playing (id, channel_id, track_id, started_at) VALUES (%s,%s,%s,%s)",
                (cp_id, channel["id"], track["id"], now_dt)
            )
        actions.append(f"CURRENTLY PLAYING: Track '{track['title']}' is now live on Station '{channel['name']}'")

    # 2. Action: Listening History log (35% chance)
    if random.random() < 0.35:
        history_id = str(uuid.uuid4())
        hist_row = {
            "id": history_id,
            "user_id": user_id,
            "channel_id": channel["id"],
            "track_id": track["id"],
            "listened_at": now_str
        }
        append_to_csv(HISTORY_CSV_PATH, ["id", "user_id", "channel_id", "track_id", "listened_at"], [
            hist_row["id"], hist_row["user_id"], hist_row["channel_id"], hist_row["track_id"], hist_row["listened_at"]
        ])
        send_supabase_post("listening_history", hist_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.listening_history (id, user_id, channel_id, track_id, listened_at) VALUES (%s,%s,%s,%s,%s)",
                (history_id, user_id, channel["id"], track["id"], now_dt)
            )
        log_user_activity(user_id, "listen_track", "music", track["id"], now_str, now_dt)
        actions.append(f"LISTENING LOG: User {user_id[:8]}... listened to '{track['title']}' on '{channel['name']}'")

    # 3. Action: Music Events (skip/like/play interactions) (30% chance)
    if random.random() < 0.30:
        event_id = str(uuid.uuid4())
        event_type = random.choice(["play", "pause", "skip", "like", "share"])
        
        event_row = {
            "id": event_id,
            "event_type": event_type,
            "channel_id": channel["id"],
            "track_id": track["id"],
            "user_id": user_id,
            "event_time": now_str
        }
        append_to_csv(EVENTS_CSV_PATH, ["id", "event_type", "channel_id", "track_id", "user_id", "event_time"], [
            event_row["id"], event_row["event_type"], event_row["channel_id"], event_row["track_id"], event_row["user_id"], event_row["event_time"]
        ])
        send_supabase_post("music_events", event_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.music_events (id, event_type, channel_id, track_id, user_id, event_time) VALUES (%s,%s,%s,%s,%s,%s)",
                (event_id, event_type, channel["id"], track["id"], user_id, now_dt)
            )
        
        # Increment counts logically
        if event_type == "like":
            track["likes_count"] += 1
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_open.music_tracks SET likes_count = likes_count + 1 WHERE id = %s",
                    (track["id"],)
                )
        elif event_type == "play":
            track["play_count"] += 1
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "UPDATE app_open.music_tracks SET play_count = play_count + 1 WHERE id = %s",
                    (track["id"],)
                )
        
        log_user_activity(user_id, f"trigger_{event_type}", "music", track["id"], now_str, now_dt)
        actions.append(f"INTERACTION EVENT: User {user_id[:8]}... triggered event '{event_type}' on track '{track['title']}'")

    # 4. Action: Favorite Music Channel (15% chance)
    if random.random() < 0.15:
        fav_id = str(uuid.uuid4())
        fav_row = {
            "id": fav_id,
            "user_id": user_id,
            "channel_id": channel["id"],
            "created_at": now_str
        }
        append_to_csv(FAVORITES_CSV_PATH, ["id", "user_id", "channel_id", "created_at"], [
            fav_row["id"], fav_row["user_id"], fav_row["channel_id"], fav_row["created_at"]
        ])
        send_supabase_post("music_favorites", fav_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.music_favorites (id, user_id, channel_id, created_at) VALUES (%s,%s,%s,%s)",
                (fav_id, user_id, channel["id"], now_dt)
            )
        log_user_activity(user_id, "favorite_channel", "music", channel["id"], now_str, now_dt)
        actions.append(f"FAVORITED STATION: User {user_id[:8]}... favorited Station '{channel['name']}'")

    # 5. Action: Music Listener Sessions (30% chance)
    if active_sessions and random.random() < 0.50:
        ended_session = active_sessions.pop(0)
        left_at_str = now_str
        
        session_row_api = {
            "id": ended_session["id"],
            "channel_id": ended_session["channel_id"],
            "user_id": ended_session["user_id"],
            "joined_at": ended_session["joined_at"],
            "left_at": left_at_str
        }
        append_to_csv(SESSIONS_CSV_PATH, ["id", "channel_id", "user_id", "joined_at", "left_at"], [
            ended_session["id"], ended_session["channel_id"], ended_session["user_id"], ended_session["joined_at"], left_at_str
        ])
        send_supabase_post("music_listener_sessions", session_row_api)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "UPDATE app_open.music_listener_sessions SET left_at = %s WHERE id = %s",
                (now_dt, ended_session["id"])
            )
            insert_postgres_row(
                "UPDATE app_open.music_channels SET current_listeners = GREATEST(0, current_listeners - 1) WHERE id = %s",
                (ended_session["channel_id"],)
            )
        log_user_activity(ended_session["user_id"], "leave_session", "music", ended_session["channel_id"], now_str, now_dt)
        actions.append(f"LISTENER LEFT: User {ended_session['user_id'][:8]}... left session on channel {ended_session['channel_id'][:8]}...")
    elif random.random() < 0.30:
        session_id = str(uuid.uuid4())
        session_row = {
            "id": session_id,
            "channel_id": channel["id"],
            "user_id": user_id,
            "joined_at": now_str,
            "left_at": None
        }
        append_to_csv(SESSIONS_CSV_PATH, ["id", "channel_id", "user_id", "joined_at", "left_at"], [
            session_row["id"], session_row["channel_id"], session_row["user_id"], session_row["joined_at"], session_row["left_at"]
        ])
        send_supabase_post("music_listener_sessions", session_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.music_listener_sessions (id, channel_id, user_id, joined_at, left_at) VALUES (%s,%s,%s,%s,%s)",
                (session_id, channel["id"], user_id, now_dt, None)
            )
            insert_postgres_row(
                "UPDATE app_open.music_channels SET current_listeners = current_listeners + 1 WHERE id = %s",
                (channel["id"],)
            )
        
        active_sessions.append({
            "id": session_id,
            "channel_id": channel["id"],
            "user_id": user_id,
            "joined_at": now_str
        })
        log_user_activity(user_id, "join_session", "music", channel["id"], now_str, now_dt)
        actions.append(f"LISTENER JOINED: User {user_id[:8]}... joined Station '{channel['name']}'")

    # 6. Action: Notifications (30% chance)
    if random.random() < 0.30:
        notif_id = str(uuid.uuid4())
        target_user = random.choice(users)["id"]
        notif_type = random.choice(['system', 'music', 'social', 'badge'])
        titles = {
            'system': "System Maintenance",
            'music': "New Track Release!",
            'social': "New Follower Alert",
            'badge': "Badge Earned!"
        }
        messages = {
            'system': "MelodyMeet scheduled updates will roll out tonight at 2 AM UTC.",
            'music': f"Check out the fresh track '{track['title']}' on the station!",
            'social': "Another user has started following your profile. Say hi!",
            'badge': "Splendid! You have earned a new badge. Check your achievements section."
        }
        
        notif_row = {
            "id": notif_id,
            "user_id": target_user,
            "notification_type": notif_type,
            "title": titles[notif_type],
            "message": messages[notif_type],
            "is_read": False,
            "created_at": now_str
        }
        append_to_csv(NOTIFICATIONS_CSV_PATH, ["id", "user_id", "notification_type", "title", "message", "is_read", "created_at"], [
            notif_row["id"], notif_row["user_id"], notif_row["notification_type"], notif_row["title"], notif_row["message"], notif_row["is_read"], notif_row["created_at"]
        ])
        send_supabase_post("notifications", notif_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.notifications (id, user_id, notification_type, title, message, is_read, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (notif_id, target_user, notif_type, titles[notif_type], messages[notif_type], False, now_dt)
            )
        actions.append(f"NOTIFICATION: Sent '{notif_type}' alert to User {target_user[:8]}...")

    # 7. Action: User Badges Awarded (15% chance)
    if random.random() < 0.15:
        ub_id = str(uuid.uuid4())
        target_user = random.choice(users)["id"]
        b_name = random.choice(badges_pool)[0]
        badge_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"badge-{b_name}"))
        
        ub_row = {
            "id": ub_id,
            "user_id": target_user,
            "badge_id": badge_id,
            "earned_at": now_str
        }
        append_to_csv(USER_BADGES_CSV_PATH, ["id", "user_id", "badge_id", "earned_at"], [
            ub_row["id"], ub_row["user_id"], ub_row["badge_id"], ub_row["earned_at"]
        ])
        send_supabase_post("user_badges", ub_row)
        if DATABASE_URL and HAS_PG:
            insert_postgres_row(
                "INSERT INTO app_open.user_badges (id, user_id, badge_id, earned_at) VALUES (%s,%s,%s,%s)",
                (ub_id, target_user, badge_id, now_dt)
            )
        log_user_activity(target_user, "badge_earned", "badge", badge_id, now_str, now_dt)
        actions.append(f"BADGE EARNED: User {target_user[:8]}... earned badge '{b_name}'")

    # 8. Action: User Follows (20% chance)
    if random.random() < 0.20:
        uf_id = str(uuid.uuid4())
        u1 = random.choice(users)["id"]
        u2 = random.choice(users)["id"]
        if u1 != u2:
            uf_row = {
                "id": uf_id,
                "follower_user_id": u1,
                "following_user_id": u2,
                "followed_at": now_str
            }
            append_to_csv(USER_FOLLOWING_CSV_PATH, ["id", "follower_user_id", "following_user_id", "followed_at"], [
                uf_row["id"], uf_row["follower_user_id"], uf_row["following_user_id"], uf_row["followed_at"]
            ])
            send_supabase_post("user_following", uf_row)
            if DATABASE_URL and HAS_PG:
                insert_postgres_row(
                    "INSERT INTO app_open.user_following (id, follower_user_id, following_user_id, followed_at) VALUES (%s,%s,%s,%s)",
                    (uf_id, u1, u2, now_dt)
                )
                # Increment follower count in user_profiles
                profile_u2_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"profile-{u2}"))
                insert_postgres_row(
                    "UPDATE app_open.user_profiles SET followers_count = followers_count + 1 WHERE id = %s",
                    (profile_u2_id,)
                )
            log_user_activity(u1, "follow_user", "social", u2, now_str, now_dt)
            actions.append(f"SOCIAL FOLLOW: User {u1[:8]}... started following User {u2[:8]}...")

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
    print("        MELODYMEET MUSIC OPEN MODULE LIVE DATA SIMULATOR")
    print("=" * 60)
    
    users = load_user_pool()
    
    # Pre-seed metadata and config tables
    seed_static_tables(users)
    seed_initial_music_catalogs()
    
    if DATABASE_URL:
        if HAS_PG:
            print("[INFO] PostgreSQL connection active.")
        else:
            print("[WARNING] DATABASE_URL detected, but 'psycopg2' is not installed. Defaulting to local CSV & Supabase REST API.")
            
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API target active.")
        
    print("[INFO] CSV Mode: Enabled (Appends to music_*_mock_data.csv and associated tables)")
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
