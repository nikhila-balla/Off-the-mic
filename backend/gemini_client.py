"""
gemini_client.py — Off The Mic
Google Generative AI (Gemini) client wrapper.
"""

import os
import google.generativeai as genai

# Load environment variables if not loaded (local development)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Configure the API key
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY")

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        print(f"[GEMINI CONFIG ERROR] Could not configure SDK: {e}")
        API_KEY = None

def get_gemini_model(model_name: str = "gemini-2.5-flash"):
    """
    Returns a configured GenerativeModel instance, or None if the API key is missing.
    """
    if not API_KEY:
        return None
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"[GEMINI MODEL ERROR] Could not load model {model_name}: {e}")
        return None

def is_ai_available() -> bool:
    """Check if the Gemini API key is configured."""
    return bool(API_KEY)
