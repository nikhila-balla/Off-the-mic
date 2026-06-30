"""
topic_generator.py — Off The Mic
AI / NLP-powered topic and interview question generation.
Placeholder ML hooks ready for upgrade to transformer-based generation.
"""

import random
import json
from datetime import datetime
from gemini_client import get_gemini_model, is_ai_available

# ── TOPIC BANK ─────────────────────────────────────────────────
TOPIC_BANK = {
    'technology': {
        'beginner': [
            "Should everyone learn to code?",
            "Is social media helpful or harmful for teens?",
            "Are smartphones making us less social?",
            "Should schools ban phones in class?",
            "Do you prefer reading books or using apps to learn?",
        ],
        'intermediate': [
            "How will automation change the job market in the next decade?",
            "Is the convenience of smart home devices worth the privacy trade-off?",
            "Should tech companies be responsible for the content users post?",
            "How has technology changed the way we form relationships?",
            "Can AI ever truly replace human creativity?",
        ],
        'advanced': [
            "Evaluate the ethical implications of mass surveillance under the guise of national security.",
            "To what extent should governments regulate algorithmic decision-making in public services?",
            "Is the open-source movement sustainable in a monopolistic tech landscape?",
            "How does digital colonialism perpetuate global inequality?",
            "Argue for or against the idea that the metaverse will fragment rather than connect society.",
        ],
    },
    'ai': {
        'beginner': [
            "What is artificial intelligence in simple words?",
            "Should AI be allowed to make art?",
            "Can a robot be your friend?",
            "Do you trust AI recommendations?",
            "What would you ask an AI if you could ask anything?",
        ],
        'intermediate': [
            "Is AI bias a technical problem or a societal one?",
            "Should AI-generated content be labelled?",
            "How might AI change the way doctors diagnose illness?",
            "What jobs do you think AI will never be able to do?",
            "Does AI make education more or less equitable?",
        ],
        'advanced': [
            "Critically assess whether large language models constitute a form of understanding.",
            "Should sentient AI have legal rights?",
            "How should liability be assigned when autonomous AI systems cause harm?",
            "Is the race to AGI a net positive for humanity?",
            "Analyse the tension between AI transparency and proprietary competitive advantage.",
        ],
    },
    'debate': {
        'beginner': [
            "Should school uniforms be mandatory?",
            "Is homework necessary?",
            "Should junk food be banned in schools?",
            "Should voting age be lowered to 16?",
            "Are zoos ethical?",
        ],
        'intermediate': [
            "Should social media platforms be classified as public utilities?",
            "Is cancel culture a force for good or harm?",
            "Should college education be free for everyone?",
            "Is remote work better than office work?",
            "Should extreme sports be banned?",
        ],
        'advanced': [
            "Resolved: Universal basic income is the most effective response to technological unemployment.",
            "The right to free speech must be balanced against the duty to prevent harm — discuss.",
            "Is civil disobedience ever morally justified?",
            "Evaluate the claim that meritocracy is a myth that perpetuates inequality.",
            "Resolved: Economic growth and environmental sustainability are fundamentally incompatible.",
        ],
    },
    'social': {
        'beginner': [
            "What does community mean to you?",
            "How can young people make a difference?",
            "Is kindness a strength or a weakness?",
            "What is the most important social issue facing your generation?",
            "Should people speak out when they witness injustice?",
        ],
        'intermediate': [
            "How does social media amplify or reduce social inequality?",
            "Is charity a sustainable solution to poverty?",
            "How should mental health education be integrated into schools?",
            "What role does privilege play in access to opportunity?",
            "Can art be a tool for social change?",
        ],
        'advanced': [
            "To what extent does systemic racism persist in institutional structures today?",
            "Analyse the relationship between economic precarity and political radicalisation.",
            "Is the concept of meritocracy a barrier to genuine social mobility?",
            "Evaluate whether humanitarian intervention is a form of neo-colonialism.",
            "How should society balance individual liberty with collective responsibility during public health crises?",
        ],
    },
    'college': {
        'beginner': [
            "What is the best thing about college life?",
            "How do you manage your time as a student?",
            "What has been your biggest challenge in college so far?",
            "Is college friendship different from school friendship?",
            "What skill do you wish you learned before college?",
        ],
        'intermediate': [
            "Does a college degree still guarantee career success?",
            "How does social media affect mental health of college students?",
            "Is student debt a personal responsibility or a systemic failure?",
            "How important is extracurricular involvement for career prospects?",
            "Should colleges provide mental health support as a core service?",
        ],
        'advanced': [
            "Critically examine whether the traditional university model is equipped for the 21st century workforce.",
            "Is the commodification of higher education undermining its original purpose?",
            "Analyse the impact of prestige culture in colleges on student well-being and ethics.",
            "How does the lack of vocational education pathways disadvantage working-class students?",
            "Should colleges be politically neutral institutions?",
        ],
    },
}

