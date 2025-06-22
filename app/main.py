from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.agents.supervisor_agent import GuidanceAuditorAgent
from google.cloud import aiplatform as vertexai
import json
from typing import Optional

# --- App Configuration ---
app = FastAPI(
    title="Guidance Survey AI",
    description="An agent to audit reports against guidance documents using Vertex AI Search.",
    version="2.1.0", # Final Version
)

# --- Global Variables ---
templates = Jinja2Templates(directory="app/templates")
auditor_agent = None

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    global auditor_agent
    try:
        from app.tools.search_tool import PROJECT_ID, LOCATION
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        auditor_agent = GuidanceAuditorAgent()
        print("--- Auditor Agent Initialized Successfully ---")
    except Exception as e:
        print(f"FATAL: Could not initialize GuidanceAuditorAgent during startup: {e}")

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse, summary="Main UI")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/audit", summary="Run Guidance Audit")
async def audit_report(
    report_text: Optional[str] = Form(None), 
    report_file: Optional[UploadFile] = File(None)
):
    if auditor_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized.")
    
    if not report_text and not report_file:
        raise HTTPException(status_code=400, detail="No report text or file provided.")

    file_content = None
    file_name = None
    if report_file:
        file_content = await report_file.read()
        file_name = report_file.filename

    try:
        result = auditor_agent.run_audit(
            file_content=file_content, 
            file_name=file_name, 
            report_text=report_text
        )
        return result
    except Exception as e:
        print(f"An error occurred during the audit process: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
