# app/services/cv_agent.py
import anthropic
import json
import os
from pathlib import Path

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── TOOLS (las funciones reales) ──────────────────────────────

def extract_cv_text(file_path: str) -> str:
    """Extrae texto de PDF o DOCX"""
    if file_path.endswith(".pdf"):
        import PyPDF2
        reader = PyPDF2.PdfReader(file_path)
        return "\n".join(page.extract_text() for page in reader.pages)
    elif file_path.endswith(".docx"):
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Formato no soportado")

def clean_json(raw: str) -> dict:
    """Limpia la respuesta de Claude y parsea el JSON"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)

def parse_cv(cv_text: str) -> dict:
    """Parsea el CV a estructura JSON via Claude"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        temperature=0.1,
        system="""Parse this CV and return ONLY valid JSON with this exact structure:
{
  "contact": {"name": "", "email": "", "location": "", "linkedin": ""},
  "summary": "",
  "skills": {"technical": [], "tools": [], "soft": []},
  "experience": [{"company": "", "title": "", "start": "", "end": "", "bullets": []}],
  "education": [{"institution": "", "degree": "", "field": "", "year": ""}]
}
No markdown. No backticks. No explanation. Just the JSON object.""",
        messages=[{"role": "user", "content": cv_text}]
    )
    return clean_json(response.content[0].text)

def analyze_jd(jd_text: str) -> dict:
    """Extrae requisitos clave del JD"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        temperature=0.1,
        system="""Extract job requirements and return ONLY valid JSON with this exact structure:
{
  "role_level": "junior|mid|senior|lead",
  "required_skills": [{"skill": "", "importance": "must_have|preferred"}],
  "experience_years": 0,
  "ats_keywords": []
}
No markdown. No backticks. No explanation. Just the JSON object.""",
        messages=[{"role": "user", "content": jd_text}]
    )
    
    raw = response.content[0].text.strip()
    
    # Limpiar markdown si Claude lo agregó igual
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    
    return json.loads(raw)

def score_compatibility(cv: dict, jd: dict) -> dict:
    """Calcula el score de compatibilidad"""
    prompt = f"CV:\n{json.dumps(cv)}\n\nJD Requirements:\n{json.dumps(jd)}"
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        temperature=0.1,
        system="""Score CV vs JD and return ONLY valid JSON with this exact structure:
{
  "overall_score": 0,
  "subscores": {
    "technical_skills": {"score": 0, "rationale": ""},
    "experience_level": {"score": 0, "rationale": ""},
    "keyword_density": {"score": 0, "rationale": ""}
  },
  "missing_critical": [{"keyword": "", "urgency": "blocking|important|minor"}],
  "strengths": [],
  "gaps": []
}
No markdown. No backticks. No explanation. Just the JSON object.""",
        messages=[{"role": "user", "content": prompt}]
    )
    return clean_json(response.content[0].text)

def rewrite_cv(cv: dict, jd: dict, score: dict) -> str:
    """Reescribe el CV optimizado para el JD — con guardrails estrictos"""
    
    prompt = f"""
CANDIDATE'S ORIGINAL CV (source of truth — nothing can be added that isn't here):
{json.dumps(cv, indent=2)}

JOB DESCRIPTION REQUIREMENTS:
{json.dumps(jd, indent=2)}

GAPS IDENTIFIED:
{json.dumps(score.get('missing_critical', []), indent=2)}
"""
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        temperature=0.1,
        system="""You are an expert CV writer. Your job is to REWRITE (not invent) the candidate's CV.