# ── INTERVIEW QUESTION BANK ─────────────────────────────────────
INTERVIEW_BANK = {
    'hr': {
        'questions': [
            "Tell me about yourself.",
            "Why do you want to work here?",
            "What are your greatest strengths?",
            "What is your biggest weakness?",
            "Where do you see yourself in five years?",
            "Why are you leaving your current role?",
            "What motivates you at work?",
            "How do you handle stress and pressure?",
        ],
        'tips': [
            "Structure your answer: background → skills → enthusiasm for this role.",
            "Research the company and align your values to their mission.",
            "Choose strengths that match the job description with a concrete example.",
            "Name a real weakness and demonstrate how you are actively improving.",
            "Be specific and ambitious but realistic.",
            "Stay positive — focus on growth, not dissatisfaction.",
            "Link your motivators to the actual work this role involves.",
            "Describe a concrete coping strategy you genuinely use.",
        ],
    },
    'behavioral': {
        'questions': [
            "Tell me about a time you failed. What did you learn?",
            "Describe a situation where you had to work with a difficult colleague.",
            "Give an example of a time you showed leadership without a formal title.",
            "Tell me about a time you had to meet a tight deadline.",
            "Describe a time you had to persuade someone who disagreed with you.",
            "Tell me about a time you received critical feedback. How did you respond?",
            "Give an example of a creative solution you came up with.",
            "Describe a time you went above and beyond what was expected.",
        ],
        'tips': [
            "Use STAR: Situation → Task → Action → Result. End with a learning.",
            "Focus on your actions and empathy, not the colleague's flaws.",
            "Leadership is about influence — describe how you rallied others.",
            "Show planning, prioritisation, and calm under pressure.",
            "Describe how you sought to understand their perspective first.",
            "Show self-awareness and how you used the feedback to change.",
            "Walk through your thinking — interviewers value reasoning.",
            "Be specific and quantify results where possible.",
        ],
    },
    'technical': {
        'questions': [
            "Walk me through how you would design a scalable web application.",
            "How do you approach debugging a complex issue you've never seen before?",
            "Explain object-oriented programming in simple terms.",
            "What is the difference between a process and a thread?",
            "How do you ensure code quality in a team environment?",
            "Explain REST APIs and when you would use them.",
            "What is your experience with version control systems like Git?",
            "How would you explain recursion to someone non-technical?",
        ],
        'tips': [
            "Think aloud — interviewers value your reasoning as much as the answer.",
            "Show a systematic approach: reproduce, isolate, test, fix, verify.",
            "Use a relatable analogy to show depth of understanding.",
            "Processes are independent; threads share memory within a process.",
            "Mention code reviews, linting, tests, and documentation.",
            "REST = stateless, resource-based. Compare with GraphQL if relevant.",
            "Mention branching strategies and how you handle merge conflicts.",
            "Use a simple analogy like Russian nesting dolls.",
        ],
    },
}


