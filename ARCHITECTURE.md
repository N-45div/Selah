# 🕊️ Selah — Telecast Copilot System Architecture

> **Selah** is a production-grade live telecast copilot and copyright compliance engine designed for church media teams. It orchestrates autonomous AI research agents (`google-adk` + `google-genai` + `parallel-web`) to protect live Sunday worship streams from algorithmic copyright mutes, Content ID takedowns, and licensing violations across three synchronized acts.

---

## 🏛️ High-Level System Architecture

```mermaid
graph TD
    subgraph "Act 1: Pre-Broadcast Intake & Licensing Guard"
        UI_In["Setlist Intake UI (Image / Text / PCO)"] --> API_Plan["FastAPI /api/plan"]
        API_Plan --> SetlistAgent["Setlist Parsing Agent (Gemini 3.7 Flash)"]
        SetlistAgent --> LicAgent["Licensing & Musicology Agent (Google ADK + Parallel Search)"]
        LicAgent --> CCLI_DB["Parallel Web Search (CCLI SongSelect & Hymnary)"]
        LicAgent --> GuardVerdict["Progressive Rights Verdict (Green / Yellow / Red)"]
        GuardVerdict --> HumanInLoop["Human-in-the-Loop Resolution Gate"]
        HumanInLoop --> PackAgent["Slide Pack Agent (Lyrics + Indic Transliteration)"]
    end

    subgraph "Act 2: Live Telecast Operator Console"
        PackAgent --> LiveConsole["Live Operator Console (/console)"]
        LiveConsole --> BC_Chan["BroadcastChannel Engine (0ms Local Sync)"]
        BC_Chan --> OutputScreen["OBS Fullscreen Projection (/output)"]
        BC_Chan --> LowerThird["OBS Transparent Lower-Third (/output?mode=lower-third)"]
        BC_Chan --> StageHUD["Musician & Stage HUD (/stage)"]
        LiveConsole --> PPTX["16:9 Widescreen PowerPoint Exporter (.pptx)"]
        LiveConsole --> Pro7["ProPresenter 7 Bundle Exporter (.json)"]
    end

    subgraph "Act 3: Post-Broadcast Closeout & Dispute Defense"
        LiveConsole --> CloseoutAPI["FastAPI /api/plan/{id}/end"]
        CloseoutAPI --> CloseoutAgent["Closeout Agent (Gemini 3.7 Flash)"]
        CloseoutAgent --> YT_Desc["YouTube Description with CCLI Attribution"]
        CloseoutAgent --> Chapters["Timestamped YouTube Chapter Markers"]
        CloseoutAgent --> CCLI_Log["Quarterly CCLI Usage Reporting Log"]
        CloseoutAgent --> DisputeKit["Multi-Platform Dispute Kit (Content ID & Meta Appeals)"]
    end
```

---

## 🤖 Multi-Agent Orchestration & Data Pipeline

Selah utilizes specialized autonomous agents working in parallel to ensure broadcast integrity and legal safety:

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Church Media Operator
    participant Fast as FastAPI Backend
    participant Setlist as Setlist Agent (Gemini)
    participant Lic as Licensing Agent (ADK + Parallel)
    participant Pack as Slide Pack Agent (Gemini)
    participant Console as Live Console & OBS Display
    participant Closeout as Closeout Agent (Gemini)

    Operator->>Fast: Submit Sunday setlist (Handwritten photo / Text / PCO)
    Fast->>Setlist: Extract songs, authors, and language hints
    Setlist-->>Fast: Normalized song list [TC-01, TC-02, TC-04]
    
    par Autonomous Progressive Research
        Fast->>Lic: Research Song 1 (In Christ Alone)
        Lic->>Lic: Search CCLI & Parallel Deep Web
        Lic-->>Fast: Verdict: RED (Needs CCLI Streaming License)
    and
        Fast->>Lic: Research Song 2 (Amazing Grace)
        Lic->>Lic: Search Hymnary & Public Domain catalog
        Lic-->>Fast: Verdict: YELLOW (Public Domain)
    and
        Fast->>Lic: Research Song 3 (Enakkai Jeevan)
        Lic->>Lic: Search Tamil Christian Hymnary
        Lic-->>Fast: Verdict: GREEN (Covered with Transliteration)
    end

    Fast-->>Operator: Progressive Rights Verdicts Stream (SSE / Polling)
    Operator->>Fast: Resolve Song 1 (Select "Mute stream audio during this song")
    
    Operator->>Fast: Trigger Slide Generation
    Fast->>Pack: Generate strict verbatim lyrics & phonetic transliterations
    Pack-->>Fast: Formatted slide deck
    Fast-->>Operator: Slide Pack Ready

    Operator->>Console: Launch Live Telecast Console
    Console->>Console: Broadcast slide transitions via BroadcastChannel
    Console-->>Operator: 0ms real-time lower-thirds & Stage HUD updates

    Operator->>Fast: End Livestream
    Fast->>Closeout: Compile compliance dossier & dispute package
    Closeout-->>Operator: Download Closeout Pack (.md) & YouTube metadata
