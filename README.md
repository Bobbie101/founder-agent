# 🚀 First-Time Founder Agent

> The mentor every first-time founder never had.

Built for the **Google Cloud Rapid Agent Hackathon** · MongoDB Partner Track  
Team: [@wolfworldrun](https://github.com/wolfworldrun) · [@Bobbie101](https://github.com/Bobbie101)

---

## What It Does

You describe your business idea. The agent does the heavy lifting — searching real market data, storing your progress, generating documents, and walking you step by step from "I have an idea" to "I'm ready to pitch."

It doesn't give generic advice. It thinks like a mentor — blending the frameworks of **Steve Jobs** (clarity and craft), **Elon Musk** (first principles and urgency), and **Bill Gates** (systems and market reality).

---

## Features

| Step | Feature | Status |
|------|---------|--------|
| 1 | Idea intake + timestamped profile | ✅ |
| 2 | Launch mentality coaching (YC framework) | ✅ |
| 3 | Idea clarity — one sentence, one customer, one problem | ✅ |
| 4 | Do things that don't scale — get first 10 customers manually | ✅ |
| 5 | Customer discovery — 5 sharp interview questions | ✅ |
| 6 | Idea protection checklist | ✅ |
| 7 | Market validation — real data via Google Search | ✅ |
| 8 | Legal setup roadmap by country | ✅ |
| 9 | Investor readiness score (0–100 algorithm) | ✅ |
| 10 | PIN-secured profile resume via sidebar keypad | ✅ |
| 11 | Progress tracker with milestone ring | ✅ |
| 12 | Notes and resource saving | ✅ |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | Google ADK + Gemini 2.5 Flash (Vertex AI) |
| Orchestration | Google Agent Development Kit (ADK) |
| Database | MongoDB Atlas (`founder_agent` db) |
| DB Dev Layer | MongoDB MCP Server (Claude Code) |
| Search | Google Search tool (via ADK sub-agent) |
| Backend | Python + Flask |
| Frontend | HTML + CSS + Vanilla JS |
| Auth | SHA-256 hashed PIN per founder profile |

---

## Architecture

```
User (Browser)
      ↓
Flask App (src/app.py)
      ↓
Google ADK Runner
      ↓
root_agent (Gemini 2.5 Flash)
      ├── search_agent (Google Search sub-agent)
      └── tools.py (pymongo → MongoDB Atlas)

MongoDB MCP Server → Atlas (dev/admin layer via Claude Code)
```

---

## Project Structure

```
founder-agent/
├── src/
│   ├── agent.py          ← ADK agent + composite mentor personality
│   ├── tools.py          ← MongoDB tools (save, get, milestone, score)
│   └── app.py            ← Flask backend + API routes
├── templates/
│   └── index.html        ← Chat UI
├── static/
│   ├── style.css         ← Light theme, Space Grotesk + Inter
│   └── app.js            ← Chat logic + PIN keypad modal
├── .env                  ← secrets (never committed)
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.12+
- Node.js 23+
- Google Cloud project with Vertex AI enabled
- MongoDB Atlas cluster (M0 free tier works)

### 1. Clone and install

```bash
git clone https://github.com/Bobbie101/founder-agent.git
cd founder-agent
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the project root:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/?appName=your-app
FLASK_SECRET=any-random-string
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project your-gcp-project-id
gcloud auth application-default set-quota-project your-gcp-project-id
```

### 4. Run

```bash
PYTHONPATH=src python src/app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## MongoDB Collections

| Collection | What's stored |
|-----------|--------------|
| `founders` | Founder profile, idea, milestones, investor score, hashed PIN |
| `notes` | Founder-saved notes from conversations |
| `resources` | Links auto-saved by agent during research |

---

## MongoDB MCP Server

The MongoDB MCP Server is configured for Claude Code as the developer/admin layer. It allows direct natural language queries to the Atlas cluster during development.

```bash
# Setup (already done — config lives in ~/.claude.json)
npx -y mongodb-mcp-server setup
```

---

## Mentor Personality

The agent blends three frameworks:

- **Steve Jobs** — Obsessed with simplicity. If it can't be said in one sentence, it isn't ready. Pushes for what makes something *insanely great*.
- **Elon Musk** — First principles thinking. Strips every assumption. "But WHY is it done that way?"
- **Bill Gates** — Market reality and systems. Data-driven. "Your most unhappy customers are your greatest source of learning."

---

## Team

| Name | GitHub | Role |
|------|--------|------|
| Wolf | [@wolfworldrun](https://github.com/wolfworldrun) | Agent prompts, MongoDB tools, Flask UI, PIN security, investor score algorithm |
| Bobbie | [@Bobbie101](https://github.com/Bobbie101) | Agent architecture, ADK setup, tools scaffolding, search sub-agent |

---

## Hackathon

**Google Cloud Rapid Agent Hackathon**  
Partner Track: MongoDB  
Deadline: June 11, 2026