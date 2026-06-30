"""
vocab_engine.py — Off The Mic
Adaptive vocabulary recommendation engine with difficulty-based logic.
"""

import random
import json
import os
from datetime import date
from typing import Dict, Any
from gemini_client import get_gemini_model, is_ai_available

# ── WORD BANK ──────────────────────────────────────────────────
WORD_BANK = {
    'beginner': [
        {
            'word': 'Eloquence', 'pos': 'noun',
            'pronunciation': '/ ˈel.ə.kwəns /',
            'meaning': 'The ability to express thoughts and ideas clearly, fluently, and persuasively in speech.',
            'example': '"Her eloquence in the debate left the audience spellbound."',
            'challenge': 'Use this word in a 60-second story about someone who inspired you.',
        },
        {
            'word': 'Articulate', 'pos': 'adjective',
            'pronunciation': '/ ɑːˈtɪk.jʊ.lɪt /',
            'meaning': 'Having or showing the ability to speak fluently and coherently; expressing ideas clearly.',
            'example': '"The most articulate candidate won over voters with clarity."',
            'challenge': 'Describe a topic you feel passionate about — be as articulate as possible.',
        },
        {
            'word': 'Poise', 'pos': 'noun',
            'pronunciation': '/ pɔɪz /',
            'meaning': 'Graceful and elegant bearing; a state of balance and self-confidence under pressure.',
            'example': '"Despite the unexpected question, she answered with remarkable poise."',
            'challenge': 'Speak for 45 seconds about a challenge you handled with poise.',
        },
        {
            'word': 'Candour', 'pos': 'noun',
            'pronunciation': '/ ˈkæn.dər /',
            'meaning': 'The quality of being open, honest, and direct in expression.',
            'example': '"His candour during the interview was refreshing."',
            'challenge': 'Share a candid opinion about something you usually keep to yourself.',
        },
        {
            'word': 'Affable', 'pos': 'adjective',
            'pronunciation': '/ ˈæf.ə.bəl /',
            'meaning': 'Friendly, easy to talk to, and pleasant in manner.',
            'example': '"His affable personality made him a natural presenter."',
            'challenge': 'Introduce yourself as if meeting someone new — be warm and affable.',
        },
    ],
    'intermediate': [
        {
            'word': 'Rhetoric', 'pos': 'noun',
            'pronunciation': '/ ˈret.ər.ɪk /',
            'meaning': 'The art of effective or persuasive speaking or writing using language that powerfully affects its audience.',
            'example': '"The politician\'s rhetoric was compelling, but critics urged deeper analysis."',
            'challenge': 'Give a short persuasive speech on a topic you care about — focus on rhetoric.',
        },
        {
            'word': 'Gravitas', 'pos': 'noun',
            'pronunciation': '/ ˈɡræv.ɪ.tæs /',
            'meaning': 'Dignity, seriousness, and weight of character in a person\'s manner of speaking.',
            'example': '"The CEO spoke with gravitas, and the boardroom fell attentive."',
            'challenge': 'Speak about a serious topic using a measured, weighty tone.',
        },
        {
            'word': 'Lucid', 'pos': 'adjective',
            'pronunciation': '/ ˈluː.sɪd /',
            'meaning': 'Clear, coherent, and easy to understand; leaving no room for confusion.',
            'example': '"Her lucid explanation made the complex theory accessible to everyone."',
            'challenge': 'Explain a technical concept to a non-expert as lucidly as possible.',
        },
        {
            'word': 'Conviction', 'pos': 'noun',
            'pronunciation': '/ kənˈvɪk.ʃən /',
            'meaning': 'A firmly held belief; the quality of speaking with certainty and passion.',
            'example': '"She spoke with such conviction that even the sceptics reconsidered."',
            'challenge': 'Argue a position you genuinely believe — let your conviction show.',
        },
        {
            'word': 'Intonation', 'pos': 'noun',
            'pronunciation': '/ ˌɪn.təˈneɪ.ʃən /',
            'meaning': 'The rise and fall of voice in speaking; the way pitch conveys meaning and emotion.',
            'example': '"Mastering intonation separates a monotone speaker from a captivating one."',
            'challenge': 'Read the same sentence with three different intonations — curious, assertive, and warm.',
        },
    ],
    'advanced': [
        {
            'word': 'Verbose', 'pos': 'adjective',
            'pronunciation': '/ vɜːˈboʊs /',
            'meaning': 'Using more words than necessary; excessively wordy in speech or writing.',
            'example': '"His verbose response wandered so far that the audience lost the point."',
            'challenge': 'Restate a complex idea you know in exactly 30 words — no more, no less.',
        },
        {
            'word': 'Cadence', 'pos': 'noun',
            'pronunciation': '/ ˈkeɪ.dəns /',
            'meaning': 'The rhythmic flow and beat of speech; the tempo and music of spoken words.',
            'example': '"Her speech had a natural cadence that made it almost musical to listen to."',
            'challenge': 'Deliver a 90-second monologue — pay deliberate attention to your cadence.',
        },
        {
            'word': 'Brevity', 'pos': 'noun',
            'pronunciation': '/ ˈbrev.ɪ.ti /',
            'meaning': 'The quality of expressing something concisely without losing meaning.',
            'example': '"Shakespeare understood brevity — his most powerful lines are often his shortest."',
            'challenge': 'Summarise your life philosophy in under 60 seconds using brevity as a virtue.',
        },
        {
            'word': 'Enunciate', 'pos': 'verb',
            'pronunciation': '/ ɪˈnʌn.si.eɪt /',
            'meaning': 'To pronounce words clearly and distinctly; to articulate each syllable with precision.',
            'example': '"A skilled broadcaster enunciates every word so no listener is left behind."',
            'challenge': 'Speak a complex paragraph at half speed, fully enunciating each syllable.',
        },
        {
            'word': 'Synergy', 'pos': 'noun',
            'pronunciation': '/ ˈsɪn.ər.dʒi /',
            'meaning': 'The interaction of elements that produces a combined effect greater than the sum of their parts.',
            'example': '"The synergy between the two speakers created an electrifying exchange."',
            'challenge': 'Describe a collaboration you were part of — explain the synergy that made it work.',
        },
    ],
}


