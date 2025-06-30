from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import csv
import asyncio
from pathlib import Path
from db import init_db, save_lead, is_message_sent
from send_whatsapp import send_whatsapp_message

# ── FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(
    title="Lead WhatsApp Messenger",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ─────────────────────────────────────────────────────────────
class LeadRequest(BaseModel):
    job_title: str
    location: str

# ── Helpers ────────────────────────────────────────────────────────────
LEADS_FILE = Path(__file__).parent / "leads.csv"
executor = ThreadPoolExecutor(max_workers=1)  # Only 1 instance of WhatsApp

# ── Background WhatsApp Queue ──────────────────────────────────────────
send_queue: asyncio.Queue = asyncio.Queue()

async def whatsapp_worker():
    while True:
        phone, text, row = await send_queue.get()
        try:
            success = await asyncio.get_event_loop().run_in_executor(
                executor, send_whatsapp_message, phone, text
            )
            if success:
                save_lead(row)
                print(f"✅ Sent WhatsApp to {phone}")
            else:
                print(f"❌ Failed to send to {phone}")
        except Exception as e:
            print(f"⚠️ WhatsApp send error for {phone}: {e}")
        finally:
            send_queue.task_done()

# ── Events ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    init_db()
    asyncio.create_task(whatsapp_worker())
    print("✅ FastAPI started & WhatsApp worker running")

# ── Health route ───────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Lead WhatsApp API running"}

# ── Load leads helper ──────────────────────────────────────────────────
def load_leads() -> list[dict]:
    if not LEADS_FILE.exists():
        raise FileNotFoundError(f"{LEADS_FILE} not found")
    with LEADS_FILE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ── Main endpoint ─────────────────────────────────────────────────────
@app.post("/fetch-leads/")
async def fetch_leads(data: LeadRequest):
    try:
        all_leads = load_leads()
    except FileNotFoundError as err:
        raise HTTPException(status_code=500, detail=str(err))

    matches = [
        row for row in all_leads
        if row["job_title"].lower() == data.job_title.lower()
        and row["location"].lower() == data.location.lower()
        # and not is_message_sent(row["phone_number"])  
    ]

    if not matches:
        raise HTTPException(status_code=404, detail="No new leads found")

    # ⛔ Limit to only 10 leads per request
    limited_matches = matches[:10]

    for row in limited_matches:
        msg = (
            f"Hi {row['job_title']} from {row['location']}, "
            "we have an exciting opportunity for you! "
            f"Check this out: {row['linkedin_url']}"
        )
        await send_queue.put((row["phone_number"], msg, row))

    return {"sent_leads": limited_matches}
