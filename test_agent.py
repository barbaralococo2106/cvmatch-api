# test_agent.py
from dotenv import load_dotenv
load_dotenv()

from app.services.cv_agent import run_agent

cv_file_path = "/Users/barbaralococo/Desktop/Trabajos/matchCV/cvmatch-api/CV _Bárbara _Lococo.pdf"

resultado = run_agent(
    cv_file_path=cv_file_path,
    jd_text="""https://www.linkedin.com/jobs/search/?currentJobId=4384288184&f_C=74044131&geoId=92000000&origin=COMPANY_PAGE_JOBS_CLUSTER_EXPANSION&originToLandingJobPostings=4416306836%2C4384288184%2C4395924520%2C4390243175%2C4418753966%2C4401139934%2C4413042438%2C4403692783%2C4414175305&trk=d_flagship3_company_posts"""
)

print("SCORE:", resultado.get("score_compatibility", {}).get("overall_score"))
print("\nCV REESCRITO:\n", resultado.get("rewrite_cv", ""))

# Guardar CV reescrito
with open("cv_reescrito.md", "w") as f:
    f.write(resultado.get("rewrite_cv", ""))

print("\n✓ CV guardado en cv_reescrito.md")