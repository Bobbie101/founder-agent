import os
import asyncio
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import root_agent

load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv("FLASK_SECRET", "founder-agent-secret")

session_service = InMemorySessionService()
# Store runners per user session
_runners = {}

async def get_or_create_runner(session_id: str):
    if session_id not in _runners:
        runner = Runner(
            agent=root_agent,
            app_name="founder_agent",
            session_service=session_service
        )
        adk_session = await session_service.create_session(
            app_name="founder_agent",
            user_id=session_id
        )
        _runners[session_id] = (runner, adk_session.id)
    return _runners[session_id]

async def chat_with_agent(session_id: str, message: str) -> str:
    runner, adk_session_id = await get_or_create_runner(session_id)
    result = ""
    async for event in runner.run_async(
        user_id=session_id,
        session_id=adk_session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=message)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                result = event.content.parts[0].text
    return result

@app.route("/")
def index():
    if "session_id" not in session:
        import uuid
        session["session_id"] = str(uuid.uuid4())[:8]
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    session_id = session.get("session_id", "default")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = asyncio.run(chat_with_agent(session_id, message))
        return jsonify({"response": response, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/progress/<name>")
def progress(name):
    from tools import get_founder
    result = get_founder(name, "000000")
    return jsonify(result)

@app.route("/api/check/<name>")
def check_founder(name):
    from tools import founders
    founder = founders.find_one({"name": name}, {"_id": 0, "pin_hash": 1})
    if founder and founder.get("pin_hash"):
        return jsonify({"exists": True})
    return jsonify({"exists": False})

@app.route("/api/verify", methods=["POST"])
def verify_pin():
    import hashlib
    data = request.json
    name = data.get("name")
    pin = data.get("pin")
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    from tools import founders, calculate_investor_score
    founder = founders.find_one({"name": name, "pin_hash": pin_hash})
    if not founder:
        return jsonify({"success": False, "message": "Incorrect PIN"})
    completed = [k for k, v in founder['milestones'].items() if v['completed']]
    remaining = [k for k, v in founder['milestones'].items() if not v['completed']]
    next_step = remaining[0].replace("_", " ").title() if remaining else "All milestones complete!"
    return jsonify({
        "success": True,
        "name": founder['name'],
        "investor_score": founder['investor_score'],
        "milestones": founder['milestones'],
        "next_step": next_step,
        "message": f"Welcome back {founder['name']}! You've completed {len(completed)} of 6 milestones. Next up: {next_step}."
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
