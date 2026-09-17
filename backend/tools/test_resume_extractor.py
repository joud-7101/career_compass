from backend.tools.resume_extractor import extract_profile_from_resume


resume_text = """
Sara Ahmed
Jeddah, Saudi Arabia
sara@example.com
+966500000000

Professional Summary
Information Systems graduate interested in data analysis
and artificial intelligence.

Education
Bachelor of Science in Information Systems
King Abdulaziz University
2022 - 2026

Work Experience
Data Analyst Intern
ABC Company
June 2025 - August 2025

Analyzed business data using Excel and Power BI.
Created dashboards and reports for the management team.

Skills
Python
SQL
Excel
Power BI
Git

Certifications
Microsoft Power BI Data Analyst

Projects
Sales Dashboard Project
Built an interactive Power BI dashboard to analyze
sales performance.

Languages
Arabic
English

Professional Links
LinkedIn: https://linkedin.com/in/sara
GitHub: https://github.com/sara
"""


profile = extract_profile_from_resume(
    resume_text
)

print(
    profile.model_dump_json(
        indent=2
    )
)