# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import shutil
import os
import io
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def clean_cv_text(cv_text: str) -> str:
    """Elimina secciones internas del agente y el título REWRITTEN CV"""
    # Cortar secciones internas
    for marker in ["## CHANGES MADE", "## What was NOT added", "## WHAT WAS NOT ADDED"]:
        if marker in cv_text:
            cv_text = cv_text.split(marker)[0].strip()

    # Sacar el título "REWRITTEN CV: ..."
    lines = cv_text.split('\n')
    if lines and ('REWRITTEN CV' in lines[0].upper() or 'REWRITTEN' in lines[0].upper()):
        lines = lines[1:]
    
    return '\n'.join(lines).strip()

def md_to_pdf(md_text: str) -> bytes:
    """Convierte Markdown a PDF con reportlab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)

    h1 = ParagraphStyle('h1', fontSize=18, textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12, fontName='Helvetica-Bold')
    h2 = ParagraphStyle('h2', fontSize=14, textColor=colors.HexColor('#4B5563'),
        spaceAfter=8, spaceBefore=16, fontName='Helvetica-Bold')
    h3 = ParagraphStyle('h3', fontSize=12, textColor=colors.HexColor('#6B7280'),
        spaceAfter=6, spaceBefore=10, fontName='Helvetica-Bold')
    body = ParagraphStyle('body', fontSize=10, textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6, leading=16, fontName='Helvetica')
    bullet_style = ParagraphStyle('bullet', fontSize=10, textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=4, leading=16, leftIndent=20, fontName='Helvetica')

    def clean(text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text.strip()

    story = []
    for line in md_text.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('### '):
            story.append(Paragraph(clean(line[4:]), h3))
        elif line.startswith('## '):
            story.append(Paragraph(clean(line[3:]), h2))
        elif line.startswith('# '):
            story.append(Paragraph(clean(line[2:]), h1))
        elif line.startswith('- ') or line.startswith('* '):
            story.append(Paragraph(f'• {clean(line[2:])}', bullet_style))
        elif line.startswith('---'):
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(clean(line), body))

    doc.build(story)
    return buffer.getvalue()

@app.get("/")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/analyze")
async def analyze(
    cv_file: UploadFile = File(...),
    jd_text: str = Form(...),
    company_name: str = Form(default="the company"),
    role_title: str = Form(default="the role"),
    db = Depends(get_db),
):
    if not cv_file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF o DOCX")

    temp_path = f"/tmp/{cv_file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(cv_file.file, f)

    try:
        resultado = run_agent(cv_file_path=temp_path, jd_text=jd_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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

@app.get("/analyses/{analysis_id}/download-cv")
def download_cv(analysis_id: str, db = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")

    cv_text = clean_cv_text(analysis.rewritten_cv or "")
    
    # Obtener el nombre del candidato del CV parseado
    nombre = ""
    if analysis.parsed_cv and isinstance(analysis.parsed_cv, dict):
        nombre = analysis.parsed_cv.get("contact", {}).get("name", "")
    
    # Agregar el nombre como título al inicio
    if nombre:
        cv_text = f"# {nombre}\n\n{cv_text}"
    
    pdf_bytes = md_to_pdf(cv_text)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=CV_optimizado.pdf"}
    )

@app.get("/analyses/{analysis_id}/download-cover-letter")
def download_cover_letter(analysis_id: str, db = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")

    cv_text = clean_cv_text(analysis.rewritten_cv or "")
    
    # Obtener el nombre del candidato del CV parseado
    nombre = ""
    if analysis.parsed_cv and isinstance(analysis.parsed_cv, dict):
        nombre = analysis.parsed_cv.get("contact", {}).get("name", "")
    
    # Agregar el nombre como título al inicio
    if nombre:
        cv_text = f"# {nombre}\n\n{cv_text}"
    
    pdf_bytes = md_to_pdf(cv_text)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cover_letter.pdf"}
    )