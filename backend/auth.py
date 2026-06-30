"""
auth.py — Off The Mic
Supabase authentication + OTP verification via Brevo email.
"""

import random
import string
import smtplib
import hashlib
import os
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# Load .env file if it exists (for local development)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# ── SUPABASE CONFIG ────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vexxudgibkjgitixqgjg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_xcM6lUmOJadOW-9_eXNzRg_Knc-ffbP")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── EMAIL CONFIG (Brevo) ───────────────────────────────────────
SMTP_EMAIL    = os.environ.get("OTM_EMAIL", "nikhila2601@gmail.com")
SMTP_PASSWORD = os.environ.get("OTM_EMAIL_PASS", "your_brevo_smtp_key")
SMTP_HOST     = "smtp-relay.brevo.com"
SMTP_PORT     = 587

OTP_EXPIRY_MINUTES = 10


# ── HELPERS ────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def _send_otp_email(to_email: str, otp: str, display_name: str = "") -> bool:
    if SMTP_PASSWORD == "your_brevo_smtp_key":
        print(f"\n{'='*40}")
        print(f"  OTP for {to_email}: {otp}")
        print(f"  (Email not configured — dev mode)")
        print(f"{'='*40}\n")
        return True

    greeting  = f"Hi {display_name}," if display_name else "Hi,"
    html_body = f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:480px;
                margin:0 auto;background:#FAF7F2;border-radius:16px;
                padding:40px 36px;color:#2F463B;">
      <h1 style="font-size:28px;margin:0 0 4px;">Off The Mic</h1>
      <p style="color:#A8B5A2;font-size:13px;margin:0 0 32px;">
        practice a little, speak a lot.
      </p>
      <p style="font-size:15px;margin:0 0 24px;">{greeting}</p>
      <p style="font-size:15px;margin:0 0 24px;">
        Here is your one-time login code:
      </p>
      <div style="background:#FFFDF9;border:1px solid #E8E2D9;border-radius:12px;
                  padding:28px;text-align:center;margin:0 0 24px;">
        <span style="font-size:48px;font-weight:700;letter-spacing:12px;
                     color:#2F463B;">{otp}</span>
      </div>
      <p style="font-size:13px;color:#A8B5A2;margin:0;">
        This code expires in {OTP_EXPIRY_MINUTES} minutes.<br>
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """
    text_body = f"{greeting}\n\nYour Off The Mic login code is: {otp}\n\nExpires in {OTP_EXPIRY_MINUTES} minutes."

    # 1. Try sending via Brevo HTTP API (Port 443 - not blocked by firewalls)
    api_key = os.environ.get("BREVO_API_KEY") or SMTP_PASSWORD
    if api_key and api_key != "your_brevo_smtp_key":
        import requests
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            payload = {
                "sender": {"name": "Off The Mic", "email": SMTP_EMAIL},
                "to": [{"email": to_email, "name": display_name or to_email}],
                "subject": "Your Off The Mic login code",
                "htmlContent": html_body
            }
            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code in (200, 201, 202):
                print("[EMAIL] Successfully sent via Brevo HTTP API")
                return True
            else:
                print(f"[EMAIL HTTP API FAILED] Status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[EMAIL HTTP API ERROR] {e}")

    # 2. Try sending via Standard SMTP (Port 587 - fallback)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Off The Mic login code"
        msg["From"]    = f"Off The Mic <{SMTP_EMAIL}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        print("[EMAIL] Successfully sent via SMTP relay")
        return True

    except Exception as e:
        print(f"[EMAIL SMTP ERROR] {e}")
        return False


# ── SIGNUP ─────────────────────────────────────────────────────
def signup_user(email: str, password: str, display_name: str) -> dict:
    email = email.lower().strip()

    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        return {"success": False, "message": "An account with this email already exists."}

    hashed = _hash_password(password)

    result = supabase.table("users").insert({
        "email":         email,
        "password_hash": hashed,
        "display_name":  display_name.strip(),
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "streak":        0,
        "sessions":      0,
    }).execute()

    if result.data:
        return {
            "success": True,
            "message": "Account created successfully.",
            "user_id": result.data[0]["id"],
        }

    return {"success": False, "message": "Could not create account. Please try again."}


# ── LOGIN STEP 1 ───────────────────────────────────────────────
def login_step1(email: str, password: str) -> dict:
    email  = email.lower().strip()
    hashed = _hash_password(password)

    result = supabase.table("users") \
        .select("id, email, display_name, password_hash") \
        .eq("email", email) \
        .execute()

    if not result.data:
        return {"success": False, "message": "No account found with that email."}

    user = result.data[0]
    if user["password_hash"] != hashed:
        return {"success": False, "message": "Incorrect password."}

    otp     = _generate_otp()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    supabase.table("otps").delete().eq("user_id", user["id"]).execute()

    supabase.table("otps").insert({
        "user_id":    user["id"],
        "otp_code":   otp,
        "expires_at": expires,
        "used":       False,
    }).execute()

    sent = _send_otp_email(email, otp, user.get("display_name", ""))

    if not sent:
        print(f"\n{'='*40}")
        print(f"  [DEV LOG] OTP for {email}: {otp}")
        print(f"  (Email delivery failed — console fallback)")
        print(f"{'='*40}\n")

    return {
        "success":  True,
        "message":  "OTP sent to your email." if sent else "OTP generated (check server console).",
        "email":    email,
    }


# ── LOGIN STEP 2 ───────────────────────────────────────────────
def login_step2(email: str, otp_entered: str) -> dict:
    email = email.lower().strip()

    user_result = supabase.table("users") \
        .select("id, email, display_name, streak, sessions") \
        .eq("email", email) \
        .execute()

    if not user_result.data:
        return {"success": False, "message": "User not found."}

    user = user_result.data[0]

    otp_result = supabase.table("otps") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .eq("used", False) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not otp_result.data:
        return {"success": False, "message": "No OTP found. Please request a new one."}

    otp_record = otp_result.data[0]

    raw_expiry = otp_record["expires_at"]
    if raw_expiry.endswith("Z"):
        raw_expiry = raw_expiry[:-1] + "+00:00"
    expires_at = datetime.fromisoformat(raw_expiry)
    now_utc = datetime.now(timezone.utc)
    if now_utc > expires_at:
        return {"success": False, "message": "OTP has expired. Please login again."}

    if otp_record["otp_code"] != otp_entered.strip():
        return {"success": False, "message": "Incorrect OTP. Please try again."}

    supabase.table("otps").update({"used": True}).eq("id", otp_record["id"]).execute()

    supabase.table("users").update({
        "last_login": datetime.now(timezone.utc).isoformat(),
        "sessions":   (user.get("sessions") or 0) + 1,
    }).eq("id", user["id"]).execute()

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id":           user["id"],
            "email":        user["email"],
            "display_name": user["display_name"],
            "streak":       user.get("streak", 0),
            "sessions":     user.get("sessions", 0),
        },
    }


# ── PROGRESS HELPERS ───────────────────────────────────────────
def save_learned_word(user_id: str, word: str) -> dict:
    existing = supabase.table("learned_words") \
        .select("id").eq("user_id", user_id).eq("word", word).execute()
    if existing.data:
        return {"success": False, "message": "Already saved."}
    supabase.table("learned_words").insert({
        "user_id":    user_id,
        "word":       word,
        "learned_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"success": True}


def save_topic(user_id: str, topic: str, category: str = "", difficulty: str = "") -> dict:
    supabase.table("saved_topics").insert({
        "user_id":    user_id,
        "topic":      topic,
        "category":   category,
        "difficulty": difficulty,
        "saved_at":   datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"success": True}


def save_answer(user_id: str, question: str, answer: str, q_type: str = "") -> dict:
    supabase.table("saved_answers").insert({
        "user_id":  user_id,
        "question": question,
        "answer":   answer,
        "type":     q_type,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"success": True}


def get_user_progress(user_id: str) -> dict:
    user    = supabase.table("users").select("streak,sessions,display_name").eq("id", user_id).execute()
    words   = supabase.table("learned_words").select("word").eq("user_id", user_id).execute()
    topics  = supabase.table("saved_topics").select("topic").eq("user_id", user_id).execute()
    answers = supabase.table("saved_answers").select("id").eq("user_id", user_id).execute()

    u = user.data[0] if user.data else {}
    return {
        "display_name":  u.get("display_name", ""),
        "streak":        u.get("streak", 0),
        "sessions":      u.get("sessions", 0),
        "words_learned": len(words.data),
        "topics_saved":  len(topics.data),
        "answers_saved": len(answers.data),
        "learned_words": [w["word"] for w in words.data],
        "saved_topics":  [t["topic"] for t in topics.data],
    }