# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import os

load_dotenv()

from app.services.cv_agent import run_agent

app = FastAPI(title="CVMatch API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/analyze")
async def analyze(
    cv_file: UploadFile = File(...),
    jd_text: str = Form(...),
    company_name: str = Form(default="the company"),
    role_title: str = Form(default="the role"),
):
    # Validar formato del archivo
    if not cv_file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF o DOCX")

    # Guardar CV temporalmente
    temp_path = f"/tmp/{cv_file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(cv_file.file, f)

    try:
        resultado = run_agent(
            cv_file_path=temp_path,
            jd_text=jd_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Siempre limpiar el archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {
        "score":        resultado.get("score_compatibility", {}),
        "rewritten_cv": resultado.get("rewrite_cv", ""),
        "cover_letter": resultado.get("generate_cover_letter", ""),
        "parsed_cv":    resultado.get("parse_cv", {}),
        "jd_analysis":  resultado.get("analyze_jd", {}),
    }