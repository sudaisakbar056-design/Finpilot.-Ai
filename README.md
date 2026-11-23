# FinPilot AI — Finance + Data + Automation Agent

A beginner-friendly starter application with:
- Responsive web app and installable Android PWA
- Finance dashboard and transaction ledger
- CSV upload and automatic dataset profiling
- Finance metrics (revenue, expenses, net profit, margin)
- AI chat endpoint (optional OpenAI API key)
- Simple automation rules that can be run manually

## Requirements
- Python 3.10+
- A modern browser
- Optional: OpenAI API key for AI chat

## 1. Start the backend
Open a terminal in the `backend` folder:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
# Copy .env.example to .env and optionally add your API key
uvicorn main:app --reload
```

Backend runs at http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

## 2. Start the frontend
Open `frontend/index.html` in a browser, or serve it locally:

```bash
cd frontend
python -m http.server 5500
```

Then open http://127.0.0.1:5500

The frontend defaults to `http://127.0.0.1:8000`. On a phone, localhost refers to the phone itself, not your computer. For phone testing, change the API URL in Settings to your computer's LAN IP, e.g. `http://192.168.1.10:8000`, and ensure both devices share Wi-Fi. Allow the backend through your firewall.

## 3. Install on Android
For local testing, open the frontend URL in Chrome on Android. Use Chrome menu > **Install app** or **Add to Home screen**. For installation from anywhere, deploy the frontend and backend to HTTPS hosting first. A PWA is installable; this project does not include a native APK.

## 4. Enable AI chat (optional)
In `backend`, copy `.env.example` to `.env` and set:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Restart the backend. Never put the API key in frontend JavaScript or share it publicly. AI chat returns a clear message when no key is configured.

## 5. Important limitations
- This is a functional MVP, not audited financial software.
- Data is stored locally in `backend/finpilot.db` by default.
- CSV upload currently analyses the uploaded file in memory; it does not permanently store it.
- Automation rules run when you press **Run automations**; no background scheduler is configured.
- Do not upload confidential customer or bank data to an unsecured deployment.
- For public deployment, add authentication, HTTPS, database backups, rate limits and access controls before using real financial records.
