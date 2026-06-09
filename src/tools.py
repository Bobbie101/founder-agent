import os
import hashlib
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['founder_agent']
founders = db['founders']
notes = db['notes']
resources = db['resources']

# ─────────────────────────────────────────────
# INVESTOR SCORE ALGORITHM
# ─────────────────────────────────────────────
def calculate_investor_score(founder: dict) -> int:
    score = 0

    # Problem clarity (20pts)
    if founder.get("problem") and len(founder["problem"]) > 20:
        score += 20

    # Market size (20pts) — market validated milestone
    if founder.get("milestones", {}).get("market_validated", {}).get("completed"):
        score += 20

    # Differentiation (20pts) — unfair advantage
    if founder.get("unfair_advantage") and len(founder["unfair_advantage"]) > 20:
        score += 20

    # Traction (20pts) — customer discovery milestone
    if founder.get("milestones", {}).get("customer_discovery", {}).get("completed"):
        score += 20

    # Founder-market fit (20pts) — why now
    if founder.get("why_now") and len(founder["why_now"]) > 20:
        score += 20

    return score


# ─────────────────────────────────────────────
# TOOL 1 — Save a new founder profile
# ─────────────────────────────────────────────
def save_founder(
    name: str,
    idea: str,
    problem: str,
    target_customer: str,
    why_now: str,
    unfair_advantage: str,
    pin: str
) -> dict:
    """
    Saves a founder's profile and business idea to MongoDB.
    Call this as soon as a founder shares their name and describes their idea.
    Always ask the founder to set a 4-digit PIN to secure their profile.
    This creates their permanent profile so progress is never lost.

    Args:
        name: The founder's full name
        idea: Their business idea in one clear sentence
        problem: The specific problem their idea solves
        target_customer: Who their ideal customer is
        why_now: Why this idea is relevant right now
        unfair_advantage: What makes them uniquely positioned to build this
        pin: A 4-digit PIN chosen by the founder to secure their profile

    Returns:
        Confirmation the profile was saved with their founder ID
    """
    existing = founders.find_one({"name": name})
    if existing:
        return {
            "status": "already_exists",
            "message": f"Profile already exists for {name}. Ask them for their PIN to retrieve it."
        }

    pin_hash = hashlib.sha256(pin.encode()).hexdigest()

    founder_data = {
        "name": name,
        "idea": idea,
        "problem": problem,
        "target_customer": target_customer,
        "why_now": why_now,
        "unfair_advantage": unfair_advantage,
        "pin_hash": pin_hash,
        "idea_documented_at": datetime.now(),
        "investor_score": 0,
        "milestones": {
            "idea_clarity": {"completed": False, "completed_at": None},
            "idea_protected": {"completed": False, "completed_at": None},
            "market_validated": {"completed": False, "completed_at": None},
            "customer_discovery": {"completed": False, "completed_at": None},
            "legal_setup": {"completed": False, "completed_at": None},
            "investor_ready": {"completed": False, "completed_at": None}
        },
        "created_at": datetime.now()
    }

    # Calculate initial score
    initial_score = calculate_investor_score(founder_data)
    founder_data["investor_score"] = initial_score

    result = founders.insert_one(founder_data)

    return {
        "status": "saved",
        "founder_id": str(result.inserted_id),
        "investor_score": initial_score,
        "message": f"Profile created for {name}! Your idea is timestamped — this is your first line of protection. PIN saved securely.",
        "idea_documented_at": founder_data["idea_documented_at"].strftime("%B %d, %Y at %I:%M %p")
    }


# ─────────────────────────────────────────────
# TOOL 2 — Get a returning founder's profile
# ─────────────────────────────────────────────
def get_founder(name: str, pin: str) -> dict:
    """
    Retrieves a founder's full profile and progress from MongoDB.
    Use pin="000000" to check if a founder exists without revealing data.
    Only use a real PIN when doing full verification via the sidebar.

    Args:
        name: The founder's name to look up
        pin: Their 4-digit PIN, or "000000" to check existence only

    Returns:
        Their profile and progress, or existence check result
    """
    # Existence check only — no data returned
    if pin == "000000":
        founder = founders.find_one({"name": name})
        if not founder:
            return {
                "status": "not_found",
                "message": f"No profile found for {name}. They are a new founder."
            }
        return {
            "status": "exists",
            "message": f"Welcome back {name}! Please use the sidebar Resume field to load your profile securely."
        }

    # Full verification with PIN
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    founder = founders.find_one({"name": name, "pin_hash": pin_hash})

    if not founder:
        return {
            "status": "not_found",
            "message": f"No profile found for {name} with that PIN. Check the name and PIN and try again."
        }

    completed = [k for k, v in founder['milestones'].items() if v['completed']]
    remaining = [k for k, v in founder['milestones'].items() if not v['completed']]
    next_step = remaining[0].replace("_", " ").title() if remaining else "All milestones complete!"

    return {
        "status": "found",
        "name": founder['name'],
        "idea": founder['idea'],
        "problem": founder['problem'],
        "target_customer": founder['target_customer'],
        "why_now": founder['why_now'],
        "unfair_advantage": founder['unfair_advantage'],
        "idea_documented_at": founder['idea_documented_at'].strftime("%B %d, %Y"),
        "investor_score": founder['investor_score'],
        "completed_milestones": completed,
        "remaining_milestones": remaining,
        "next_step": next_step,
        "message": f"Welcome back {name}! Your idea has been on record since {founder['idea_documented_at'].strftime('%B %d, %Y')}. You've completed {len(completed)} of 6 milestones. Investor score: {founder['investor_score']}/100. Next up: {next_step}."
    }


