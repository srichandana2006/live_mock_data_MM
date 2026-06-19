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

# CSV File Paths
PODCASTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcasts_mock_data.csv")
EPISODES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_episodes_mock_data.csv")
FOLLOWERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_followers_mock_data.csv")
LIKES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_likes_mock_data.csv")
COMMENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_comments_mock_data.csv")
SHARES_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_shares_mock_data.csv")
BOOKMARKS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_bookmarks_mock_data.csv")
SESSIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_listener_sessions_mock_data.csv")
COMPLETION_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_completion_mock_data.csv")
EVENTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "podcast_events_mock_data.csv")
LIVE_SESS_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_sessions_mock_data.csv")
LIVE_LIST_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_listeners_mock_data.csv")
LIVE_CHAT_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_chat_mock_data.csv")
LIVE_QUEST_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_questions_mock_data.csv")
LIVE_REACT_CSV_PATH = os.path.join(WORKSPACE_DIR, "live_podcast_reactions_mock_data.csv")
REPORTS_CSV_PATH = os.path.join(WORKSPACE_DIR, "content_reports_mock_data.csv")
ASSIGN_CSV_PATH = os.path.join(WORKSPACE_DIR, "operator_assignments_mock_data.csv")
FLAGGED_CSV_PATH = os.path.join(WORKSPACE_DIR, "flagged_content_mock_data.csv")
ANALYTICS_CSV_PATH = os.path.join(WORKSPACE_DIR, "listener_analytics_mock_data.csv")
ROOMS_CSV_PATH = os.path.join(WORKSPACE_DIR, "room_participants_mock_data.csv")
CHANNELS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_channels_mock_data.csv")

# New CSV File Paths for tables 22 to 32
OPERATORS_CSV_PATH = os.path.join(WORKSPACE_DIR, "operators_mock_data.csv")
AUDIT_LOGS_CSV_PATH = os.path.join(WORKSPACE_DIR, "audit_logs_mock_data.csv")
REPORTS_CSV_PATH_NEW = os.path.join(WORKSPACE_DIR, "reports_mock_data.csv")
MOD_ACTIONS_CSV_PATH = os.path.join(WORKSPACE_DIR, "moderation_actions_mock_data.csv")
RJS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rjs_mock_data.csv")
RJ_SHOWS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_live_shows_mock_data.csv")
RJ_CHAT_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_chat_messages_mock_data.csv")
RJ_FOLLOWERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_followers_mock_data.csv")
RJ_LISTENER_SESS_CSV_PATH = os.path.join(WORKSPACE_DIR, "rj_listener_sessions_mock_data.csv")
SONG_REQ_CSV_PATH = os.path.join(WORKSPACE_DIR, "song_requests_mock_data.csv")
SONG_LIKES_CSV_PATH = os.path.join(WORKSPACE_DIR, "song_likes_mock_data.csv")

# Simulator settings
TICK_INTERVAL = 5.0

# Database / Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

# Fallback credentials
if not SUPABASE_URL:
    SUPABASE_URL = "https://ehhludmyveoixzknqwnt.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVoaGx1ZG15dmVvaXh6a25xd250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1NjIyOTQsImV4cCI6MjA5NzEzODI5NH0.2zVm9zF1CA9SDwUvTUiXSE4fiN5adqFL4Sg29a6W1TE"

# Seed data pools
podcast_titles = ["The Daily Rhythm", "Tech Bytes & Beats", "Echoes of Eternity", "Laugh Track Live", "Mindset Matters", "Science Decoded", "History Reimagined", "Indie Creator Spotlight"]
hosts = ["Dr. Ramesh Kumar", "Samantha Rogers", "Aditya Reddy", "Vikram Sen", "Priya Nair", "Sarah Jenkins", "Michael Chang", "Kabir Sharma"]
languages = ["English", "Hindi", "Telugu", "Tamil", "Spanish", "German"]
categories = ["music", "technology", "education", "comedy", "science", "history", "business"]
platforms = ["whatsapp", "instagram", "twitter", "facebook"]
event_types = ["play", "pause", "resume", "skip", "complete"]
reaction_types = ["like", "heart", "clap", "fire"]
report_reasons = ["Inappropriate content", "Spam", "Copyright violation", "Harassment", "Hate speech"]
flag_reasons = ["Automated profanity detection", "Copyright audio mismatch", "Spam pattern detected"]
chat_messages = ["Wow, cool stream!", "Loving this talk show.", "Can we request a song?", "Absolutely amazing session!", "Yes, so informative.", "Hello from Hyderabad!", "Nice to meet everyone here.", "Fire stream! 🔥", "Host is outstanding! 🙌"]
questions_pool = ["What got you started in podcasting?", "What advice do you have for beginners?", "How do you choose your weekly topics?", "Can we expect guests on this show soon?", "How long does editing typically take you?"]

