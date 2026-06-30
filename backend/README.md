# Off The Mic

> *practice a little, speak a lot.*

Off The Mic is an AI-powered communication practice platform that helps users improve public speaking, vocabulary, interview readiness, and speech confidence.

---

## Project Structure

```
off-the-mic/
├── index.html          Landing page
├── login.html          Login
├── signup.html         Sign-up
├── dashboard.html      Feature hub
├── topics.html         AI topic generator + timer
├── vocab.html          Vocabulary builder
├── analysis.html       Speech recording & analysis
├── interview.html      Interview prep
├── progress.html       Progress tracker
├── style.css           Complete stylesheet (Caveat + Poppins)
├── script.js           Shared JS (toast, streak, API helpers)
└── backend/
    ├── app.py              Flask API
    ├── topic_generator.py  Topic + interview question engine
    ├── speech_analyzer.py  Speech metric extraction
    ├── vocab_engine.py     Adaptive vocabulary engine
    └── requirements.txt
```

---

## Quick Start

### Frontend (no server needed)
Open `index.html` directly in your browser. All features work without the Flask backend — topic generation, vocab, analysis, interview prep, and progress tracking all run in-browser using localStorage.

### Backend (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
The API will run at `http://localhost:5000`.

---

## Supabase Integration

1. Create a project at [supabase.com](https://supabase.com)
2. Add your keys to the frontend pages:
   ```html
   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
   <script>
     const supabase = window.supabase.createClient('YOUR_URL', 'YOUR_ANON_KEY')
   </script>
   ```
3. Replace the auth placeholder comments in `login.html` and `signup.html`
4. Replace the progress placeholder comments in `backend/app.py`

Suggested Supabase tables:
- `profiles` (user_id, display_name, streak, joined_at)
- `learned_words` (user_id, word, learned_at)
- `saved_topics` (user_id, topic, category, difficulty, saved_at)
- `saved_answers` (user_id, question, answer, type, saved_at)
- `sessions` (user_id, type, scores, created_at)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/generate-topic` | Generate a speaking topic |
| `POST` | `/analyze-speech` | Analyse transcript or audio |
| `GET`  | `/get-vocab` | Get a vocabulary word |
| `GET`  | `/word-of-day` | Today's word of the day |
| `GET`  | `/interview-question` | Get an interview question |
| `GET`  | `/progress` | Fetch user progress |
| `POST` | `/progress` | Save a progress event |

---

## ML Upgrade Path

Each Python module has clearly marked `# FUTURE ML HOOK` sections:

- **topic_generator.py** → swap `generate_topic()` for a fine-tuned T5/GPT-2 generator
- **speech_analyzer.py** → integrate Whisper for transcription + librosa for prosodic features
- **vocab_engine.py** → replace `recommend_next_word()` with a Deep Knowledge Tracing model

---

## Design

- **Background:** `#FAF7F2` (warm off-white)
- **Cards:** `#FFFDF9`
- **Text:** `#2F463B` (deep forest green)
- **Accent:** `#A8B5A2` (sage)
- **Headings:** Caveat (Google Fonts)
- **Body:** Poppins (Google Fonts)