## ABSOLUTE RULES — NEVER VIOLATE:
1. NEVER add a skill, tool, technology, or certification the candidate didn't mention in their original CV
2. NEVER change company names, job titles, or employment dates
3. NEVER invent metrics, numbers, or outcomes (if the original says "improved performance", keep it vague — don't say "improved performance by 40%")
4. NEVER add responsibilities that aren't implied by the original bullets
5. If a skill is required by the JD but NOT in the CV → DO NOT add it. Instead, find the closest real skill the candidate has and highlight that instead.

## WHAT YOU CAN DO:
- Rephrase bullets using stronger action verbs
- Reorder sections to prioritize what's most relevant to the JD
- Incorporate JD keywords ONLY when they describe something the candidate already does
- Expand on existing bullets with more professional language
- Rewrite the summary to align with the target role — using only facts from the CV

## VERIFICATION STEP:
Before returning the rewritten CV, mentally check every bullet point:
"Is this based on something in the original CV?" → If NO, remove it.

## OUTPUT FORMAT:
Return the rewritten CV in clean Markdown.
After the CV, add a section called "## Changes Made" listing exactly what you changed and why.
Then add "## What was NOT added" listing the JD requirements that weren't in the CV and therefore were intentionally excluded.""",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# ── TOOL SCHEMAS (lo que Claude "ve") ────────────────────────

TOOLS = [
    {
        "name": "extract_cv_text",
        "description": "Extracts raw text from a CV file (PDF or DOCX)",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the CV file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "parse_cv",
        "description": "Parses raw CV text into structured JSON with contact, skills, experience, education",
        "input_schema": {
            "type": "object",
            "properties": {
                "cv_text": {"type": "string", "description": "Raw text of the CV"}
            },
            "required": ["cv_text"]
        }
    },
    {
        "name": "analyze_jd",
        "description": "Extracts key requirements from a job description",
        "input_schema": {
            "type": "object",
            "properties": {
                "jd_text": {"type": "string", "description": "Full job description text"}
            },
            "required": ["jd_text"]
        }
    },
    {
        "name": "score_compatibility",
        "description": "Scores how well the CV matches the job description",
        "input_schema": {
            "type": "object",
            "properties": {
                "cv":  {"type": "object", "description": "Parsed CV JSON"},
                "jd":  {"type": "object", "description": "Analyzed JD JSON"}
            },
            "required": ["cv", "jd"]
        }
    },
    {
        "name": "rewrite_cv",
        "description": "Rewrites the CV to better match the job description",
        "input_schema": {
            "type": "object",
            "properties": {
                "cv":    {"type": "object"},
                "jd":    {"type": "object"},
                "score": {"type": "object"}
            },
            "required": ["cv", "jd", "score"]
        }
    }
]

# ── DISPATCHER ────────────────────────────────────────────────

def dispatch_tool(name: str, inputs: dict):
    """Ejecuta la tool que Claude pidió"""
    if name == "extract_cv_text":  return extract_cv_text(**inputs)
    if name == "parse_cv":         return parse_cv(**inputs)
    if name == "analyze_jd":       return analyze_jd(**inputs)
    if name == "score_compatibility": return score_compatibility(**inputs)
    if name == "rewrite_cv":       return rewrite_cv(**inputs)
    raise ValueError(f"Tool desconocida: {name}")

# ── AGENTE PRINCIPAL ──────────────────────────────────────────

def run_agent(cv_file_path: str, jd_text: str) -> dict:
    """
    Corre el agente completo.
    Claude decide qué tools usar y en qué orden.
    """
    messages = [
        {
            "role": "user",
            "content": f"""Analyze this job application:
CV file: {cv_file_path}
Job Description: {jd_text}

Please:
1. Extract and parse the CV
2. Analyze the job description  
3. Score the compatibility
4. Rewrite the CV to better match the role

Use the available tools in the right order."""
        }
    ]

    results = {}

    # Loop agentico — corre hasta que Claude diga "ya terminé"
    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            tools=TOOLS,
            messages=messages
        )

        # Claude terminó
        if response.stop_reason == "end_turn":
            results["summary"] = response.content[0].text
            break

        # Claude quiere usar una tool
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"→ Usando tool: {block.name}")  # útil para debuggear
                    output = dispatch_tool(block.name, block.input)

                    # Guardamos resultados intermedios
                    results[block.name] = output

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output) if isinstance(output, dict) else output
                    })

            # Le devolvemos los resultados a Claude para que siga
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    return results

