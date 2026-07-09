# AI-First CRM — HCP Module (Log Interaction Screen)

An AI-first CRM module that lets pharmaceutical field representatives log interactions with
Healthcare Professionals (HCPs) either through a **structured manual form** or a **conversational
AI assistant** — both writing to the same backend data model, so the two workflows stay in sync.

Built for the "AI-First CRM HCP Module – Log Interaction Screen" technical assignment.

---

## 1. Project Overview

Field reps need to log every HCP touchpoint (visit, call, email) with structured details — topics
discussed, materials/samples shared, sentiment, outcomes, and follow-up plans. Typing all of this
into a rigid form is slow. This project lets a rep instead just **describe what happened in plain
English** to an AI chat assistant, which uses an LLM (Groq `gemma2-9b-it`) orchestrated through
**LangGraph** to understand intent, extract structured fields, and update the form automatically —
while the manual form remains fully available and editable at any time.

---

## 2. Architecture Diagram

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│           FRONTEND          │        │            BACKEND            │
│  React + Redux Toolkit       │  HTTP  │           FastAPI              │
│                              │◄──────►│                                │
│  ┌────────────┐ ┌─────────┐ │        │  ┌──────────┐   ┌───────────┐ │
│  │ Interaction │ │  Chat   │ │        │  │  Routes  │──►│ Interaction│ │
│  │   Form      │ │Assistant│ │        │  │ /api/*   │   │  Service   │ │
│  │ (left pane) │ │(right)  │ │        │  └────┬─────┘   └─────┬─────┘ │
│  └──────┬──────┘ └────┬────┘ │        │       │               │       │
│         │             │      │        │       ▼               ▼       │
│    Redux Store ◄──────┘      │        │  LangGraph Agent   PostgreSQL │
│  (interaction, chat state)   │        │  ┌──────────────┐  /MySQL DB  │
└─────────────────────────────┘        │  │ Router Node  │             │
                                        │  │ (LLM decides │             │
                                        │  │   intent)    │             │
                                        │  └──────┬───────┘             │
                                        │         ▼                     │
                                        │  ┌────────────────────────┐  │
                                        │  │ 5 Tools:               │  │
                                        │  │ Log / Edit / Search /  │  │
                                        │  │ History / Follow-up    │  │
                                        │  └───────────┬────────────┘  │
                                        │              ▼                │
                                        │        Groq API (LLM)         │
                                        └───────────────────────────────┘
```

**Sync flow:** whenever the AI assistant (chat) triggers a tool that changes interaction data,
the response flows `FastAPI → Redux Store → React Form`, so the left-side form updates
immediately without a page refresh — this is what keeps both workflows synchronized.

---

## 3. Folder Structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route definitions
│   │   ├── core/           # config.py, llm_client.py (Groq wrapper)
│   │   ├── database/       # SQLAlchemy engine/session setup
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # DB business logic (shared by API + tools)
│   │   ├── tools/          # 5 LangGraph tools
│   │   ├── langgraph/      # graph.py — router + dispatch nodes
│   │   ├── prompts/        # LLM prompt templates
│   │   ├── utils/          # logger.py
│   │   └── main.py         # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # InteractionForm.jsx, ChatAssistant.jsx
│   │   ├── pages/          # LogInteractionPage.jsx
│   │   ├── redux/          # store.js, slices/
│   │   ├── services/       # api.js (Axios)
│   │   └── main.jsx, App.jsx, index.css
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── .gitignore
└── README.md
```

---

## 4. Features

- **Split-screen UI**: editable structured form (left) + conversational AI assistant (right)
- **Dual logging workflows** writing to the same database table/model
- **LangGraph-orchestrated agent** with LLM-based intent routing (no keyword/if-else routing)
- **5 LangGraph tools**: Log Interaction, Edit Interaction, Search Interaction, View History,
  Follow-up Recommendation
- **Groq `gemma2-9b-it`** as primary model, with automatic fallback to
  `llama-3.3-70b-versatile` if a call fails
- **Redux Toolkit** state management with automatic form sync when the AI updates data
- Clean layered backend: routes → services → database, with tools reusing the same service layer
- Structured logging, typed Pydantic schemas, and consistent error handling throughout

---

## 5. Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or MySQL) — or just use SQLite for quick local testing, no install needed
- A free Groq API key: https://console.groq.com

### Clone
```bash
git clone <your-repo-url>
cd hcp-crm
```

---

## 6. Environment Variables

**backend/.env** (copy from `backend/.env.example`):
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=gemma2-9b-it
GROQ_MODEL_FALLBACK=llama-3.3-70b-versatile

# Easiest local option (no DB server needed):
DATABASE_URL=sqlite:///./hcp_crm.db

# Or Postgres:
# DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/hcp_crm

# Or MySQL:
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/hcp_crm

APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**frontend/.env** (copy from `frontend/.env.example`):
```
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 7. Running the Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste in your real GROQ_API_KEY

uvicorn app.main:app --reload --port 8000
```

Backend will be live at **http://localhost:8000** (interactive API docs at
**http://localhost:8000/docs**). Tables are created automatically on startup — no manual
migration step needed for this project's scale.

---

## 8. Running the Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend will be live at **http://localhost:5173**.

---

## 9. Running PostgreSQL Locally (optional — skip if using SQLite)

```bash
# Install (Ubuntu example)
sudo apt install postgresql

# Start the service, then create the database:
sudo -u postgres psql
CREATE DATABASE hcp_crm;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE hcp_crm TO postgres;
\q
```
Then set `DATABASE_URL` in `backend/.env` to match. For MySQL, create the database similarly and
use a `mysql+pymysql://` URL instead — SQLAlchemy handles both with no code changes.

---

## 10. Groq API Setup

1. Go to https://console.groq.com and sign up (free).
2. Create a new API key.
3. Paste it into `backend/.env` as `GROQ_API_KEY`.
4. The app uses `gemma2-9b-it` by default, and automatically retries with
   `llama-3.3-70b-versatile` if the primary model call fails.

---

## 11. LangGraph Overview

The agent is a small two-node graph (`backend/app/langgraph/graph.py`):

1. **Router node** — sends the user's message to the LLM with a system prompt describing all 5
   tools, and asks it to return which tool applies as JSON. This is a pure LLM decision — there is
   no keyword matching or hardcoded if/else intent logic anywhere in the routing code.
2. **Dispatch node** — calls whichever tool function the router selected, using the shared
   `interaction_service` for all DB reads/writes.

### The 5 Tools (`backend/app/tools/`)

| Tool | Responsibility |
|---|---|
| **Log Interaction** | Extracts structured fields (HCP name, type, date, topics, materials, samples, sentiment, outcomes, follow-up) from free text via the LLM, validates with Pydantic, saves to DB. |
| **Edit Interaction** | Given an existing interaction + a natural-language correction, asks the LLM to identify *only* the changed fields, and applies a partial update — all other fields are preserved untouched. |
| **Search Interaction** | Extracts an HCP name and/or date from the message, then runs a deterministic DB query (no LLM guessing on the actual matching) to return results. |
| **View History** | Returns the full chronological interaction history, optionally filtered to one HCP. |
| **Follow-up Recommendation** | Feeds an HCP's full interaction history to the LLM and asks for next-visit timing, materials, samples, talking points, and follow-up actions — the one genuinely generative tool in the set. |

---

## 12. Available APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/interactions` | Create interaction (manual form) |
| GET | `/api/interactions` | List all interactions |
| GET | `/api/interactions/{id}` | Get one interaction |
| PUT | `/api/interactions/{id}` | Update interaction (manual form) |
| DELETE | `/api/interactions/{id}` | Delete interaction |
| POST | `/api/chat` | Conversational entry point — runs the LangGraph agent, returns a natural-language reply + any updated/found data |
| POST | `/api/langgraph/execute` | Runs the graph directly and returns the raw tool result (handy for demoing each tool individually) |

Full interactive docs (Swagger UI) are auto-generated by FastAPI at `/docs` once the backend is
running.

---

## 13. Example Chat Prompts (for testing / demo)

- *Log:* "Met Dr. Ayesha Rao in person today, discussed the new cardiology drug, shared brochures
  and 2 sample packs, she seemed positive, follow up in 2 weeks."
- *Edit:* "Actually change the sentiment to neutral and add that she asked for pricing info."
- *Search:* "Show me all interactions with Dr. Rao."
- *History:* "Show my full interaction history."
- *Follow-up:* "What should I do for my next visit with Dr. Rao?"

---

## 14. Screenshots

*(Add screenshots of the running app here before submitting — e.g. `frontend/screenshot-form.png`,
`screenshot-chat.png` — and reference them below.)*

```markdown
![Form and Chat Split Screen](./screenshot-1.png)
```

---

## 15. Future Improvements

- Alembic migrations instead of `create_all` for safer schema evolution
- Authentication/authorization (multi-rep accounts, role-based access)
- Streaming chat responses (token-by-token) for a more ChatGPT-like feel
- Vector-store-backed memory so the assistant can reference interactions semantically, not just
  by exact name/date match
- Pagination and filtering UI for the interaction history view
- Unit + integration tests for tools and API routes

---

## 16. Pushing This Project to GitHub

```bash
cd hcp-crm
git init
git add .
git commit -m "Initial commit: AI-First CRM HCP Module"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

(Create the empty repo on GitHub first at https://github.com/new — don't initialize it with a
README there, since this project already has one.)

---

## 17. What to Submit

Per the assignment's Google Form (https://forms.gle/XdvLNBJkbdVDGADM8):

1. **GitHub repository link** — the repo you just pushed above, containing this whole
   `frontend/` + `backend/` project and this README.
2. **Video recording (10–15 min)** covering:
   - Frontend walkthrough (show the split-screen form + chat working)
   - Demo of all 5 LangGraph tools actually running (Log, Edit, Search, History, Follow-up)
   - Brief code/architecture explanation (this README's diagram + folder structure is a good
     script to follow)
   - **A short summary, in your own words, of what you understood the task to be asking for** —
     the instructor's brief explicitly asks for this, so say it out loud on camera even though
     it's not something you code (e.g., "the goal was to give field reps two equally valid ways to
     log HCP interactions — form or conversation — while an LLM-orchestrated LangGraph agent keeps
     both in sync using tools for logging, editing, searching, history, and follow-up
     recommendations").
