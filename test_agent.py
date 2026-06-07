# test_agent.py
from dotenv import load_dotenv
load_dotenv()

from app.services.cv_agent import run_agent

cv_file_path = "/Users/barbaralococo/Desktop/Trabajos/matchCV/cvmatch-api/CV _Bárbara _Lococo.pdf"

resultado = run_agent(
    cv_file_path=cv_file_path,
    jd_text="""At Félix, we're building the financial ecosystem for Latin immigrants in the U.S., starting with a revolution in remittances. Our core product is an AI-powered chatbot built on WhatsApp, allowing our users to send money home as easily as sending a text message. We leverage cutting-edge technology like AI, blockchain, and stablecoins to make cross-border payments faster, more affordable, and more accessible than ever before.

We are a hyper-growth Series B company, backed by over $100 million in funding from top-tier global investors, including QED, Castle Island, Switch Ventures, HTwenty, Monashees, and General Catalyst Customer Value Fund. This isn't just about the numbers; it's a testament to the trust our investors have in our vision and our team. Additionally, Félix was selected as an “Endeavour Entrepreneur” and was a recipient of the CrossTech Fintech Startups Award. We are a group of extremely talented and dedicated high-performers, united by our shared obsession with a single goal: empowering our customers. We are all owners of Félix, driven by a bias for action and a true experimentation spirit to get shit done with urgency and focus.

Joining Félix means you will be part of a team building a legacy, a company that will outlive us all. This is a rare opportunity to apply your skills to a deeply meaningful mission—serving a community that has been underserved for too long. We are a team that is fiercely loyal to each other, where radical transparency and constructive feedback are how we grow and push for excellence. We are bold, we care less about what others are doing, and more about creating sustainable value and a product that truly makes our users' lives better. We are building the future, today.

About The Role

As the Lead Data Scientist, you will be the brain behind our user conversion and retention engines. We are looking for a high-impact, business-oriented leader who understands that models are only as good as the results they drive. You won't just be looking at data; you will be architecting the intelligence that powers our core business KPIs. This role requires someone who is a go-getter, genuinely excited about leveraging data to dictate the direction of the product. You will bridge the gap between technical complexity and business growth, translating ambiguous user signals into optimized, scalable machine-learning solutions.

Responsibilities

Lead the improvement and scaling of our New User Conversion (NUC) and Existing User Conversion (EUC) ML optimization models.
Partner with Chat, Product, Engineering, and Growth teams to develop and implement strategies based on model findings.
Partner with Product Managers to define the experimentation roadmap, ensuring that every ML initiative is tied to a clear hypothesis and user benefit.
Pioneer the implementation of Natural Language Processing (NLP) signals into our core models to better understand and predict user intent through chat interactions.
Develop and enhance new features to measure specific influences on business KPIs, focusing on practical modeling where features dictate high-quality analysis.
Proactively identify new ML use cases across the company to drive efficiency and user value.
Use Python, SQL, and DBT to maintain high standards of data hygiene and model performance.

Requirements

Significant experience in ML Modeling, specifically using Regression, Clustering, XGBoost, and CatBoost.
Strong technical background in Natural Language Processing (NLP), Word Embeddings (HuggingFace) applied to real-world business problems.
Mastery of SQL and BigQuery for handling large-scale datasets.
Hands-on experience with Data Visualization tools such as Tableau, PowerBI, or Looker to drive business insights.
Familiarity with dbt (Data Build Tool) or similar data transformation frameworks.
Full professional proficiency in English
Exceptional communication and stakeholder management skills, with the ability to present complex technical findings to non-technical audiences.
A proactive, "go-getter" attitude with a deep interest in how data can be leveraged to drive product decisions and KPIs.
These are the applicable requisites, although equivalent competencies in any of the above will also be considered.

What We Offer

Competitive salary
Initial stock options grant
Annual performance bonus
Health, dental, and vision plans 
Remote work environment, although we have offices in Miami and México City and would love to work in hybrid model if you are up to it.
Continuous learning opportunities 
Unlimited PTO
Paid parental leave
Empowering opportunities for growth in a dynamic entrepreneurial environment

Equal Opportunity Employer

At Félix, we are committed to providing equal employment opportunities to all qualified employees and applicants without regard to race, religion, nationality, sex, sexual orientation, gender identity, age, or disability. This policy applies to all terms and conditions of employment, including recruitment, hiring, placement, promotion, training, compensation, benefits, and termination.

"""
)

print("SCORE:", resultado.get("score_compatibility", {}).get("overall_score"))
print("\nCV REESCRITO:\n", resultado.get("rewrite_cv", ""))

# Guardar CV reescrito
with open("cv_reescrito.md", "w") as f:
    f.write(resultado.get("rewrite_cv", ""))

print("\n✓ CV guardado en cv_reescrito.md")
print("\nTODOS LOS RESULTADOS:", list(resultado.keys()))
print("\nSUMMARY:", resultado.get("summary", ""))

print("SCORE:", resultado.get("score_compatibility", {}).get("overall_score"))
print("\nCV REESCRITO:\n", resultado.get("rewrite_cv", ""))
print("\nCOVER LETTER:\n", resultado.get("generate_cover_letter", ""))

# Guardar ambos outputs
with open("cv_reescrito.md", "w") as f:
    f.write(resultado.get("rewrite_cv", ""))

with open("cover_letter.md", "w") as f:
    f.write(resultado.get("generate_cover_letter", ""))

print("\n✓ CV guardado en cv_reescrito.md")
print("✓ Cover letter guardada en cover_letter.md")