from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import csv
from db import init_db, save_lead, is_message_sent
from send_whatsapp import send_whatsapp_message

app = FastAPI()

class LeadRequest(BaseModel):
    job_title: str
    location: str

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/fetch-leads/")
def fetch_leads(data: LeadRequest):
    results = []
    try:
        with open("leads.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (row["job_title"].lower() == data.job_title.lower() and
                    row["location"].lower() == data.location.lower()
                    #   and not is_message_sent(row["phone_number"])
                    ):

                    message = (
                        f"Hi {row['job_title']} from {row['location']}, "
                        "we have an exciting opportunity for you! "
                        f"Check this out: {row['linkedin_url']}"
                    )
                    success = send_whatsapp_message(row["phone_number"], message)
                    if success:
                        save_lead(row)
                        results.append(row)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="CSV file not found")

    if not results:
        raise HTTPException(status_code=404, detail="No new leads found")

    return {"sent_leads": results}