# ─────────────────────────────────────────────
# TOOL 3 — Update a milestone as complete
# ─────────────────────────────────────────────
def update_milestone(name: str, milestone: str) -> dict:
    """
    Marks a milestone as complete for a founder in MongoDB.
    Call this when a founder has genuinely completed a step.
    Automatically recalculates their investor readiness score.

    Available milestones:
    - idea_clarity
    - idea_protected
    - market_validated
    - customer_discovery
    - legal_setup
    - investor_ready

    Args:
        name: The founder's name
        milestone: The milestone name to mark complete

    Returns:
        Confirmation, new investor score, and next step
    """
    valid_milestones = [
        "idea_clarity", "idea_protected", "market_validated",
        "customer_discovery", "legal_setup", "investor_ready"
    ]

    if milestone not in valid_milestones:
        return {
            "status": "error",
            "message": f"Invalid milestone. Choose from: {valid_milestones}"
        }

    result = founders.update_one(
        {"name": name},
        {"$set": {
            f"milestones.{milestone}.completed": True,
            f"milestones.{milestone}.completed_at": datetime.now()
        }}
    )

    if result.modified_count == 0:
        return {
            "status": "error",
            "message": f"Could not find founder {name}."
        }

    # Recalculate investor score
    founder = founders.find_one({"name": name})
    new_score = calculate_investor_score(founder)
    founders.update_one(
        {"name": name},
        {"$set": {"investor_score": new_score}}
    )

    milestone_display = milestone.replace("_", " ").title()
    remaining = [k for k, v in founder['milestones'].items() if not v['completed'] and k != milestone]
    next_step = remaining[0].replace("_", " ").title() if remaining else "All milestones complete!"

    return {
        "status": "updated",
        "milestone_completed": milestone_display,
        "investor_score": new_score,
        "next_step": next_step,
        "message": f"Milestone complete: {milestone_display}! Investor score updated to {new_score}/100. Next: {next_step}."
    }


# ─────────────────────────────────────────────
# TOOL 4 — Save a founder's own note
# ─────────────────────────────────────────────
def save_note(name: str, note: str) -> dict:
    """
    Saves a note written by the founder to MongoDB.
    Call this when a founder wants to save a thought or decision.

    Args:
        name: The founder's name
        note: The note content to save

    Returns:
        Confirmation the note was saved
    """
    note_data = {
        "founder_name": name,
        "note": note,
        "type": "founder_note",
        "created_at": datetime.now()
    }

    notes.insert_one(note_data)

    return {
        "status": "saved",
        "message": f"Note saved!",
        "saved_at": note_data["created_at"].strftime("%B %d, %Y at %I:%M %p")
    }


# ─────────────────────────────────────────────
# TOOL 5 — Agent saves a resource it finds
# ─────────────────────────────────────────────
def save_resource(name: str, title: str, url: str, why_useful: str) -> dict:
    """
    Saves a useful resource found during research to MongoDB.
    Call this automatically whenever you find a genuinely useful link.

    Args:
        name: The founder's name
        title: The title of the resource
        url: The URL link
        why_useful: One sentence explaining why this is useful

    Returns:
        Confirmation the resource was saved
    """
    resource_data = {
        "founder_name": name,
        "title": title,
        "url": url,
        "why_useful": why_useful,
        "type": "agent_resource",
        "saved_at": datetime.now()
    }

    resources.insert_one(resource_data)

    return {
        "status": "saved",
        "message": f"Resource saved: {title}",
        "saved_at": resource_data["saved_at"].strftime("%B %d, %Y")
    }


# ─────────────────────────────────────────────
# TOOL 6 — Get all notes and resources
# ─────────────────────────────────────────────
def get_notes_and_resources(name: str) -> dict:
    """
    Retrieves all saved notes and resources for a founder.
    Call this when a founder asks to see their saved items.

    Args:
        name: The founder's name

    Returns:
        All their saved notes and resources
    """
    founder_notes = list(notes.find(
        {"founder_name": name},
        sort=[("created_at", -1)]
    ))

    founder_resources = list(resources.find(
        {"founder_name": name},
        sort=[("saved_at", -1)]
    ))

    formatted_notes = [{
        "note": n["note"],
        "saved_at": n["created_at"].strftime("%B %d, %Y at %I:%M %p")
    } for n in founder_notes]

    formatted_resources = [{
        "title": r["title"],
        "url": r["url"],
        "why_useful": r["why_useful"],
        "saved_at": r["saved_at"].strftime("%B %d, %Y")
    } for r in founder_resources]

    if not formatted_notes and not formatted_resources:
        return {
            "status": "empty",
            "message": f"No notes or resources saved yet for {name}."
        }

    return {
        "status": "found",
        "total_notes": len(formatted_notes),
        "total_resources": len(formatted_resources),
        "notes": formatted_notes,
        "resources": formatted_resources,
        "message": f"Here's everything saved for {name}: {len(formatted_notes)} notes and {len(formatted_resources)} resources."
    }