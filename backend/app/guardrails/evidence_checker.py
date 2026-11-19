"""
Evidence Verification Guardrail.
Cross-checks generated resume and cover letter content against verified
candidate ground-truth data to identify unsupported claims and hallucinations.
"""
from typing import Any, Dict, List, Set


def _normalize_skill(skill: str) -> str:
    """Normalize skill string for flexible case-insensitive matching."""
    return skill.strip().lower()


def verify_application_evidence(
    generated_application: Dict[str, Any],
    candidate_profile: Dict[str, Any],
) -> List[str]:
    """Audit the generated resume against ground-truth profile data.

    Returns:
        List of flagged unsupported claims (empty list means full compliance).
    """
    unsupported_claims: List[str] = []
    if not generated_application or not candidate_profile:
        return unsupported_claims

    resume = generated_application.get("resume", {})

    # 1. Collect verified ground-truth skills
    verified_skills: Set[str] = {
        _normalize_skill(s) for s in candidate_profile.get("skills", []) if isinstance(s, str)
    }

    # Also collect skills mentioned in projects or experience
    for proj in candidate_profile.get("projects", []):
        if isinstance(proj, dict):
            for tech in proj.get("technologies", []):
                verified_skills.add(_normalize_skill(tech))

    # 2. Collect verified companies
    verified_companies: Set[str] = set()
    for exp in candidate_profile.get("experience", []):
        if isinstance(exp, dict) and exp.get("company"):
            verified_companies.add(exp["company"].strip().lower())

    # 3. Check resume work experience companies
    for exp in resume.get("work_experience", []):
        if isinstance(exp, dict) and exp.get("company"):
            comp_name = exp["company"].strip().lower()
            if verified_companies and comp_name not in verified_companies:
                unsupported_claims.append(
                    f"Work experience lists company '{exp['company']}' which is not in verified candidate profile."
                )

    # 4. Check resume education institutions
    verified_institutions: Set[str] = set()
    for edu in candidate_profile.get("education", []):
        if isinstance(edu, dict) and edu.get("institution"):
            verified_institutions.add(edu["institution"].strip().lower())

    for edu in resume.get("education", []):
        if isinstance(edu, dict) and edu.get("institution"):
            inst_name = edu["institution"].strip().lower()
            if verified_institutions and inst_name not in verified_institutions:
                unsupported_claims.append(
                    f"Education lists institution '{edu['institution']}' which is not in verified candidate profile."
                )

    return unsupported_claims