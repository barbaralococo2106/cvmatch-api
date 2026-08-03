# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from app.database import engine, SessionLocal
from app import models
from app.services.cv_agent import run_agent

models.Base.metadata.create_all(bind=engine)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/analyze")
async def analyze(
    cv_file: UploadFile = File(...),
    jd_text: str = Form(...),
    company_name: str = Form(default="the company"),
    role_title: str = Form(default="the role"),
    db = Depends(get_db),
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
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Guardar en la base de datos
    analysis = models.Analysis(
        jd_text=jd_text,
        company_name=company_name,
        role_title=role_title,
        score=resultado.get("score_compatibility", {}),
        rewritten_cv=resultado.get("rewrite_cv", ""),
        cover_letter=resultado.get("generate_cover_letter", ""),
        parsed_cv=resultado.get("parse_cv", {}),
        jd_analysis=resultado.get("analyze_jd", {}),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "id":           analysis.id,
        "created_at":   analysis.created_at,
        "score":        analysis.score,
        "rewritten_cv": analysis.rewritten_cv,
        "cover_letter": analysis.cover_letter,
        "parsed_cv":    analysis.parsed_cv,
        "jd_analysis":  analysis.jd_analysis,
    }
    
@app.get("/analyses")
def get_analyses(db = Depends(get_db)):
    analyses = db.query(models.Analysis).order_by(models.Analysis.created_at.desc()).all()
    
    return [
        {
            "id":           a.id,
            "created_at":   a.created_at,
            "company_name": a.company_name,
            "role_title":   a.role_title,
            "score":        a.score.get("overall_score") if a.score else None,
        }
        for a in analyses
    ]

@app.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, db = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    return {
        "id":           analysis.id,
        "created_at":   analysis.created_at,
        "company_name": analysis.company_name,
        "role_title":   analysis.role_title,
        "score":        analysis.score,
        "rewritten_cv": analysis.rewritten_cv,
        "cover_letter": analysis.cover_letter,
        "parsed_cv":    analysis.parsed_cv,
        "jd_analysis":  analysis.jd_analysis,
    }