```

---

## 🛡️ The 3-Layer Copyright Defense Model

```mermaid
flowchart TD
    Song["Song in Sunday Setlist"] --> CheckStatus{"Is Song in Public Domain?"}
    
    CheckStatus -- "Yes (Pre-1929)" --> PD["PUBLIC DOMAIN (Yellow)"]
    PD --> PD_Note["Safe to stream • Original congregation performance • No master recording copyright"]
    
    CheckStatus -- "No (Post-1929 Copyright)" --> CheckLic{"Does church hold CCLI Streaming License?"}
    
    CheckLic -- "Yes" --> Covered["COVERED (Green)"]
    Covered --> Cov_Note["Authorized under CCLI Streaming License • Include mandatory attribution line"]
    
    CheckLic -- "No (CCLI Copyright License only)" --> Red["NEEDS STREAMING LICENSE (Red)"]
    Red --> Red_Choice{"Human-in-the-Loop Choice"}
    Red_Choice --> ChoiceA["1. Swap with Public Domain hymn"]
    Red_Choice --> ChoiceB["2. Mute stream audio (Safe Mode)"]
    Red_Choice --> ChoiceC["3. Proceed at own risk with Dispute Kit ready"]
```

---

## 🖥️ Live Telecast Display Synchronization Architecture

Selah uses the browser-native **`BroadcastChannel` API** for zero-latency multi-monitor synchronization from a single booth machine. All operator console, sanctuary projector, OBS overlay, and stage monitor tabs run in the same browser instance and sync via in-memory IPC with no network round-trip:

> **Scope Note:** `BroadcastChannel` is same-browser, same-origin only. This provides multi-monitor output from one control booth computer (the standard small-church setup). True multi-device sync across separate PCs (e.g., a dedicated projector machine) requires a network transport — the SSE stream endpoint (`/api/plan/{id}/stream`) already exists as the foundation for this roadmap feature.

```mermaid
graph LR
    subgraph "Control Booth Machine (Single Browser)"
        Console["ConsolePage (/console)<br/>Space / Arrow Keys / Foot Pedal"]
    end

    subgraph "Local IPC (0ms, Same-Origin)"
        BC["BroadcastChannel('selah_stream')"]
    end

    subgraph "Multi-Monitor Outputs (Same Machine)"
        OBS_Full["OutputPage (/output)<br/>Sanctuary Projector (16:9)"]
        OBS_Lower["OutputPage (/output?mode=lower-third)<br/>OBS Transparent Chroma/Alpha Overlay"]
        Stage_HUD["StagePage (/stage)<br/>Musician Confidence Monitor + Clock"]
    end

    Console -->|postMessage| BC
    BC -->|onmessage| OBS_Full
    BC -->|onmessage| OBS_Lower
    BC -->|onmessage| Stage_HUD
```

---

## 🔒 Post-Broadcast Compliance & Dispute Pipeline

```mermaid
graph TD
    EndEvent["Operator clicks 'End Stream'"] --> CloseoutGen["Closeout Agent Engine"]
    
    CloseoutGen --> Comp1["YouTube Metadata Engine"]
    Comp1 --> YT_Out["• SEO Title & Description<br/>• Mandatory CCLI Attributions<br/>• Timestamped Chapter Markers (0:00 start)"]

    CloseoutGen --> Comp2["CCLI Quarterly Audit Table"]
    Comp2 --> CCLI_Out["• Markdown / CSV Log<br/>• Date, Title, CCLI #, Usage Type"]

    CloseoutGen --> Comp3["Multi-Platform Dispute Kit"]
    Comp3 --> Dispute_Out["• YouTube Content ID Dispute Statement<br/>• Meta / Facebook Rights Manager Appeal Statement<br/>• CCLI Streaming License Verification Bundle"]
```

---

## ⚙️ Technical Specifications

| Tier | Component | Technology | Performance / Latency |
| :--- | :--- | :--- | :--- |
| **Frontend** | Live Console & Displays | React 19, Vite, Lucide Icons, BroadcastChannel API | `< 16ms` (60fps render) |
| **Backend** | REST & Agent Services | Python 3.12, FastAPI, Uvicorn | Sub-millisecond routing |
| **Agent Core** | Autonomous Agents | `google-adk` 2.7.0, `google-genai` 2.18.1 (`gemini-3.7-flash`) | Parallel multi-key rotation |
| **Grounding** | Deep Web Verification | `parallel-web` 1.3.0 (Parallel Search SDK) | `< 800ms` grounded search |
| **Packaging** | Native Slide Formats | `python-pptx` (16:9 Widescreen), JSON (ProPresenter 7) | Instant client-side download |
| **Deployment** | Serverless Container | Google Cloud Run, Cloud Build, Artifact Registry | $0.00 idle cost (`min-instances=0`) |
