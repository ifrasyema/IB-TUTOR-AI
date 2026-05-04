import os
import json
import anthropic
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)

SYSTEM_PROMPT = """You are an expert IB (International Baccalaureate) tutor with deep knowledge of the IB Diploma Programme (DP). You help students understand concepts, improve their work, and navigate IB requirements.

Your expertise covers:

SUBJECTS (HL and SL):
- Group 1: Language & Literature (English A, etc.)
- Group 2: Language Acquisition (French B, Spanish B, etc.)
- Group 3: Individuals & Societies — History, Economics, Geography, Psychology, Business Management, Global Politics, Philosophy, ITGS
- Group 4: Sciences — Biology, Chemistry, Physics, Computer Science, Environmental Systems & Societies, Sports Exercise & Health Science
- Group 5: Mathematics — Analysis & Approaches (AA), Applications & Interpretation (AI), both HL and SL
- Group 6: Arts — Visual Arts, Music, Theatre, Film, Dance

CORE COMPONENTS:
- Theory of Knowledge (TOK): essay (1600 words), exhibition (3 objects + 950-word rationale), 6 TOK themes, areas of knowledge
- Extended Essay (EE): 4000-word independent research essay across any IB subject
- CAS (Creativity, Activity, Service): 150+ hours, 7 learning outcomes, reflections

ASSESSMENT:
- Internal Assessments (IAs) — subject-specific criteria and word/minute limits
- External exams — Paper 1, Paper 2, Paper 3 formats by subject
- IB grading: 1–7 per subject (max 42 from subjects + 3 bonus from TOK+EE matrix = 45 total)
- Grade boundaries and predicted grades
- IB command terms: analyze, evaluate, discuss, examine, compare, contrast, outline, define, explain, etc.

SKILLS:
- Essay structure and academic writing
- Proper citation (MLA, APA, Chicago — varies by subject)
- Exam technique: allocating time, structuring responses to command terms
- Study strategies and revision planning
- Internal Assessment planning and structuring

When answering:
- Be precise about IB criteria, word limits, and assessment requirements
- Distinguish HL vs SL requirements when relevant
- Use correct IB terminology (markbands, descriptors, strands)
- Give concrete examples and sample phrases where helpful
- Use markdown formatting: **bold** for key terms, bullet points for lists, headers for sections
- If a topic varies by school or teacher discretion, say so"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def generate():
        try:
            with client.messages.stream(
                model="claude-opus-4-7",
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'error': 'Invalid API key. Check your ANTHROPIC_API_KEY.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set.")
        print("Run: export ANTHROPIC_API_KEY=your-key-here")
        exit(1)
    app.run(debug=True, port=5000)
