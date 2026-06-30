"""
Off The Mic — Vercel Serverless Function
All Flask routes merged into a single WSGI app for Vercel's @vercel/python runtime.
"""

import sys
import os

# Add parent dir so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import secrets

from auth import (
    signup_user, login_step1, login_step2,
    save_learned_word, save_topic, save_answer, get_user_progress
)
from topic_generator import generate_topic, get_interview_question
from speech_analyzer import analyze_speech_text, analyze_audio
from vocab_engine import get_vocab_word, get_word_of_day, recommend_next_word

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', secrets.token_hex(32))
CORS(app, resources={r"/*": {"origins": "*"}})


# ── HEALTH ─────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
@app.route('/api/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Off The Mic API'})


# ════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════════

@app.route('/api/auth/signup', methods=['POST'])
def route_signup():
    data         = request.get_json(force=True) or {}
    email        = data.get('email', '').strip()
    password     = data.get('password', '')
    display_name = data.get('display_name', '').strip()

    if not email or not password or not display_name:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters.'}), 400

    result = signup_user(email, password, display_name)
    status = 201 if result['success'] else 409
    return jsonify(result), status


@app.route('/api/auth/login', methods=['POST'])
def route_login():
    data     = request.get_json(force=True) or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required.'}), 400

    result = login_step1(email, password)
    return jsonify(result), 200 if result['success'] else 401


@app.route('/api/auth/verify-otp', methods=['POST'])
def route_verify_otp():
    data  = request.get_json(force=True) or {}
    email = data.get('email', '').strip()
    otp   = data.get('otp', '').strip()

    if not email or not otp:
        return jsonify({'success': False, 'message': 'Email and OTP required.'}), 400

    result = login_step2(email, otp)

    if result['success']:
        session['user_id']      = result['user']['id']
        session['user_email']   = result['user']['email']
        session['display_name'] = result['user']['display_name']

    return jsonify(result), 200 if result['success'] else 401


@app.route('/api/auth/logout', methods=['POST'])
def route_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out.'})


@app.route('/api/auth/me', methods=['GET'])
def route_me():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in.'}), 401
    return jsonify({
        'success':      True,
        'user_id':      session['user_id'],
        'email':        session['user_email'],
        'display_name': session['display_name'],
    })


# ════════════════════════════════════════════════════════════════
#  PROGRESS ROUTES
# ════════════════════════════════════════════════════════════════

@app.route('/api/progress', methods=['GET'])
def route_progress():
    user_id = request.args.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated.'}), 401
    data = get_user_progress(user_id)
    return jsonify({'success': True, **data})


@app.route('/api/progress/save-word', methods=['POST'])
def route_save_word():
    data    = request.get_json(force=True) or {}
    user_id = data.get('user_id') or session.get('user_id')
    word    = data.get('word', '')
    if not user_id or not word:
        return jsonify({'success': False, 'message': 'user_id and word required.'}), 400
    return jsonify(save_learned_word(user_id, word))


@app.route('/api/progress/save-topic', methods=['POST'])
def route_save_topic():
    data       = request.get_json(force=True) or {}
    user_id    = data.get('user_id') or session.get('user_id')
    topic      = data.get('topic', '')
    category   = data.get('category', '')
    difficulty = data.get('difficulty', '')
    if not user_id or not topic:
        return jsonify({'success': False, 'message': 'user_id and topic required.'}), 400
    return jsonify(save_topic(user_id, topic, category, difficulty))


@app.route('/api/progress/save-answer', methods=['POST'])
def route_save_answer():
    data     = request.get_json(force=True) or {}
    user_id  = data.get('user_id') or session.get('user_id')
    question = data.get('question', '')
    answer   = data.get('answer', '')
    q_type   = data.get('type', '')
    if not user_id or not question or not answer:
        return jsonify({'success': False, 'message': 'user_id, question, and answer required.'}), 400
    return jsonify(save_answer(user_id, question, answer, q_type))


# ════════════════════════════════════════════════════════════════
#  FEATURE ROUTES
# ════════════════════════════════════════════════════════════════

@app.route('/api/generate-topic', methods=['POST'])
def route_generate_topic():
    data = request.get_json(force=True) or {}
    category = data.get('category', '')
    difficulty = data.get('difficulty', '')
    user_id = data.get('user_id') or session.get('user_id')
    
    saved_topics = []
    if user_id:
        try:
            progress = get_user_progress(user_id)
            saved_topics = progress.get('saved_topics', [])
        except Exception as e:
            print(f"[TOPIC RECOMMENDATION ERROR] {e}")
            
    topic = generate_topic(category, difficulty, exclude_history=saved_topics)
    return jsonify({'topic': topic, 'category': category or 'mixed', 'difficulty': difficulty or 'all'})


@app.route('/api/analyze-speech', methods=['POST'])
def route_analyze_speech():
    if request.is_json:
        data   = request.get_json(force=True) or {}
        result = analyze_speech_text(data.get('transcript', ''))
        return jsonify(result)
    audio = request.files.get('audio')
    if audio:
        return jsonify(analyze_audio(audio))
    return jsonify({'error': 'No transcript or audio provided'}), 400


@app.route('/api/get-vocab', methods=['GET'])
def route_get_vocab():
    level = request.args.get('level', 'intermediate')
    user_id = request.args.get('user_id') or session.get('user_id')
    if user_id:
        try:
            progress = get_user_progress(user_id)
            learned = progress.get('learned_words', [])
            return jsonify(recommend_next_word(learned, level))
        except Exception as e:
            print(f"[VOCAB RECOMMENDATION ERROR] {e}")
    return jsonify(get_vocab_word(level=level))


@app.route('/api/word-of-day', methods=['GET'])
def route_word_of_day():
    return jsonify(get_word_of_day())


@app.route('/api/interview-question', methods=['GET'])
def route_interview_question():
    q_type = request.args.get('type', 'hr')
    user_id = request.args.get('user_id') or session.get('user_id')
    
    answered = []
    if user_id:
        try:
            from auth import supabase
            answers_res = supabase.table("saved_answers").select("question").eq("user_id", user_id).execute()
            answered = [a["question"] for a in answers_res.data] if answers_res.data else []
        except Exception as e:
            print(f"[INTERVIEW RECOMMENDATION ERROR] {e}")
            
    question_data = get_interview_question(q_type, exclude_history=answered)
    return jsonify(question_data)


# Vercel expects the app object to be named `app`
# The handler is the WSGI app itself