# Pools to preserve relations between ticks
active_podcasts = []
active_episodes = []
active_sessions = []       # podcast listener sessions
active_live_sessions = []  # live broadcasts
active_live_listeners = [] # live session listeners
active_reports = []
active_channels = []

# Pools for tables 22 to 32
active_operators = []
active_rjs = []
active_rj_shows = []
active_rj_listener_sessions = []
active_user_reports = []


def load_user_pool():
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

def generate_code(prefix):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return f"{prefix}-" + "".join(random.choice(chars) for _ in range(6))

def append_to_csv(filepath, headers, data):
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)

def send_supabase_post(table_name, payload):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
        "Accept-Profile": "app_operator",
        "Content-Profile": "app_operator"
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

def simulate_step(users):
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    actions = []

    # 1. Action: Create a Podcast (15% chance, or if pool < 2)
    if random.random() < 0.15 or len(active_podcasts) < 2:
        podcast_id = str(uuid.uuid4())
        title = random.choice(podcast_titles) + " with " + random.choice(hosts).split()[-1]
        host = random.choice(hosts)
        lang = random.choice(languages)
        cat = random.choice(categories)
        pcode = generate_code("POD")
        desc = f"Welcome to {title}. Join us weekly as we explore topics in {cat}."
        
        podcast_row = {
            "id": podcast_id,
            "podcast_code": pcode,
            "title": title,
            "host_name": host,
            "language": lang,
            "category": cat,
            "description": desc,
            "followers_count": random.randint(10, 500),
            "total_plays": random.randint(100, 5000),
            "created_at": now_str
        }
        append_to_csv(PODCASTS_CSV_PATH, ["id", "podcast_code", "title", "host_name", "language", "category", "description", "followers_count", "total_plays", "created_at"], list(podcast_row.values()))
        send_supabase_post("podcasts", podcast_row)
        active_podcasts.append(podcast_row)
        actions.append(f"PODCAST CREATED: '{title}' ({pcode})")

    # 2. Action: Create an Episode (25% chance, if podcasts exist)
    if active_podcasts and (random.random() < 0.25 or len(active_episodes) < 3):
        podcast = random.choice(active_podcasts)
        episode_id = str(uuid.uuid4())
        ep_num = random.randint(1, 50)
        ep_title = f"Episode #{ep_num}: " + random.choice(["The Future of music", "Navigating the Unknown", "Expert Panel Discussion", "A Deep Dive", "Rhythm & Harmony"])
        duration = random.randint(300, 3600)
        audio = f"https://streaming.melodymet.com/podcasts/{podcast['podcast_code'].lower()}/{episode_id}.mp3"
        
        ep_row = {
            "id": episode_id,
            "podcast_id": podcast["id"],
            "episode_title": ep_title,
            "duration_seconds": duration,
            "audio_url": audio,
            "play_count": random.randint(5, 100),
            "created_at": now_str
        }
        append_to_csv(EPISODES_CSV_PATH, ["id", "podcast_id", "episode_title", "duration_seconds", "audio_url", "play_count", "created_at"], list(ep_row.values()))
        send_supabase_post("podcast_episodes", ep_row)
        active_episodes.append(ep_row)
        actions.append(f"EPISODE PUBLISHED: '{ep_title}' in Podcast '{podcast['title']}'")

    # 3. Action: Podcast Follower (15% chance)
    if active_podcasts and random.random() < 0.15:
        podcast = random.choice(active_podcasts)
        user_id = random.choice(users)
        follow_id = str(uuid.uuid4())
        follow_row = {"id": follow_id, "podcast_id": podcast["id"], "user_id": user_id, "followed_at": now_str}
        append_to_csv(FOLLOWERS_CSV_PATH, list(follow_row.keys()), list(follow_row.values()))
        send_supabase_post("podcast_followers", follow_row)
        actions.append(f"USER FOLLOWED: User {user_id[:8]}... followed podcast '{podcast['title']}'")

    # 4. Action: Podcast Likes (20% chance)
    if active_episodes and random.random() < 0.20:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        like_id = str(uuid.uuid4())
        like_row = {"id": like_id, "podcast_id": ep["podcast_id"], "episode_id": ep["id"], "user_id": user_id, "created_at": now_str}
        append_to_csv(LIKES_CSV_PATH, list(like_row.keys()), list(like_row.values()))
        send_supabase_post("podcast_likes", like_row)
        actions.append(f"EPISODE LIKED: User {user_id[:8]}... liked episode '{ep['episode_title']}'")

    # 5. Action: Podcast Comments (20% chance)
    if active_episodes and random.random() < 0.20:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        comment_id = str(uuid.uuid4())
        text = random.choice(chat_messages)
        comment_row = {"id": comment_id, "podcast_id": ep["podcast_id"], "episode_id": ep["id"], "user_id": user_id, "comment": text, "created_at": now_str}
        append_to_csv(COMMENTS_CSV_PATH, list(comment_row.keys()), list(comment_row.values()))
        send_supabase_post("podcast_comments", comment_row)
        actions.append(f"COMMENT POSTED: User {user_id[:8]}... commented on '{ep['episode_title']}'")

    # 6. Action: Podcast Shares (15% chance)
    if active_episodes and random.random() < 0.15:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        share_id = str(uuid.uuid4())
        plat = random.choice(platforms)
        share_row = {"id": share_id, "podcast_id": ep["podcast_id"], "episode_id": ep["id"], "user_id": user_id, "platform": plat, "created_at": now_str}
        append_to_csv(SHARES_CSV_PATH, list(share_row.keys()), list(share_row.values()))
        send_supabase_post("podcast_shares", share_row)
        actions.append(f"EPISODE SHARED: User {user_id[:8]}... shared on {plat}")

    # 7. Action: Podcast Bookmarks (15% chance)
    if active_episodes and random.random() < 0.15:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        bookmark_id = str(uuid.uuid4())
        bookmark_row = {"id": bookmark_id, "user_id": user_id, "episode_id": ep["id"], "bookmarked_at": now_str}
        append_to_csv(BOOKMARKS_CSV_PATH, list(bookmark_row.keys()), list(bookmark_row.values()))
        send_supabase_post("podcast_bookmarks", bookmark_row)
        actions.append(f"EPISODE BOOKMARKED: User {user_id[:8]}... bookmarked episode")

    # 8. Action: Listener Session Start (20% chance)
    if active_episodes and random.random() < 0.20:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        session_id = str(uuid.uuid4())
        session_row = {"id": session_id, "podcast_id": ep["podcast_id"], "episode_id": ep["id"], "user_id": user_id, "joined_at": now_str, "left_at": None}
        append_to_csv(SESSIONS_CSV_PATH, list(session_row.keys()), list(session_row.values()))
        send_supabase_post("podcast_listener_sessions", session_row)
        active_sessions.append({
            "id": session_id,
            "podcast_id": ep["podcast_id"],
            "episode_id": ep["id"],
            "user_id": user_id,
            "joined_at_dt": now_dt,
            "joined_at_str": now_str
        })
        actions.append(f"LISTENER SESSION STARTED: User {user_id[:8]}... started listening")

    # 9. Action: Listener Session End & Completion (50% chance)
    if active_sessions and random.random() < 0.50:
        ended_sess = active_sessions.pop(0)
        percentage = round(random.uniform(10.0, 100.0), 2)
        end_session_row = {"id": ended_sess["id"], "podcast_id": ended_sess["podcast_id"], "episode_id": ended_sess["episode_id"], "user_id": ended_sess["user_id"], "joined_at": ended_sess["joined_at_str"], "left_at": now_str}
        append_to_csv(SESSIONS_CSV_PATH, list(end_session_row.keys()), list(end_session_row.values()))
        send_supabase_post("podcast_listener_sessions", end_session_row)
        
        comp_id = str(uuid.uuid4())
        comp_row = {"id": comp_id, "user_id": ended_sess["user_id"], "episode_id": ended_sess["episode_id"], "percentage_completed": percentage, "completed_at": now_str}
        append_to_csv(COMPLETION_CSV_PATH, list(comp_row.keys()), list(comp_row.values()))
        send_supabase_post("podcast_completion", comp_row)
        actions.append(f"SESSION ENDED & COMPLETED: User completed {percentage}% of episode")

    # 10. Action: Telemetry Events (40% chance)
    if active_episodes and random.random() < 0.40:
        ep = random.choice(active_episodes)
        user_id = random.choice(users)
        event_id = str(uuid.uuid4())
        etype = random.choice(event_types)
        event_row = {"id": event_id, "event_type": etype, "podcast_id": ep["podcast_id"], "episode_id": ep["id"], "user_id": user_id, "event_time": now_str}
        append_to_csv(EVENTS_CSV_PATH, list(event_row.keys()), list(event_row.values()))
        send_supabase_post("podcast_events", event_row)
        actions.append(f"TELEMETRY EVENT: User triggered '{etype}' on episode")

    # 11. Action: Create Live Podcast Session (15% chance)
    if active_podcasts and random.random() < 0.15:
        podcast = random.choice(active_podcasts)
        sess_id = str(uuid.uuid4())
        title = f"Live: Discussing {podcast['title']}"
        desc = "Interactive Q&A live broadcast with listeners."
        sched = (now_dt - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(["scheduled", "live", "completed", "cancelled"])
        
        sess_row = {
            "id": sess_id,
            "podcast_id": podcast["id"],
            "host_name": podcast["host_name"],
            "title": title,
            "description": desc,
            "scheduled_start": sched,
            "actual_start": now_str,
            "actual_end": None,
            "status": status,
            "current_listeners": random.randint(5, 80) if status == "live" else 0,
            "created_at": now_str
        }
        append_to_csv(LIVE_SESS_CSV_PATH, list(sess_row.keys()), list(sess_row.values()))
        send_supabase_post("live_podcast_sessions", sess_row)
        active_live_sessions.append(sess_row)
        actions.append(f"LIVE BROADCAST SESSION: Host '{podcast['host_name']}' created session '{title}' (Status: {status})")

    # 12. Action: Live Podcast Listener Join (20% chance)
    if active_live_sessions and random.random() < 0.20:
        sess = random.choice(active_live_sessions)
        user_id = random.choice(users)
        list_id = str(uuid.uuid4())
        
        list_row = {
            "id": list_id,
            "session_id": sess["id"],
            "user_id": user_id,
            "joined_at": now_str,
            "left_at": None
        }
        append_to_csv(LIVE_LIST_CSV_PATH, list(list_row.keys()), list(list_row.values()))
        send_supabase_post("live_podcast_listeners", list_row)
        active_live_listeners.append(list_row)
        actions.append(f"LIVE LISTENER JOINED: User {user_id[:8]}... joined Live Session")

    # 13. Action: Live Chat Message (35% chance)
    if active_live_sessions and random.random() < 0.35:
        sess = random.choice(active_live_sessions)
        user_id = random.choice(users)
        chat_id = str(uuid.uuid4())
        msg = random.choice(chat_messages)
        
        chat_row = {
            "id": chat_id,
            "session_id": sess["id"],
            "user_id": user_id,
            "message": msg,
            "created_at": now_str
        }
        append_to_csv(LIVE_CHAT_CSV_PATH, list(chat_row.keys()), list(chat_row.values()))
        send_supabase_post("live_podcast_chat", chat_row)
        actions.append(f"LIVE CHAT MESSAGE: User {user_id[:8]}... sent: '{msg[:15]}...'")

    # 14. Action: Live Question Submission (20% chance)
    if active_live_sessions and random.random() < 0.20:
        sess = random.choice(active_live_sessions)
        user_id = random.choice(users)
        quest_id = str(uuid.uuid4())
        quest = random.choice(questions_pool)
        status = random.choice(["pending", "answered", "rejected"])
        
        quest_row = {
            "id": quest_id,
            "session_id": sess["id"],
            "user_id": user_id,
            "question": quest,
            "status": status,
            "created_at": now_str
        }
        append_to_csv(LIVE_QUEST_CSV_PATH, list(quest_row.keys()), list(quest_row.values()))
        send_supabase_post("live_podcast_questions", quest_row)
        actions.append(f"LIVE QUESTION: User {user_id[:8]}... asked a question (Status: {status})")

    # 15. Action: Live Reaction (30% chance)
    if active_live_sessions and random.random() < 0.30:
        sess = random.choice(active_live_sessions)
        user_id = random.choice(users)
        react_id = str(uuid.uuid4())
        react = random.choice(reaction_types)
        
        react_row = {
            "id": react_id,
            "session_id": sess["id"],
            "user_id": user_id,
            "reaction_type": react,
            "created_at": now_str
        }
        append_to_csv(LIVE_REACT_CSV_PATH, list(react_row.keys()), list(react_row.values()))
        send_supabase_post("live_podcast_reactions", react_row)
        actions.append(f"LIVE REACTION: User {user_id[:8]}... reacted with '{react}'")

    # 16. Action: Content Reports (10% chance)
    if active_podcasts and random.random() < 0.10:
        podcast = random.choice(active_podcasts)
        reported_by = random.choice(users)
        rep_id = str(uuid.uuid4())
        reason = random.choice(report_reasons)
        priority = random.choice(["low", "medium", "high", "critical"])
        status = random.choice(["pending", "under_investigation", "resolved"])
        
        rep_row = {
            "id": rep_id,
            "content_type": "podcast",
            "content_id": podcast["id"],
            "reported_by": reported_by,
            "reason": reason,
            "priority": priority,
            "status": status,
            "created_at": now_str,
            "resolved_at": now_str if status == "resolved" else None
        }
        append_to_csv(REPORTS_CSV_PATH, list(rep_row.keys()), list(rep_row.values()))
        send_supabase_post("content_reports", rep_row)
        active_reports.append(rep_row)
        actions.append(f"CONTENT REPORTED: Podcast '{podcast['title']}' flagged for: '{reason}'")

    # 17. Action: Operator Assignment (15% chance, if active reports exist)
    if active_reports and random.random() < 0.15:
        rep = random.choice(active_reports)
        op_id = str(uuid.uuid4())
        assign_id = str(uuid.uuid4())
        status = random.choice(["assigned", "in_review", "resolved"])
        
        assign_row = {
            "id": assign_id,
            "operator_id": op_id,
            "report_id": rep["id"],
            "status": status,
            "assigned_at": now_str
        }
        append_to_csv(ASSIGN_CSV_PATH, list(assign_row.keys()), list(assign_row.values()))
        send_supabase_post("operator_assignments", assign_row)
        actions.append(f"OPERATOR ASSIGNMENT: Report assigned to operator {op_id[:8]}... (Status: {status})")

    # 18. Action: Automated Flagged Content (10% chance)
    if active_episodes and random.random() < 0.10:
        ep = random.choice(active_episodes)
        flag_id = str(uuid.uuid4())
        reason = random.choice(flag_reasons)
        status = random.choice(["flagged", "approved", "removed"])
        
        flag_row = {
            "id": flag_id,
            "content_type": "episode",
            "content_id": ep["id"],
            "flag_reason": reason,
            "status": status,
            "created_at": now_str
        }
        append_to_csv(FLAGGED_CSV_PATH, list(flag_row.keys()), list(flag_row.values()))
        send_supabase_post("flagged_content", flag_row)
        actions.append(f"AUTOMATED FLAG: Episode '{ep['episode_title']}' flagged automatically: '{reason}'")

    # 19. Action: Listener Analytics (15% chance)
    if active_podcasts and random.random() < 0.15:
        podcast = random.choice(active_podcasts)
        analytics_id = str(uuid.uuid4())
        lcount = random.randint(10, 1000)
        pcount = lcount + random.randint(10, 300)
        dur = random.randint(10, 200) * 10
        
        analytics_row = {
            "id": analytics_id,
            "content_type": "podcast",
            "content_id": podcast["id"],
            "listener_count": lcount,
            "peak_listener_count": pcount,
            "session_duration": dur,
            "recorded_at": now_str
        }
        append_to_csv(ANALYTICS_CSV_PATH, list(analytics_row.keys()), list(analytics_row.values()))
        send_supabase_post("listener_analytics", analytics_row)
        actions.append(f"ANALYTICS RECORDED: Aggregated metrics saved for '{podcast['title']}'")

    # 20. Action: Room Participants (15% chance)
    if random.random() < 0.15:
        room_id = str(uuid.uuid4())
        user_id = random.choice(users)
        part_id = str(uuid.uuid4())
        
        part_row = {
            "id": part_id,
            "room_id": room_id,
            "user_id": user_id,
            "joined_at": now_str,
            "left_at": None
        }
        append_to_csv(ROOMS_CSV_PATH, list(part_row.keys()), list(part_row.values()))
        send_supabase_post("room_participants", part_row)
        actions.append(f"ROOM PARTICIPANT: User {user_id[:8]}... joined live room")

    # 21. Action: RJ Radio Channel Setup (15% chance)
    if random.random() < 0.15 or len(active_channels) < 1:
        chan_id = str(uuid.uuid4())
        rj_id = str(uuid.uuid4())
        ccode = generate_code("RJ")
        cname = f"MelodyMeet RJ {random.choice(hosts).split()[-1]} Show"
        lang = random.choice(languages)
        cat = random.choice(["music", "talk_show", "news", "entertainment"])
        
        chan_row = {
            "id": chan_id,
            "channel_code": ccode,
            "rj_id": rj_id,
            "channel_name": cname,
            "language": lang,
            "category": cat,
            "is_live": random.choice([True, False]),
            "current_listeners": random.randint(20, 200),
            "created_at": now_str
        }
        append_to_csv(CHANNELS_CSV_PATH, list(chan_row.keys()), list(chan_row.values()))
        send_supabase_post("rj_channels", chan_row)
        active_channels.append(chan_row)
        actions.append(f"RJ RADIO CHANNEL: Channel '{cname}' ({ccode}) created/updated (Language: {lang})")

    # 22. Action: Operator Registration (10% chance)
    if random.random() < 0.10 or len(active_operators) < 2:
        op_id = str(uuid.uuid4())
        name = "Operator " + random.choice(["Dave", "Alice", "Bob", "Eve", "Frank"]) + " " + str(random.randint(1, 100))
        email = name.lower().replace(" ", "") + "@melodymet.com"
        role = random.choice(['admin', 'moderator', 'reviewer', 'support'])
        status = random.choice(['active', 'inactive', 'suspended'])
        content_type = random.choice(['podcasts', 'rj_channels', 'live_rooms', 'reports'])
        
        op_row = {
            "id": op_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": now_str,
            "status": status,
            "last_login": now_str,
            "assigned_content_type": content_type,
            "updated_at": now_str
        }
        append_to_csv(OPERATORS_CSV_PATH, list(op_row.keys()), list(op_row.values()))
        send_supabase_post("operators", op_row)
        active_operators.append(op_row)
        actions.append(f"OPERATOR CREATED: {name} (Role: {role})")

    # 23. Action: Audit Log Entry (15% chance)
    if active_operators and random.random() < 0.15:
        op = random.choice(active_operators)
        audit_id = str(uuid.uuid4())
        audit_action = random.choice(['Suspended user account', 'Approved flagged episode', 'Removed inappropriate comment', 'Reviewed content report', 'Assigned moderator priority'])
        record_id = str(uuid.uuid4())
        
        audit_row = {
            "id": audit_id,
            "operator_id": op["id"],
            "action": audit_action,
            "created_at": now_str,
            "record_id": record_id
        }
        append_to_csv(AUDIT_LOGS_CSV_PATH, list(audit_row.keys()), list(audit_row.values()))
        send_supabase_post("audit_logs", audit_row)
        actions.append(f"AUDIT LOG: Operator {op['name']} performed action '{audit_action}'")

    # 24. Action: User Report Submission (15% chance)
    if random.random() < 0.15 or len(active_user_reports) < 2:
        rep_id = str(uuid.uuid4())
        reported_user = random.choice(users)
        reported_by = random.choice(users)
        reason = random.choice(['Harassment', 'Hate speech', 'Spamming chat', 'Offensive username', 'Inappropriate profile picture'])
        status = random.choice(['pending', 'under_review', 'resolved', 'dismissed'])
        
        rep_row = {
            "id": rep_id,
            "reported_user_id": reported_user,
            "reported_by_user_id": reported_by,
            "reason": reason,
            "status": status,
            "created_at": now_str
        }
        append_to_csv(REPORTS_CSV_PATH_NEW, list(rep_row.keys()), list(rep_row.values()))
        send_supabase_post("reports", rep_row)
        active_user_reports.append(rep_row)
        actions.append(f"REPORT SUBMITTED: User {reported_by[:8]}... reported User {reported_user[:8]}... (Reason: {reason})")

    # 25. Action: Moderation Action Execution (15% chance)
    if active_operators and random.random() < 0.15:
        op = random.choice(active_operators)
        action_id = str(uuid.uuid4())
        target_user = random.choice(users)
        atype = random.choice(['warning', 'mute', 'ban', 'suspend', 'content_removal'])
        reason = f"Enforced standard protocols for {atype}."
        
        mod_row = {
            "id": action_id,
            "operator_id": op["id"],
            "target_user_id": target_user,
            "action_type": atype,
            "created_at": now_str,
            "reason": reason
        }
        append_to_csv(MOD_ACTIONS_CSV_PATH, list(mod_row.keys()), list(mod_row.values()))
        send_supabase_post("moderation_actions", mod_row)
        actions.append(f"MODERATION ACTION: Operator {op['name']} applied '{atype}' on user {target_user[:8]}...")

    # 26. Action: RJ Registration (10% chance)
    if random.random() < 0.10 or len(active_rjs) < 2:
        rj_id = str(uuid.uuid4())
        stage_name = "RJ " + random.choice(["Rishi", "Rohini", "Kartik", "Ananya", "Dev"]) + " " + str(random.randint(1, 100))
        full_name = stage_name.replace("RJ ", "") + " Kumar"
        rj_code = generate_code("RJ")
        email = stage_name.lower().replace(" ", "") + "@melodymet.com"
        lang = random.choice(languages)
        state = random.choice(['Maharashtra', 'Telangana', 'Karnataka', 'Tamil Nadu', 'Delhi'])
        cat = random.choice(['music', 'talk_show', 'comedy', 'news'])
        
        rj_row = {
            "id": rj_id,
            "rj_code": rj_code,
            "full_name": full_name,
            "stage_name": stage_name,
            "email": email,
            "language": lang,
            "state": state,
            "country": "India",
            "category": cat,
            "profile_image": f"https://images.melodymet.com/rjs/{rj_code.lower()}.png",
            "followers_count": random.randint(50, 1000),
            "total_listeners": random.randint(1000, 50000),
            "total_shows": random.randint(5, 100),
            "is_active": True,
            "created_at": now_str
        }
        append_to_csv(RJS_CSV_PATH, list(rj_row.keys()), list(rj_row.values()))
        send_supabase_post("rjs", rj_row)
        active_rjs.append(rj_row)
        actions.append(f"RJ REGISTERED: {stage_name} (Code: {rj_code})")

    # 27. Action: RJ Live Show Schedule/Start (15% chance)
    if active_channels and (random.random() < 0.15 or len(active_rj_shows) < 1):
        chan = random.choice(active_channels)
        show_id = str(uuid.uuid4())
        show_name = random.choice(["Morning Beats", "Midnight Melodies", "Chai & Talk", "Retro Rewind", "Rock Block"]) + f" with {chan['channel_name'].split()[-2]}"
        desc = f"Catch the latest trends and tracks live on {show_name}."
        sched_start = now_str
        sched_end = (now_dt + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(['scheduled', 'live', 'completed', 'cancelled'])
        
        show_row = {
            "id": show_id,
            "channel_id": chan["id"],
            "show_name": show_name,
            "description": desc,
            "scheduled_start": sched_start,
            "scheduled_end": sched_end,
            "actual_start": now_str if status in ('live', 'completed') else None,
            "actual_end": now_str if status == 'completed' else None,
            "status": status
        }
        append_to_csv(RJ_SHOWS_CSV_PATH, list(show_row.keys()), list(show_row.values()))
        send_supabase_post("rj_live_shows", show_row)
        active_rj_shows.append(show_row)
        actions.append(f"RJ LIVE SHOW: '{show_name}' status updated to '{status}'")

    # 28. Action: RJ Chat Message (30% chance)
    if active_rj_shows and random.random() < 0.30:
        live_show = random.choice(active_rj_shows)
        msg_id = str(uuid.uuid4())
        username = "User_" + str(random.randint(100, 999))
        message = random.choice(["Hello RJ!", "Awesome track playing!", "Loving the show!", "Best evening ever!", "Please play my request!"])
        
        msg_row = {
            "id": msg_id,
            "show_id": live_show["id"],
            "username": username,
            "message": message,
            "created_at": now_str
        }
        append_to_csv(RJ_CHAT_CSV_PATH, list(msg_row.keys()), list(msg_row.values()))
        send_supabase_post("rj_chat_messages", msg_row)
        actions.append(f"RJ SHOW CHAT MESSAGE: '{username}' sent: '{message}'")

    # 29. Action: RJ Follower Action (15% chance)
    if active_rjs and random.random() < 0.15:
        rj = random.choice(active_rjs)
        user_id = random.choice(users)
        follow_id = str(uuid.uuid4())
        
        follow_row = {
            "id": follow_id,
            "rj_id": rj["id"],
            "user_id": user_id,
            "followed_at": now_str
        }
        append_to_csv(RJ_FOLLOWERS_CSV_PATH, list(follow_row.keys()), list(follow_row.values()))
        send_supabase_post("rj_followers", follow_row)
        actions.append(f"RJ FOLLOWED: User {user_id[:8]}... followed {rj['stage_name']}")

    # 30. Action: RJ Listener Session (15% chance)
    if active_rj_shows and random.random() < 0.15:
        show = random.choice(active_rj_shows)
        user_id = random.choice(users)
        session_id = str(uuid.uuid4())
        
        session_row = {
            "id": session_id,
            "show_id": show["id"],
            "user_id": user_id,
            "joined_at": now_str,
            "left_at": None
        }
        append_to_csv(RJ_LISTENER_SESS_CSV_PATH, list(session_row.keys()), list(session_row.values()))
        send_supabase_post("rj_listener_sessions", session_row)
        active_rj_listener_sessions.append(session_row)
        actions.append(f"RJ LISTENER JOINED: User {user_id[:8]}... joined RJ show '{show['show_name']}'")

    # 31. Action: RJ Song Request (20% chance)
    if active_rj_shows and random.random() < 0.20:
        show = random.choice(active_rj_shows)
        req_id = str(uuid.uuid4())
        listener = "Listener_" + str(random.randint(100, 999))
        song = random.choice(["Zara Zara", "Kesaria", "Naatu Naatu", "Butta Bomma", "Tum Hi Ho"])
        artist = random.choice(["Bombay Jayashri", "Arijit Singh", "Rahul Sipligunj", "Armaan Malik", "Arijit Singh"])
        msg = "Please play this song for my friends!"
        status = random.choice(['pending', 'accepted', 'played', 'rejected', 'skipped'])
        
        req_row = {
            "id": req_id,
            "show_id": show["id"],
            "listener_name": listener,
            "song_name": song,
            "artist_name": artist,
            "request_message": msg,
            "status": status,
            "created_at": now_str
        }
        append_to_csv(SONG_REQ_CSV_PATH, list(req_row.keys()), list(req_row.values()))
        send_supabase_post("song_requests", req_row)
        actions.append(f"SONG REQUEST SUBMITTED: '{listener}' requested '{song}' by '{artist}' (Status: {status})")

    # 32. Action: RJ Song Like (20% chance)
    if random.random() < 0.20:
        user_id = random.choice(users)
        track_id = str(uuid.uuid4())
        like_id = str(uuid.uuid4())
        
        like_row = {
            "id": like_id,
            "user_id": user_id,
            "track_id": track_id,
            "created_at": now_str
        }
        append_to_csv(SONG_LIKES_CSV_PATH, list(like_row.keys()), list(like_row.values()))
        send_supabase_post("song_likes", like_row)
        actions.append(f"SONG LIKED: User {user_id[:8]}... liked track {track_id[:8]}...")

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
    print("        MELODYMEET PODCASTS & OPERATOR MODULE LIVE DATA SIMULATOR")
    print("=" * 60)
    
    users = load_user_pool()
    
    if SUPABASE_URL and SUPABASE_KEY:
        print("[INFO] Supabase API target active.")
        
    print(f"[INFO] CSV Mode: Enabled (Appends to complete operator mock files)")
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