def get_vocab_word(level: str = 'intermediate') -> Dict[str, Any]:
    """
    Return a random vocabulary word appropriate for the given level.
    If Gemini AI is available, generates a dynamic word.
    Otherwise, falls back to the static bank.
    """
    return recommend_next_word([], level)


def get_word_of_day() -> Dict[str, Any]:
    """
    Return a unique daily word-of-the-day.
    Checks Supabase 'word_of_day' table first. If missing, generates a new
    non-repeating word using Gemini and caches it in Supabase (or local file).
    """
    from auth import supabase
    from datetime import date
    
    today_str = date.today().isoformat()
    
    # 1. Try to fetch from Supabase
    try:
        res = supabase.table("word_of_day").select("*").eq("publish_date", today_str).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"[WORD OF DAY DB FETCH ERROR] {e}")
        
    # 2. Try to fetch from local JSON cache (fallback if DB/network fails)
    cache_path = os.path.join(os.path.dirname(__file__), "word_of_day_cache.json")
    local_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                local_cache = json.load(f)
            if today_str in local_cache:
                return local_cache[today_str]
        except Exception as e:
            print(f"[WORD OF DAY LOCAL FETCH ERROR] {e}")
            
    # 3. Generate a new word that doesn't repeat
    # Collect history of past words to exclude
    history = []
    try:
        hist_res = supabase.table("word_of_day").select("word").execute()
        if hist_res.data:
            history = [r["word"] for r in hist_res.data]
    except Exception as e:
        print(f"[WORD OF DAY HISTORY FETCH ERROR] {e}")
        
    # Add local cache history
    if "history" in local_cache:
        history = list(set(history + local_cache["history"]))
        
    # Generate the word
    word_data = None
    if is_ai_available():
        model = get_gemini_model("gemini-2.5-flash")
        if model:
            try:
                history_desc = f" Avoid repeating these past words: {', '.join(history)}." if history else ""
                prompt = (
                    "Generate a single, highly engaging vocabulary word suitable for improving public speaking and communication."
                    f"{history_desc}"
                    " Return the result ONLY as a JSON object with exactly these keys:\n"
                    " - 'word': the word itself (capitalized/proper casing)\n"
                    " - 'pos': part of speech (noun, verb, adjective, adverb, etc.)\n"
                    " - 'pronunciation': phonetics (e.g. '/ ˈel.ə.kwəns /')\n"
                    " - 'meaning': a concise definition\n"
                    " - 'example': a sample sentence using the word\n"
                    " - 'challenge': a 30-to-60 second public speaking practice challenge focusing on utilizing this word\n\n"
                    "Do not include any markdown formatting like ```json or anything else. Just the raw JSON object."
                )
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                
                data = json.loads(text)
                required_keys = ['word', 'pos', 'pronunciation', 'meaning', 'example', 'challenge']
                if all(k in data for k in required_keys):
                    word_data = data
            except Exception as e:
                print(f"[WORD OF DAY GEMINI GENERATION ERROR] {e}")
                
    # If AI fails or is offline, pick from the static bank excluding history
    if not word_data:
        all_static = []
        for level_words in WORD_BANK.values():
            all_static.extend(level_words)
        unseen = [w for w in all_static if w['word'] not in history]
        if not unseen:
            unseen = all_static # Reset if all used
        word_data = random.choice(unseen).copy()
        
    word_data['publish_date'] = today_str
    
    # 4. Save to Supabase
    try:
        supabase.table("word_of_day").insert({
            "publish_date": today_str,
            "word": word_data["word"],
            "pos": word_data["pos"],
            "pronunciation": word_data["pronunciation"],
            "meaning": word_data["meaning"],
            "example": word_data["example"],
            "challenge": word_data["challenge"]
        }).execute()
    except Exception as e:
        print(f"[WORD OF DAY SAVE DB ERROR] {e}")
        
    # 5. Save to local cache as fallback
    try:
        local_cache[today_str] = word_data
        if "history" not in local_cache:
            local_cache["history"] = []
        if word_data["word"] not in local_cache["history"]:
            local_cache["history"].append(word_data["word"])
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(local_cache, f, indent=2)
    except Exception as e:
        print(f"[WORD OF DAY SAVE LOCAL ERROR] {e}")
        
    return word_data


