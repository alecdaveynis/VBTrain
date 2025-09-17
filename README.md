# 🏐 VBTrain — AI-Powered Volleyball Coaching Assistant

VBTrain is a full-stack **Flask web app** that uses **computer vision + LLMs** to turn raw game footage and team stats into actionable coaching insights.  
Built as a lightweight tool for club and collegiate teams, it analyzes clips, suggests optimal lineups, and generates tailored practice plans.

---

## 🚀 Features

### 🎥 Video Analysis
- Upload `.mp4/.mov/.avi` clips (under ~60s works best)
- Extracts timeline events (every ~2s) with OpenCV
- GPT feedback: **observations, adjustments, and drills** per event
- Inline video playback with annotated timeline

### 👥 Player Management
- Enter roster with:
  - Name, jersey #, role (OH/MB/S/OPP/L/DS)
  - Core stats (Attack %, Pass rating, Block eff, Serve in %, Dig %)
  - Struggles (comma-separated tags: e.g. `serve receive, block timing`)
- Data stored in JSON for simplicity (no DB required)

### 🏐 Optimal Lineup
- Stats-driven heuristic lineup (role-specific weights, fallback logic)
- Produces 2×OH, 2×MB, 1×S, 1×OPP, 1×L
- Bench ordered by overall composite score
- On-demand GPT critique: balance, subs, rotation notes

### 📅 Practice Planner
- Save schedule inputs (days, start time, duration, location)
- Generate **1-week plan** focused on the team’s most frequent struggles
- Drills/time blocks returned as compact, scannable coach notes
- Stored locally; regenerate anytime

### 🎨 UI/UX
- Modern dark theme with gradient accents (custom CSS)
- Responsive grid layout, card-based panels
- Clear workflow: **Players → Lineup → Practice**

---

## ⚙️ Tech Stack

- **Backend**: Flask (Python 3.11)
- **Frontend**: Jinja2 templates + custom CSS
- **Video**: OpenCV
- **AI/ML**: 
  - OpenAI GPT-4o-mini (event feedback, lineup critique, practice planner)
  - Heuristic lineup algorithm (role-weighted stats)
- **Storage**: JSON (lightweight, no DB required)
- **Infra**: `.env` for secrets, `.gitignore` for uploads/data

---
