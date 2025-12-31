import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.scanner_bridge import engine as scanner_engine 
from app.database import engine  as db_engine, get_db
from app import models
from groq import Groq
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)

# --- DATABASE INIT ---
models.Base.metadata.create_all(bind=db_engine)

app = FastAPI(title="Switchboard AI Gateway", version="3.0")

# Mount the "static" folder to serve HTML
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")

# --- DATA MODELS ---
# 1. Define the Input Format (Schema)
class PromptRequest(BaseModel):
    user_id: str
    prompt: str

# 2. Define the Output Format
class ScanResponse(BaseModel):
    status: str
    risk_detected: bool
    ai_response: str = None
    processed_by: str

def get_intelligent_route(prompt: str):

    p_lower = prompt.lower()
    reasoning_triggers = [
        "write a", "explain", "code", "python", "analyze", 
        "summarize", "step by step", "how to"
    ]
    
    # 1. Routing by Task Complexity (Keywords)
    # 2. Routing by Length (Longer prompts usually need better models)
    is_complex = any(trigger in p_lower for trigger in reasoning_triggers)
    is_long = len(prompt.split()) > 30
    
    if is_complex or is_long:
        return "llama-3.3-70b-versatile", "PREMIUM_REASONING"
    return "llama-3.1-8b-instant", "STANDARD_FAST"

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return{"status": "online", "system": "Switchboard AI"}

@app.post("/v1/chat", response_model=ScanResponse)
def chat_with_ai(request: PromptRequest, db: Session = Depends(get_db)):
    # 1. SMART SCAN & REDACT
    clean_text, was_redacted, latency = scanner_engine.scan_and_redact(request.prompt)

    # 2. ROUTE THE CLEAN TEXT
    model_name, route_type = get_intelligent_route(clean_text)
    
    try:
        chat_completion = client.chat.completions.create(
            messages = [
            {
                    "role": "system",
                    "content": "Sensitive information was automatically redacted for security."
            },
            {
                    "role": "user",
                    "content": clean_text
            }],
            model=model_name,
        )
        ai_reply = chat_completion.choices[0].message.content
        status = "REDACTED" if was_redacted else "PROCESSED"
    except Exception as e:
        status = "ERROR"
        ai_reply = f"AI Service Error: {str(e)}"

    # 3. LOG WITH LATENCY & PROMPT LENGTH
    new_log = models.RequestLog(
        user_id=request.user_id,
        prompt_length=len(request.prompt),
        status=status,
        risk_detected=was_redacted,
        model_used=f"{model_name} | {route_type} | Scan: {latency}ms"
    )
    db.add(new_log)
    db.commit()

    return {
        "status": status,
        "risk_detected": was_redacted,
        "ai_response": ai_reply,
        "processed_by": f"{model_name} (Latency: {latency}ms)"
    }
@app.get("/v1/logs")
def get_logs(limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch the last 10 logs for the dashboard.
    """
    return db.query(models.RequestLog).order_by(models.RequestLog.id.desc()).limit(limit).all()
     
