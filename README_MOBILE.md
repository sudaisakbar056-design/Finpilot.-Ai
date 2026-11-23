# FinPilot AI — Phone-only cloud setup

This bundle serves the frontend and API from one web service.

## Import and run on Replit
1. On Android Chrome, open https://replit.com/import
2. Choose ZIP and upload this ZIP.
3. Open the imported project.
4. Ask Replit Agent: "Run this existing FastAPI project. Keep the existing code and SQLite database. Install requirements.txt, run `uvicorn backend.main:app --host 0.0.0.0 --port 3000`, and make the web preview available. Do not replace the project with a demo."
5. Open the web preview and test `/api/health`.
6. Use Replit's Publish/Deploy option if available on your account to create a public HTTPS URL.
7. Open the published URL in Chrome > menu > Install app / Add to Home screen.

## Optional AI
Add `OPENAI_API_KEY` as a Replit Secret (not in source code) and optionally `OPENAI_MODEL` = `gpt-4o-mini`.
Restart the app after adding secrets.

## Important
This is an MVP for testing. The SQLite database is local to the service and may not be durable across all hosting/redeploy scenarios. Do not use it for sensitive or business-critical records until persistent database storage, authentication, backups and HTTPS deployment are configured. Free hosting and publishing availability/limits can change by account and plan.
