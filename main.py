from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import sqlite3, os, io, json
import pandas as pd

load_dotenv()
DB = Path(__file__).with_name("finpilot.db")
app = FastAPI(title="FinPilot AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"]
)

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, description TEXT NOT NULL,
            category TEXT NOT NULL, kind TEXT NOT NULL,
            amount REAL NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, threshold REAL NOT NULL,
            message TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1
        )""")
init_db()

class TransactionIn(BaseModel):
    date: str
    description: str
    category: str = "Other"
    kind: str
    amount: float

class ChatIn(BaseModel):
    message: str
    context: Optional[dict] = None

class RuleIn(BaseModel):
    name: str
    threshold: float
    message: str

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "FinPilot AI"}

@app.get("/api/transactions")
def transactions():
    with connect() as con:
        rows = con.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/transactions")
def add_transaction(item: TransactionIn):
    if item.kind not in ("income", "expense"):
        raise HTTPException(400, "kind must be income or expense")
    if item.amount <= 0:
        raise HTTPException(400, "amount must be greater than zero")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO transactions(date,description,category,kind,amount) VALUES(?,?,?,?,?)",
            (item.date, item.description, item.category, item.kind, item.amount)
        )
        new_id = cur.lastrowid
    return {"id": new_id, **item.model_dump()}

@app.delete("/api/transactions/{item_id}")
def delete_transaction(item_id: int):
    with connect() as con:
        cur = con.execute("DELETE FROM transactions WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Transaction not found")
    return {"deleted": item_id}

def metrics(rows):
    income = sum(float(r["amount"]) for r in rows if r["kind"] == "income")
    expenses = sum(float(r["amount"]) for r in rows if r["kind"] == "expense")
    profit = income - expenses
    return {
        "income": round(income, 2), "expenses": round(expenses, 2),
        "profit": round(profit, 2),
        "margin": round((profit / income * 100), 2) if income else 0,
        "transaction_count": len(rows)
    }

@app.get("/api/summary")
def summary():
    with connect() as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM transactions").fetchall()]
    result = metrics(rows)
    categories = {}
    for r in rows:
        if r["kind"] == "expense":
            categories[r["category"]] = categories.get(r["category"], 0) + float(r["amount"])
    result["expense_by_category"] = [
        {"category": k, "amount": round(v, 2)}
        for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)
    ]
    return result

@app.post("/api/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        if df.empty:
            raise ValueError("The CSV has no rows")
        numeric = df.select_dtypes(include="number")
        return {
            "filename": file.filename,
            "rows": int(len(df)),
            "columns": [{"name": str(c), "dtype": str(df[c].dtype)} for c in df.columns],
            "missing_values": {str(k): int(v) for k, v in df.isna().sum().items()},
            "numeric_summary": json.loads(numeric.describe().round(2).to_json()) if len(numeric.columns) else {},
            "preview": json.loads(df.head(8).fillna("").to_json(orient="records"))
        }
    except Exception as e:
        raise HTTPException(400, f"Could not read CSV: {e}")

@app.post("/api/chat")
def chat(payload: ChatIn):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return {"reply": "AI chat is not connected yet. Add OPENAI_API_KEY to backend/.env and restart the server. Your built-in dashboard, finance calculations and CSV analysis work without it."}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        system = (
            "You are FinPilot, a careful finance, data-analysis and business-automation assistant. "
            "Explain calculations step by step, state assumptions, use the user's currency when supplied, "
            "and never claim to have executed an action unless a tool actually did it. "
            "Do not present your output as audited accounting, tax or investment advice."
        )
        context = json.dumps(payload.context or {}, ensure_ascii=False)[:12000]
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system + "\nCurrent app context: " + context},
                {"role": "user", "content": payload.message}
            ],
            temperature=0.2
        )
        return {"reply": response.choices[0].message.content or ""}
    except Exception as e:
        raise HTTPException(502, f"AI provider error: {e}")

@app.get("/api/rules")
def get_rules():
    with connect() as con:
        rows = con.execute("SELECT * FROM rules ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/rules")
def add_rule(rule: RuleIn):
    with connect() as con:
        cur = con.execute("INSERT INTO rules(name,threshold,message) VALUES(?,?,?)",
                          (rule.name, rule.threshold, rule.message))
    return {"id": cur.lastrowid, **rule.model_dump(), "enabled": 1}

@app.post("/api/run-automations")
def run_automations():
    with connect() as con:
        rules = con.execute("SELECT * FROM rules WHERE enabled=1").fetchall()
        rows = [dict(r) for r in con.execute("SELECT * FROM transactions").fetchall()]
    total_expenses = sum(r["amount"] for r in rows if r["kind"] == "expense")
    fired = []
    for rule in rules:
        if total_expenses >= rule["threshold"]:
            fired.append({"rule": rule["name"], "message": rule["message"],
                          "current_expenses": round(total_expenses, 2)})
    return {"checked": len(rules), "alerts": fired,
            "message": "Automation check completed. Rules are evaluated against all recorded expenses."}


# Serve the responsive web app from the same cloud service as the API.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
