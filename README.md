# 🕊️ Selah — Live Telecast Copilot for Church Media Volunteers

> **The pastor picks the songs. Selah makes sure the livestream doesn't get muted, the slides are ready, and the paperwork is done.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Agentic_Cinema-4285F4?logo=googlecloud&logoColor=white)](https://agentic-cinema.devpost.com/)
[![Parallel Track](https://img.shields.io/badge/Partner_Track-Parallel_Search-6366F1)](https://parallel.ai)
[![Gemini](https://img.shields.io/badge/Model-Gemini_3.5_Flash-8E75B2?logo=google&logoColor=white)](https://ai.google.dev/)

---

## 📖 The Problem

A small or medium church can hold every music license correctly (such as CCLI Copyright & Streaming licenses) and **still get muted, claimed, or copyright-striked on YouTube**. 

Why? **CCLI licensing has zero connection to YouTube's automated Content ID algorithm.** 

Meanwhile, Sunday morning livestreams are run by volunteers (often teenagers or retirees) who just need to present slides. When an automated copyright strike lands or audio gets muted mid-service, panic ensues.

### Selah's Hard Boundary:
**Selah never chooses the worship. It serves it.**  
The agent **never** suggests, recommends, ranks, or substitutes songs. Input is always the exact set list the pastor or worship leader chose. Red-verdict songs present **clear operational choices for humans** (mute stream audio during the song, confirm CCLI streaming coverage, or verify public domain arrangements) — *never alternative songs*.

---

## 🏛️ Autonomous Agent Architecture & SDK Runtime Usage

Selah is built for the **Google Cloud "Agentic Cinema" Hackathon (Parallel Partner Track)**. All AI orchestration and web research use official Google and Parallel runtime SDKs:

```
                                  Pastor / Worship Team
                                            │
                                (Pasted Text or Photo)
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────┐
                    │    Act 1: Multimodal Setlist Intake          │
                    │    [backend/app/agents/setlist_agent.py]     │
                    │    • Powered by google-genai 2.18.1          │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
             ┌─────────────────────────────────────────────────────────────┐
             │       Autonomous Licensing & Rights Research Agent          │
             │       [backend/app/agents/licensing_agent.py]               │
             │       • Orchestrated by google-adk 2.7.0 (InMemoryRunner)   │
             │       • Concurrent research via asyncio.gather              │
             └──────────────────────┬──────────────────────────────┬───────┘
                                    │                              │
                     Calls Tool via ADK             2-Axis Copyright &
                                    │               Content ID Verdicts
                                    ▼                              │
     ┌─────────────────────────────────────────────┐               │
     │      Parallel Search Web API Service        │               │
     │      [backend/app/services/parallel_client.py│               │
     │      • Official parallel-web 1.3.0 SDK      │               │
     └─────────────────────────────────────────────┘               ▼
                                            ┌──────────────────────────────────────────────┐
                                            │     Act 1: Slide Pack & Transliteration      │
                                            │     [backend/app/agents/pack_agent.py]       │
                                            │     • Strict Public Domain Lyrics Policy     │
                                            │     • Indic Script Phonetic Transliterations │
                                            └──────────────────────┬───────────────────────┘
                                                                   │
                                                                   ▼
                                            ┌──────────────────────────────────────────────┐
                                            │     Act 2: Broadcast Console & OBS Output    │
                                            │     [frontend/src/pages/ConsolePage.jsx]     │
                                            │     • Go-Live Guard (Unresolved Song Lock)   │
                                            │     • BroadcastChannel Instant Screen Sync   │
                                            │     • Live Elapsed Time & YouTube Chapters   │
                                            └──────────────────────┬───────────────────────┘
                                                                   │
                                                                   ▼
                                            ┌──────────────────────────────────────────────┐
                                            │     Act 3: Post-Broadcast Close-Out Pack     │
                                            │     [backend/app/agents/closeout_agent.py]   │
                                            │     • YouTube Description + Attributions     │
                                            │     • CCLI Usage Log & Dispute Statements    │
                                            └──────────────────────────────────────────────┘
```

### Verified Runtime Code Locations:
1. **Google ADK (`google-adk`)**:
   - [`backend/app/agents/licensing_agent.py`](backend/app/agents/licensing_agent.py) — Defines `Agent(tools=[search_licensing_web])` and executes asynchronously with `InMemoryRunner.run_debug()`.
2. **Google GenAI (`google-genai`)**:
   - [`backend/app/services/gemini_client.py`](backend/app/services/gemini_client.py) — Native Gemini client with structured Pydantic schema validation.
   - [`backend/app/agents/setlist_agent.py`](backend/app/agents/setlist_agent.py) — Multimodal image + text intake.
   - [`backend/app/agents/pack_agent.py`](backend/app/agents/pack_agent.py) — Slide proofreading & Latin transliteration for Indic scripts.
   - [`backend/app/agents/closeout_agent.py`](backend/app/agents/closeout_agent.py) — Compliance packaging and legal dispute paragraph generator.
3. **Parallel Search SDK (`parallel-web`)**:
   - [`backend/app/services/parallel_client.py`](backend/app/services/parallel_client.py) — Calls `Parallel(api_key).search()` with objective-driven search queries and trimmed citations (~900 chars).
4. **No Non-Google AI**: 100% powered by Gemini (`gemini-3.5-flash`). Zero OpenAI, Anthropic, or third-party AI audio-fingerprinting dependencies.

---

## ✨ Key Features & The 3-Act Workflow

### Act 1: Prepare (Intake & Rights Guard)
- **Multimodal Setlist Ingestion**: Accepts raw typed text, WhatsApp messages, or photos of handwritten song lists.
- **Two-Axis Verdicts**:
  - 🟢 **Covered**: Covered under church's held licenses.
  - 🟡 **Public Domain**: Hymn text is PD, but highlights Content ID match risk and mitigation.
  - 🔴 **Needs License**: Calls out missing streaming license tiers (e.g. CCLI Streaming vs base Copyright license).
- **Cited Sources**: Every claim links to verified web sources from Parallel Search.
- **Go-Live Guard**: Blocks broadcast until the operator selects an operational resolution for any red-verdict song.
- **Diaspora Transliteration**: Generates Latin phonetic lines under Indic script lyrics (Tamil, Malayalam, Telugu, Hindi) for diaspora youth.

### Act 2: Broadcast (Operator Console & OBS Output)
- **Volunteer Operator Console** (`/console`): Clean, warm paper aesthetic (`#faf8f4`), big tactile buttons, keyboard shortcuts (`Space` / `→` / `←`).
- **OBS / vMix Output Screen** (`/output`): Clean dark presentation view, massive serif text, synced locally via `BroadcastChannel` with zero latency.
- **Live Chapter Marking**: One-click timestamps for "Welcome", "Worship", "Prayer", "Sermon", "Benediction".

### Act 3: Close Out (Compliance & Dispute Kit)
- **YouTube Description**: Pre-formatted with mandatory CCLI license attributions.
- **CCLI Reporting Log**: Markdown table ready to paste into the quarterly CCLI portal.
- **Content ID Dispute Pack**: Pre-drafted legal dispute statements citing public domain status or CCLI license coverage with Parallel search citations.
- **One-Click Export**: Downloadable `.md` compliance pack.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- Google AI Studio API Key (`GEMINI_API_KEY`)
- Parallel Search API Key (`PARALLEL_API_KEY`)

### 2. Clone & Configure
```bash
git clone https://github.com/N-45div/Selah.git
cd Selah

# Copy sample environment configuration
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GEMINI_API_KEY=your_google_gemini_api_key
PARALLEL_API_KEY=your_parallel_api_key
GEMINI_MODEL=gemini-3.5-flash
```

### 3. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run FastAPI backend
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend Setup (Vite + React)
In a second terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** (or `http://localhost:8000` after `npm run build`).

---

## 🧪 Acceptance Benchmark Tests

| Test Case | Setlist Input | Expected Verdict | Reason |
| :--- | :--- | :--- | :--- |
| **Test 1** | *In Christ Alone* (Keith Getty & Stuart Townend)<br>Church holds only "CCLI Copyright License" | 🔴 `needs_license`<br>Owner: Thankyou Music / Capitol CMG<br>CCLI #3350395 | CCLI Copyright License covers in-person projection only. Online streaming requires the CCLI Streaming License. |
| **Test 2** | *Amazing Grace* (John Newton) | 🟡 `public_domain`<br>Content ID Risk: Medium | Hymn text is PD (1779), but automated algorithms match contemporary recordings. Pre-drafted dispute statements provided. |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
