"""
speech_analyzer.py — Off The Mic
Speech metric extraction with ML placeholder hooks.
"""

import re
import math
import random
import json
from typing import Dict, Any
from gemini_client import get_gemini_model, is_ai_available

# Common filler words to detect
FILLER_WORDS = {
    'um', 'uh', 'like', 'you know', 'basically', 'literally',
    'actually', 'right', 'so', 'well', 'kind of', 'sort of',
    'I mean', 'you see', 'okay so', 'and um', 'err',
}


def analyze_speech_text(transcript: str) -> Dict[str, Any]:
    """
    Analyse a text transcript and return speech quality metrics.
    Uses Gemini AI if available for advanced coaching metrics and tips.
    Falls back to heuristic rules if offline.
    """
    if not transcript or not transcript.strip():
        return _empty_result()

    words      = transcript.split()
    word_count = len(words)
    lower_text = transcript.lower()

    # ── FILLER DETECTION ─────────────────────────────────────────
    detected_fillers = []
    for filler in FILLER_WORDS:
        count = len(re.findall(r'\b' + re.escape(filler) + r'\b', lower_text))
        if count:
            detected_fillers.extend([filler] * count)

    filler_count = len(detected_fillers)
    filler_ratio = filler_count / word_count if word_count else 0

    # ── SENTENCE METRICS ─────────────────────────────────────────
    sentences      = re.split(r'[.!?]+', transcript)
    sentences      = [s.strip() for s in sentences if s.strip()]
    sentence_count = max(len(sentences), 1)
    avg_sent_len   = word_count / sentence_count

    # ── VOCABULARY COMPLEXITY ────────────────────────────────────
    unique_words   = set(w.lower().strip('.,!?;:') for w in words)
    lexical_div    = len(unique_words) / word_count if word_count else 0
    avg_word_len   = sum(len(w.strip('.,!?;:')) for w in words) / word_count if word_count else 0

    # Try Gemini AI evaluation if available
    if is_ai_available():
        model = get_gemini_model("gemini-2.5-flash")
        if model:
            try:
                prompt = (
                    "You are an expert public speaking coach. Analyze the following transcript of a user's speaking exercise:\n\n"
                    f"\"{transcript}\"\n\n"
                    "Grade/estimate the following scores out of 100:\n"
                    "1. Confidence: how confident and assertive the speech sounds (lack of fillers, clear structures, strong statements)\n"
                    "2. Fluency: grammatical cohesion, smooth transitions, and flow\n"
                    "3. Pacing: consistency of rhythm and phrase/sentence variation\n"
                    "4. Clarity: ease of understanding and vocabulary precision\n\n"
                    "Also generate 4-5 highly specific, actionable, and constructive recommendations/tips for this user to improve their delivery.\n\n"
                    "Return the result ONLY as a JSON object with exactly these keys:\n"
                    " - 'confidence': integer (20 to 100)\n"
                    " - 'fluency': integer (20 to 100)\n"
                    " - 'pacing': integer (20 to 100)\n"
                    " - 'clarity': integer (20 to 100)\n"
                    " - 'feedback': list of 4-5 string suggestions\n\n"
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
                required_keys = ['confidence', 'fluency', 'pacing', 'clarity', 'feedback']
                if all(k in data for k in required_keys):
                    return {
                        'confidence':          int(data['confidence']),
                        'fluency':             int(data['fluency']),
                        'pacing':              int(data['pacing']),
                        'clarity':             int(data['clarity']),
                        'filler_count':        filler_count,
                        'filler_words':        list(set(detected_fillers)),
                        'word_count':          word_count,
                        'sentence_count':      sentence_count,
                        'avg_sentence_length': round(avg_sent_len, 1),
                        'lexical_diversity':   round(lexical_div, 2),
                        'feedback':            data['feedback'],
                    }
            except Exception as e:
                print(f"[GEMINI SPEECH ANALYZER ERROR] {e}. Falling back to static heuristics.")

    # ── HEURISTIC SCORE COMPUTATION (FALLBACK) ────────────────────
    # Fluency: penalise filler words
    fluency = max(20, min(98, round(90 - filler_ratio * 250)))

    # Clarity: reward longer/varied vocabulary, punish very short words
    clarity = max(20, min(98, round(40 + avg_word_len * 8 + lexical_div * 30)))

    # Pacing: sentence length close to 12 is ideal
    pacing = max(20, min(98, round(98 - abs(avg_sent_len - 12) * 2.5)))

    # Confidence: composite + small jitter for realism
    confidence = max(20, min(98, round((fluency * 0.35 + clarity * 0.35 + pacing * 0.3) + random.uniform(-4, 4))))

    # ── FEEDBACK ──────────────────────────────────────────────────
    feedback = _build_feedback(
        filler_count, filler_ratio, avg_sent_len,
        clarity, pacing, fluency, word_count, lexical_div
    )

    return {
        'confidence':          confidence,
        'fluency':             fluency,
        'pacing':              pacing,
        'clarity':             clarity,
        'filler_count':        filler_count,
        'filler_words':        list(set(detected_fillers)),
        'word_count':          word_count,
        'sentence_count':      sentence_count,
        'avg_sentence_length': round(avg_sent_len, 1),
        'lexical_diversity':   round(lexical_div, 2),
        'feedback':            feedback,
    }


def analyze_audio(audio_file) -> Dict[str, Any]:
    """
    Real audio file transcription and analysis using Gemini's multimodal capabilities.
    """
    import os
    import tempfile
    import google.generativeai as genai
    from gemini_client import get_gemini_model, is_ai_available

    if not is_ai_available():
        return {
            'confidence':  50,
            'fluency':     50,
            'pacing':      50,
            'clarity':     50,
            'filler_count': 0,
            'filler_words': [],
            'word_count':   0,
            'sentence_count': 0,
            'avg_sentence_length': 0.0,
            'lexical_diversity': 0.0,
            'feedback': [
                'Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file.',
                'Offline simulation results will be shown instead.'
            ],
            'error': 'API key not configured'
        }
        
    # Save uploaded file to a temporary file
    temp_dir = tempfile.gettempdir()
    original_filename = getattr(audio_file, 'filename', 'audio.webm')
    _, ext = os.path.splitext(original_filename)
    if not ext:
        ext = '.webm'
    
    temp_path = os.path.join(temp_dir, f"otm_audio_{os.getpid()}{ext}")
    
    try:
        audio_file.save(temp_path)
        
        # Upload file to Gemini API
        mime_type = "audio/webm"
        if ext == ".ogg":
            mime_type = "audio/ogg"
        elif ext == ".mp3":
            mime_type = "audio/mp3"
        elif ext == ".wav":
            mime_type = "audio/wav"
            
        print(f"[SPEECH ANALYZER] Uploading {temp_path} to Gemini...")
        file = genai.upload_file(path=temp_path, mime_type=mime_type)
        
        try:
            model = get_gemini_model("gemini-2.5-flash")
            if not model:
                raise Exception("Could not initialize Gemini model.")
                
            prompt = "Transcribe this audio recording exactly. Do not add any introduction, notes, or extra commentary. Just output the raw transcribed text of the user's speech."
            
            print("[SPEECH ANALYZER] Generating transcription via Gemini...")
            response = model.generate_content([file, prompt])
            transcript = response.text.strip()
            print(f"[SPEECH ANALYZER] Transcribed text: {transcript}")
            
            if not transcript:
                raise Exception("Gemini returned an empty transcription.")
                
            # Analyze the transcript using the existing analyze_speech_text function
            result = analyze_speech_text(transcript)
            result['transcript'] = transcript
            return result
            
        finally:
            # Always delete the uploaded file from Google's servers
            try:
                genai.delete_file(file.name)
                print(f"[SPEECH ANALYZER] Deleted remote file {file.name}")
            except Exception as delete_err:
                print(f"[SPEECH ANALYZER] Failed to delete remote file: {delete_err}")
                
    except Exception as e:
        print(f"[SPEECH ANALYZER ERROR] Audio analysis failed: {e}")
        return {
            'confidence':  60,
            'fluency':     60,
            'pacing':      60,
            'clarity':     60,
            'filler_count': 0,
            'filler_words': [],
            'word_count':   0,
            'sentence_count': 0,
            'avg_sentence_length': 0,
            'lexical_diversity': 0.0,
            'feedback': [
                f"Audio analysis failed: {str(e)}",
                "Please verify your mic is connected, make sure you spoke clearly, and try again."
            ],
            'error': str(e)
        }
    finally:
        # Clean up the local temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"[SPEECH ANALYZER] Cleaned up local temp file {temp_path}")
            except Exception as clean_err:
                print(f"[SPEECH ANALYZER] Failed to remove temp file: {clean_err}")


def _build_feedback(filler_count, filler_ratio, avg_sent_len,
                    clarity, pacing, fluency, word_count, lexical_div) -> list:
    items = []

    if filler_count > 0:
        items.append(
            f"Detected {filler_count} filler word{'s' if filler_count != 1 else ''} "
            f"(um, uh, like…). Replace each with a deliberate pause instead."
        )
    if fluency < 70:
        items.append("Your fluency score suggests some hesitation. Take a breath before each sentence.")
    elif fluency >= 85:
        items.append("Strong fluency — very few hesitations detected. Keep it up!")

    if avg_sent_len < 8:
        items.append("Sentences are quite short. Expand each idea with a supporting detail or example.")
    elif avg_sent_len > 25:
        items.append("Some sentences are very long. Break them into smaller units for clearer delivery.")
    else:
        items.append("Good sentence length — your rhythm feels natural and easy to follow.")

    if clarity < 60:
        items.append("Try using more varied and expressive vocabulary to lift your clarity score.")
    elif clarity >= 80:
        items.append("Excellent vocabulary complexity — your word choices convey confidence.")

    if pacing < 65:
        items.append("Work on consistent pacing. Aim for steady, even sentence lengths.")

    if word_count < 50:
        items.append("Short response — aim for at least 150 words to get more detailed analysis.")

    if lexical_div > 0.75:
        items.append("Great lexical diversity — you're using a wide range of words, which sounds engaging.")

    items.append(
        "Tip: Slow down by 10%. Listeners process ideas better with slightly more space between thoughts."
    )

    return items[:6]


def _empty_result() -> Dict[str, Any]:
    return {
        'confidence': 0, 'fluency': 0, 'pacing': 0, 'clarity': 0,
        'filler_count': 0, 'filler_words': [],
        'word_count': 0, 'sentence_count': 0,
        'avg_sentence_length': 0, 'lexical_diversity': 0,
        'feedback': ['Please provide a transcript to analyse.'],
    }