def get_words_by_difficulty(level: str, count: int = 5) -> list:
    """Return multiple words for a given difficulty level."""
    bank   = WORD_BANK.get(level, WORD_BANK['intermediate'])
    sample = random.sample(bank, min(count, len(bank)))
    return sample


# ── ADAPTIVE RECOMMENDATION ──────────────────
def recommend_next_word(user_history: list, preferred_level: str = 'intermediate') -> Dict[str, Any]:
    """
    Recommend the next word based on user learning history.
    If Gemini AI is available, generates a dynamic, context-rich vocabulary word.
    Otherwise, falls back to local exclusion of already-learned words.
    """
    if not user_history:
        user_history = []
        
    if is_ai_available():
        model = get_gemini_model("gemini-2.5-flash")
        if model:
            try:
                history_desc = f" Avoid recommending these words: {', '.join(user_history)}." if user_history else ""
                prompt = (
                    f"Generate a single vocabulary word of difficulty level '{preferred_level}' suitable for improving public speaking/vocabulary."
                    f"{history_desc}"
                    " Return the result ONLY as a JSON object with exactly these keys:\n"
                    " - 'word': the word itself (capitalized/proper casing)\n"
                    " - 'pos': part of speech (noun, verb, adjective, adverb, etc.)\n"
                    " - 'pronunciation': phonetics (e.g. '/ ˈel.ə.kwəns /')\n"
                    " - 'meaning': a concise definition\n"
                    " - 'example': a sample sentence using the word\n"
                    " - 'challenge': a 30-to-60 second public speaking practice challenge focusing on utilizing this word\n\n"
                    "Do not include any markdown formatting like ```json or anything else. Just the raw JSON object."
                )
                
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                    
                data = json.loads(text)
                required_keys = ['word', 'pos', 'pronunciation', 'meaning', 'example', 'challenge']
                if all(k in data for k in required_keys):
                    return data
            except Exception as e:
                print(f"[GEMINI VOCAB GENERATION ERROR] {e}. Falling back to static list.")
                
    # Offline fallback logic
    bank   = WORD_BANK.get(preferred_level, WORD_BANK['intermediate'])
    unseen = [w for w in bank if w['word'] not in user_history]

    if not unseen:
        # All words seen — advance to next level
        levels = ['beginner', 'intermediate', 'advanced']
        idx    = levels.index(preferred_level) if preferred_level in levels else 1
        next_level = levels[min(idx + 1, len(levels) - 1)]
        unseen = WORD_BANK[next_level]

    return random.choice(unseen) if unseen else get_vocab_word(preferred_level)
