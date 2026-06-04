# test_agent.py
from dotenv import load_dotenv
load_dotenv()

from app.services.cv_agent import run_agent

cv_file_path = "/Users/barbaralococo/Desktop/Trabajos/matchCV/cvmatch-api/CV _Bárbara _Lococo.pdf"

resultado = run_agent(
    cv_file_path=cv_file_path,
    jd_text="""
    We are looking for a Senior Data Scientist with experience in 
    Python, SQL, machine learning, and A/B testing...
    """
)

print("SCORE:", resultado.get("score_compatibility", {}).get("overall_score"))
print("\nCV REESCRITO:\n", resultado.get("rewrite_cv", ""))

# Guardar CV reescrito
with open("cv_reescrito.md", "w") as f:
    f.write(resultado.get("rewrite_cv", ""))

print("\n✓ CV guardado en cv_reescrito.md")