def generate_topic(category: str = '', difficulty: str = '', exclude_history: list = None) -> str:
    """
    Generate a speaking topic.
    If Gemini AI is available, generates a dynamic topic avoiding history.
    Otherwise, falls back to randomised selection from the topic bank.
    """
    if not exclude_history:
        exclude_history = []
        
    if is_ai_available():
        model = get_gemini_model("gemini-2.5-flash")
        if model:
            try:
                cat_desc = f"in the category of '{category}'" if category else "on any interesting topic"
                diff_desc = f"for a '{difficulty}' speaker" if difficulty else ""
                history_desc = f" Avoid these specific topics: {', '.join(exclude_history)}." if exclude_history else ""
                
                prompt = (
                    f"Generate a single creative and engaging public speaking prompt {cat_desc} {diff_desc}."
                    " The prompt should be a question or a short statement suitable for a speech/impromptu speaking practice."
                    f"{history_desc}"
                    " Return ONLY the topic text, nothing else. No intro, no quotes, no markdown."
                )
                
                response = model.generate_content(prompt)
                topic = response.text.strip()
                # Clean up quotes if returned
                if topic.startswith('"') and topic.endswith('"'):
                    topic = topic[1:-1].strip()
                if topic.startswith("'") and topic.endswith("'"):
                    topic = topic[1:-1].strip()
                if topic:
                    return topic
            except Exception as e:
                print(f"[GEMINI TOPIC GENERATOR ERROR] {e}. Falling back to static list.")
                
    # Fallback / Static selection logic
    cats  = [category] if category and category in TOPIC_BANK else list(TOPIC_BANK.keys())
    diffs = [difficulty] if difficulty in ('beginner', 'intermediate', 'advanced') else ['beginner', 'intermediate', 'advanced']

    pool = []
    for c in cats:
        for d in diffs:
            pool.extend(TOPIC_BANK[c][d])

    # Filter out history
    filtered_pool = [t for t in pool if t not in exclude_history]
    if not filtered_pool:
        filtered_pool = pool

    if not filtered_pool:
        return "What does it mean to communicate with confidence?"

    return random.choice(filtered_pool)


def get_interview_question(q_type: str = 'hr', exclude_history: list = None) -> dict:
    """
    Return an interview question with an accompanying tip.
    If Gemini AI is available, generates a dynamic question and tip avoiding history.
    Otherwise, falls back to randomised selection from the interview bank.
    """
    if not exclude_history:
        exclude_history = []
        
    if is_ai_available():
        model = get_gemini_model("gemini-2.5-flash")
        if model:
            try:
                type_desc = {
                    'hr': "human resources / general fit",
                    'behavioral': "behavioral (evaluating past actions, soft skills, STAR method)",
                    'technical': "technical / problem solving / system design"
                }.get(q_type, q_type)
                
                history_desc = f" Avoid these specific questions: {', '.join(exclude_history)}." if exclude_history else ""
                
                prompt = (
                    f"Generate a single professional interview question of type '{type_desc}' and a short helpful tip on how to answer it."
                    f"{history_desc}"
                    " Return the result ONLY as a JSON object with exactly two keys: 'question' and 'tip'. "
                    "Do not include any markdown formatting like ```json or anything else. Just the raw JSON object."
                )
                
                response = model.generate_content(prompt)
                text = response.text.strip()
                # Clean markdown code block wraps if LLM returns them
                if text.startswith("```"):
                    lines = text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()
                    
                data = json.loads(text)
                if 'question' in data and 'tip' in data:
                    return {
                        'question': data['question'],
                        'tip': data['tip'],
                        'type': q_type
                    }
            except Exception as e:
                print(f"[GEMINI INTERVIEW QUESTION ERROR] {e}. Falling back to static list.")
                
    # Fallback to static selection
    bank = INTERVIEW_BANK.get(q_type, INTERVIEW_BANK['hr'])
    pool = list(zip(bank['questions'], bank['tips']))
    
    # Filter by history
    filtered_pool = [item for item in pool if item[0] not in exclude_history]
    if not filtered_pool:
        filtered_pool = pool
        
    idx = random.randrange(len(filtered_pool))
    q, tip = filtered_pool[idx]
    
    return {
        'question': q,
        'tip':      tip,
        'type':     q_type,
    }



# ── FUTURE ML HOOK ─────────────────────────────────────────────
def generate_topic_ml(category: str, difficulty: str, model=None) -> str:
    """
    Placeholder for transformer-based topic generation.
    
    Example implementation with a fine-tuned GPT-2 / T5:
    
        from transformers import pipeline
        generator = pipeline('text-generation', model='your-fine-tuned-model')
        prompt    = f"Generate a {difficulty} speaking topic about {category}:"
        result    = generator(prompt, max_new_tokens=60, do_sample=True)[0]['generated_text']
        return result.split(':')[-1].strip()
    
    For now, falls back to the curated bank.
    """
    return generate_topic(category, difficulty)
