# Family Financial Memory OS (Voice-First Household Finance)

Family Financial Memory OS is a multilingual, voice-first money memory assistant designed for Indian households. 

It enables family members to log transactions, query budgets, save towards goals, and get financial literacy guidance using voice calls in their preferred language. The system features a **Next.js Dashboard** (Trust Layer) to view the ledger, verify low-confidence records, review call logs/transcripts, and manage family profiles.

---

## Models & Tech Stack

### 🤖 Voice AI Models & Agent Configuration
- **Voice AI Platform**: [Bolna](https://bolna.ai) Voice AI engine with custom API tool integration.
- **Large Language Model (LLM)**: `gpt-4o-mini` (via Azure OpenAI)
  - *Used for real-time conversational reasoning, transaction extraction, and multilingual translation.*
- **Speech-to-Text (STT)**: Deepgram (`nova-3` model)
  - *Provides ultra-low latency transcription across English, Hindi, Tamil, Telugu, and Malayalam.*
- **Text-to-Speech (TTS)**: ElevenLabs (`eleven_turbo_v2_5`)
  - *Configured with the "Devi" voice profile for a natural, culturally-resonant Indian accent.*
- **Agent IDs**:
  - *Primary Agent*: `b196f7c8-7fb6-4880-9984-4b430e4c01a9`

### ⚙️ Backend Architecture (The Brain)
- **Framework**: FastAPI (Python 3.10+) running uvicorn.
- **Role**: Handles business logic, identity resolution, budget checks, real-time database commits, and background insights.
- **Hosting**: Render (Web Service)

### 💻 Frontend Architecture (The Dashboard)
- **Framework**: Next.js (React 19)
- **Styling**: Vanilla CSS + `lucide-react` for iconography.
- **Role**: A responsive, live-updating dashboard to view financial history, goals, and real-time transcripts.
- **Hosting**: Vercel

### 🗄️ Database
- **Provider**: Supabase (PostgreSQL)
  - *(Also supports local SQLite `family_memory.db` for offline development)*
- **Role**: Persists the family money memory. Stores members, shared budgets, active debts, savings goals, and raw voice-call transcripts for auditability.

---

## Project Structure

- `/bolna`: Contains agent configurations and multilingual system prompts (`system_prompts.json`).
- `/backend`: FastAPI service:
  - `main.py`: App entry point.
  - `database.py`: Core DB operations with SQLite and Supabase wrapper functions.
  - `deploy_agent.py`: Agent creation and registration script on Bolna.
  - `routes/tools.py`: Endpoints invoked by Bolna as custom API tools.
  - `routes/webhook.py`: Observability and logging post-call webhook receiver.
  - `routes/trust.py`: Backend API endpoints for Next.js dashboard CRUD and reset actions.
  - `routes/insights.py`: Background insight engine generating family savings ideas.
- `/frontend`: Next.js web application.

---

## Core Implementations & Features

### 1. Seeded Family Members (The Sharma Family)
- **Ramesh** (Father) — Phone: `+919449694564` — Preferred Language: English
- **Sunita** (Mother) — Phone: `+919538133265` — Preferred Language: Hindi
- **Hari** (Son) — Phone: `+919538133265` — Preferred Language: English
- **Prakash** (Brother) — Phone: `+917760599655` — Preferred Language: English

> [!NOTE]
> Sunita and Hari share the phone number `+919538133265` to test and demonstrate **Shared-Line Identity Resolution** (the voice agent prompts them to state their name to confirm identity before logging).

### 2. Multilingual Voice Support
Supports 5 Indian languages with dynamic switching, language-specific welcome messages, and seamless handoffs:
- English (`en`)
- Hindi (`hi`)
- Tamil (`ta`)
- Telugu (`te`)
- Malayalam (`ml`)

### 3. Voice Custom API Tools (9 Registered Tools)
- **Logging (Real-time DB writes)**:
  - `record_expense`: Logs an expense in INR. Computes warning alerts if the budget category (Groceries, Fuel, Utilities, Tuition) is approaching or exceeding limits. Mark transactions using a three-tier confidence scale:
    - **High Confidence (>= 0.90)**: Auto-committed to DB.
    - **Medium/Low Confidence (< 0.90)**: Quarantined into `confirmation_requests` queue for manual dashboard review.
  - `record_debt`: Logs a loan or borrowing transaction between a member and a contact.
  - `goal_update`: Contributes savings to family goals (Vacation Savings, Emergency Fund, Education Fund, Vehicle Goal).
- **Retrieval (Read-only queries)**:
  - `budget_status`: Checks remaining category budget limits.
  - `spending_summary`: Summarizes spending by category, timeframe (week/month), or specific family member.
  - `financial_summary`: Holistic overview of monthly spending, top categories, debts, and goals progress.
  - `goal_status`: Queries current progress towards savings milestones.
  - `debt_guidance`: Analyzes outstanding debts and returns repayment strategies.
- **Guidance**:
  - `get_financial_literacy`: Explains safe Indian financial instruments (PPF, FD, RD, Sukanya Samriddhi Yojana, compound interest, emergency funds). Strict guardrails prevent stocks, crypto, or trading advice.

### 4. System Placeholders & Webhook Details
- **Call ID Injection**: Custom tool parameters map `call_id` to `%(call_sid)s`. This utilizes Bolna's system-level call placeholder to prevent LLM hallucinations and enforce database idempotency.
- **Caller ID Injection**: Tool configuration hardcodes the `phone_number` parameter to a default family number. Speaker name confirmation (`member_name`) is then resolved on the backend to match the correct user profile.
- **Read-Only Webhook**: The post-call webhook (`/api/webhook/bolna`) is strictly read-only. It saves call transcripts, recording URLs, and metadata to the database for observability, auditing, and timeline displays. This prevents duplicate writes since transactions are already committed in real-time during the call.

### 5. Next.js Trust Layer Dashboard
- **Overview**: Highlights core metrics, monthly budget limits, goals progress, and pending confirmation alerts.
- **Ledger & Debts Tab**: Displays confirmed transactions, loans, and allows manual edit/delete updates.
- **Budgets & Goals Tab**: Displays monthly budget consumption and savings goals progress. Includes full CRUD capabilities to add, edit, and delete budget categories and individual family savings goals.
- **Confirmation Queue**: Displays quarantined low/medium confidence events. Family members can edit the details and confirm or discard them.
- **Assistant Tab**: A voice-only layout simulator console to test commands by typing and selecting the active speaker and language.
- **Voice Logs Tab**: Timeline listing call records, transcription lines, and embedded audio player controls. (Inbound testing line: +91 92621 71465).
- **Profiles Tab**: Form-based settings to edit the global Family Name, and edit family member configurations (Names, Roles, Numbers, and Languages).
- **Outbound Calling Form**: Triggers a simulated outbound call to a selected member using the Bolna telephony API.
- **Clear Database**: Resets all transactions, debts, confirmation requests, and timelines, and zeroes out goal contributions.

### 6. Database Reseed & Safety
- SQLite schema generation is idempotent and runs automatically when the backend starts.
- Seeding default Sharma Family records is controlled by a flag (`init_sqlite_db(seed_data=False)` is default). Seeding does not auto-run on every reload, ensuring that clearing the database through the dashboard does not result in demo data silently reappearing later.

---

## Setup & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Bolna API Key (set in `.env`)

### 1. Run the FastAPI Backend
```bash
# Navigate to backend folder
cd backend

# Create virtualenv and install dependencies
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Start the FastAPI server on port 8000
.\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Expose Port & Deploy Agent Configuration
To receive voice call tool executions and post-call webhooks, expose port 8000 and upload the agent profile:
```bash
# Start a local tunnel to obtain a public URL
npx -y localtunnel --port 8000

# In a new terminal, deploy to Bolna with the public URL
.\backend\venv\Scripts\python backend/deploy_agent.py <YOUR_TUNNEL_URL>
```

### 3. Run the Next.js Frontend
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies and start server
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Run Automated E2E Tests
To run the automated test suite verifying logging, retrieval, shared line resolution, review queue, and idempotency:
```bash
# Run pytest from the root folder (uses isolated test_family_memory.db)
.\backend\venv\Scripts\python -m pytest backend/test_e2e.py
```
