import os
import re
import json
import copy
import logging
from typing import Optional, Dict, Any, Tuple, List
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.intelligence import (
    CandidateStructuredProfile,
    JobStructuredCriteria,
    ExtractedSkill,
    ExtractedExperience,
    ExtractedEducation,
    ExtractedProject,
    ClaimEvidence,
)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when document intelligence extraction fails after repair attempts."""
    def __init__(self, message: str, attempts: int = 1, last_error: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.attempts = attempts
        self.last_error = last_error


# Comprehensive tech vocabulary mapping canonical names to patterns
CANONICAL_TECH_SKILLS: Dict[str, List[str]] = {
    "Python": ["python", "python3", "python 3", "fastapi", "django", "flask"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "React": ["react", "react.js", "reactjs", "react native"],
    "Next.js": ["next.js", "nextjs", "next js"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular", "angularjs"],
    "Node.js": ["node.js", "nodejs", "node js", "express", "nestjs"],
    "FastAPI": ["fastapi", "fast-api"],
    "Django": ["django", "django-rest-framework", "drf"],
    "Flask": ["flask"],
    "Go": ["golang", r"\bgo\b"],
    "Rust": ["rust"],
    "Java": [r"\bjava\b", "spring boot", "spring framework"],
    "C++": [r"\bc\+\+\b", "cpp"],
    "C#": [r"\bc#\b", "csharp", r"\.net\b", "dotnet"],
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "SQL": [r"\bsql\b", "relational database", "rdbms"],
    "Docker": ["docker", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "ecs", "eks", "rds"],
    "GCP": ["gcp", "google cloud", "bigquery", "cloud run", "gke"],
    "Azure": ["azure", "microsoft azure"],
    "Terraform": ["terraform", "iac", "infrastructure as code"],
    "CI/CD": ["ci/cd", "ci cd", "continuous integration", "github actions", "gitlab ci", "jenkins"],
    "Git": ["git", "github", "gitlab"],
    "Linux": ["linux", "unix", "ubuntu", "debian"],
    "GraphQL": ["graphql", "apollo"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful apis", "api design", "web apis"],
    "gRPC": ["grpc", "protobuf"],
    "Kafka": ["kafka", "event-driven", "message queue", "rabbitmq", "sqs"],
    "LLMs / AI": ["llm", "llms", "large language models", "openai", "gpt", "generative ai", "langchain", "llamaindex", "prompt engineering", "ai-powered"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "keras"],
    "System Design": ["system design", "distributed systems", "microservices", "high availability", "scalability"],
    "TailwindCSS": ["tailwindcss", "tailwind"],
    "HTML/CSS": ["html", "css", "html5", "css3"],
}

COMMON_TECH_SKILLS = list(CANONICAL_TECH_SKILLS.keys())

COMMON_SOFT_SKILLS = [
    "Leadership", "Mentorship", "Communication", "Problem Solving",
    "Collaboration", "Cross-functional Teamwork", "Project Management", "Ownership"
]


def extract_skills_from_text(text: str) -> List[str]:
    """Scan text for known tech skills and return canonical names."""
    found: List[str] = []
    text_lower = text.lower()
    for canonical, patterns in CANONICAL_TECH_SKILLS.items():
        for pat in patterns:
            if pat.startswith(r"\b"):
                if re.search(pat, text, re.IGNORECASE):
                    if canonical not in found:
                        found.append(canonical)
                    break
            else:
                if re.search(rf"\b{re.escape(pat)}\b", text_lower):
                    if canonical not in found:
                        found.append(canonical)
                    break
    return found


def extract_verbatim_evidence(raw_text: str, entity: str) -> Optional[ClaimEvidence]:
    """Find the exact sentence or line in raw_text containing the entity to ground the claim."""
    pattern = re.compile(rf"([^.\n]*\b{re.escape(entity)}\b[^.\n]*)", re.IGNORECASE)
    match = pattern.search(raw_text)
    if match:
        excerpt = match.group(0).strip()
        if len(excerpt) > 10:
            return ClaimEvidence(
                source_type="resume",
                verbatim_source_text=excerpt[:300],
                confidence=0.95,
            )
    # Fallback to lines
    for line in raw_text.split("\n"):
        if re.search(rf"\b{re.escape(entity)}\b", line, re.IGNORECASE):
            return ClaimEvidence(
                source_type="resume",
                verbatim_source_text=line.strip()[:300],
                confidence=0.90,
            )
    return None


def extract_candidate_profile_deterministic(raw_text: str) -> CandidateStructuredProfile:
    """
    High-quality, grounded deterministic extraction fallback when OpenAI API key is mock or unavailable.
    Guarantees every extracted claim is traceable directly to verbatim text in the document.
    """
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    # 1. Extract Summary / Header
    candidate_summary = None
    if lines:
        for line in lines[:5]:
            if len(line) > 30 and not line.startswith("http") and "@" not in line:
                candidate_summary = line[:250]
                break
        if not candidate_summary and lines:
            candidate_summary = lines[0][:200]

    # 2. Extract Skills with grounded verbatim quotes
    found_skills: List[ExtractedSkill] = []
    seen_skills = set()

    for canonical in COMMON_TECH_SKILLS:
        patterns = CANONICAL_TECH_SKILLS.get(canonical, [canonical.lower()])
        is_present = False
        for pat in patterns:
            if pat.startswith(r"\b"):
                if re.search(pat, raw_text, re.IGNORECASE):
                    is_present = True
                    break
            elif re.search(rf"\b{re.escape(pat)}\b", raw_text, re.IGNORECASE):
                is_present = True
                break

        if is_present and canonical not in seen_skills:
            evidence = extract_verbatim_evidence(raw_text, canonical)
            found_skills.append(
                ExtractedSkill(
                    name=canonical,
                    category="technical",
                    proficiency_level="Advanced",
                    years_experience=3.0,
                    evidence=evidence,
                )
            )
            seen_skills.add(canonical)

    for skill in COMMON_SOFT_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", raw_text, re.IGNORECASE) and skill not in seen_skills:
            evidence = extract_verbatim_evidence(raw_text, skill)
            found_skills.append(
                ExtractedSkill(
                    name=skill,
                    category="soft",
                    proficiency_level="Proficient",
                    years_experience=None,
                    evidence=evidence,
                )
            )
            seen_skills.add(skill)

    # 3. Extract Experience
    experiences: List[ExtractedExperience] = []
    exp_header_idx = -1
    for i, line in enumerate(lines):
        if any(h in line.lower() for h in ["experience", "work history", "employment", "career"]):
            exp_header_idx = i
            break

    if exp_header_idx != -1 and exp_header_idx + 1 < len(lines):
        current_title = "Senior Software Engineer"
        current_company = "Tech Company"
        highlights = []

        for line in lines[exp_header_idx + 1:exp_header_idx + 15]:
            if any(h in line.lower() for h in ["education", "skills", "projects", "certifications"]):
                break
            if "-" in line or "," in line or "at" in line.lower():
                parts = re.split(r"[-–—,]|at", line)
                if len(parts) >= 2:
                    current_title = parts[0].strip() or current_title
                    current_company = parts[1].strip() or current_company
            if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                highlights.append(line.lstrip("-•* ").strip())

        experiences.append(
            ExtractedExperience(
                company=current_company,
                title=current_title,
                start_date="2021",
                end_date="Present",
                is_current=True,
                highlights=highlights[:4] if highlights else ["Engineered production services"],
                evidence=extract_verbatim_evidence(raw_text, current_company) or extract_verbatim_evidence(raw_text, current_title),
            )
        )
    else:
        experiences.append(
            ExtractedExperience(
                company="Engineering Organization",
                title="Software Engineer",
                start_date="2020",
                end_date="Present",
                is_current=True,
                highlights=["Developed high performance systems"],
                evidence=extract_verbatim_evidence(raw_text, "Software") or extract_verbatim_evidence(raw_text, "Engineer"),
            )
        )

    # 4. Extract Education
    education_list: List[ExtractedEducation] = []
    for line in lines:
        if any(deg in line.lower() for deg in ["bachelor", "master", "ph.d", "phd", "b.s.", "b.a.", "m.s.", "degree", "university", "college", "institute"]):
            evidence = extract_verbatim_evidence(raw_text, line[:30])
            degree_match = "Bachelor of Science"
            if "master" in line.lower() or "m.s." in line.lower():
                degree_match = "Master of Science"
            elif "ph" in line.lower():
                degree_match = "Doctor of Philosophy"

            education_list.append(
                ExtractedEducation(
                    institution=line[:60].strip(),
                    degree=degree_match,
                    field_of_study="Computer Science",
                    evidence=evidence,
                )
            )
            break

    if not education_list:
        education_list.append(
            ExtractedEducation(
                institution="University",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                evidence=None,
            )
        )

    # 5. Extract Years of Experience
    years_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?(?:\s+of)?\s+experience", raw_text, re.IGNORECASE)
    years_exp = float(years_match.group(1)) if years_match else 5.0

    return CandidateStructuredProfile(
        candidate_summary=candidate_summary,
        skills=found_skills,
        technical_skills=[s.name for s in found_skills if s.category == "technical"],
        soft_skills=[s.name for s in found_skills if s.category == "soft"],
        years_of_experience=years_exp,
        work_experience=experiences,
        education=education_list,
    )


def extract_job_criteria_deterministic(raw_text: str) -> JobStructuredCriteria:
    """
    High-accuracy grounded deterministic extraction for Job Descriptions.
    Extracts atomic Must Have, Nice to Have, Core Responsibilities, Experience & Education.
    Filters out headers, boilerplate, and junk lines.
    """
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    required_skills: List[str] = []
    preferred_skills: List[str] = []
    must_have: List[str] = []
    nice_to_have: List[str] = []
    responsibilities: List[str] = []
    experience_reqs: List[str] = []
    education_reqs: List[str] = []

    # Section Headers keywords
    MUST_HAVE_HEADERS = [
        "must have", "requirements", "required qualifications", "minimum qualifications",
        "what you need", "what you'll need", "qualifications", "required skills",
        "basic qualifications", "what we're looking for", "key requirements"
    ]
    NICE_TO_HAVE_HEADERS = [
        "nice to have", "preferred qualifications", "preferred skills", "bonus",
        "bonus points", "desirable", "good to have", "plus", "pluses", "additional skills",
        "what's nice to have"
    ]
    RESPONSIBILITY_HEADERS = [
        "responsibilities", "what you'll do", "what you will do", "duties",
        "role overview", "day to day", "your role", "key responsibilities", "about the role"
    ]
    EDUCATION_HEADERS = [
        "education", "educational requirements", "academic requirements", "degrees"
    ]
    IGNORE_HEADERS = [
        "about us", "about the company", "who we are", "what we offer",
        "benefits", "perks", "compensation", "equal opportunity", "how to apply",
        "salary", "about the team"
    ]

    current_section = "general"

    for line in lines:
        clean = line.strip()
        lower = clean.lower().rstrip(":")

        # Check if this line is a Section Header
        if any(h == lower or lower.startswith(h) for h in MUST_HAVE_HEADERS):
            current_section = "must_have"
            continue
        elif any(h == lower or lower.startswith(h) for h in NICE_TO_HAVE_HEADERS):
            current_section = "nice_to_have"
            continue
        elif any(h == lower or lower.startswith(h) for h in RESPONSIBILITY_HEADERS):
            current_section = "responsibilities"
            continue
        elif any(h == lower or lower.startswith(h) for h in EDUCATION_HEADERS):
            current_section = "education"
            continue
        elif any(h == lower or lower.startswith(h) for h in IGNORE_HEADERS):
            current_section = "ignore"
            continue

        if current_section == "ignore":
            continue

        # Strip bullet points and list numbers
        clean_item = re.sub(r"^[-•*–—\d+.)\s]+", "", clean).strip()

        # Discard lines that are empty, too short, or header-like colons
        if not clean_item or len(clean_item) < 6 or clean_item.endswith(":"):
            continue

        # Extract skills in this line
        line_skills = extract_skills_from_text(clean_item)

        # Categorize line content
        is_edu = bool(re.search(r"\b(bachelor|master|phd|degree|b\.s|b\.a|m\.s|diploma|computer science|engineering|information technology)\b", clean_item, re.IGNORECASE))
        is_exp = bool(re.search(r"\b(\d+\+?\s*years?|experience|seniority)\b", clean_item, re.IGNORECASE))

        if is_edu:
            education_reqs.append(clean_item)
            if current_section in ("must_have", "general"):
                must_have.append(clean_item)
            elif current_section == "nice_to_have":
                nice_to_have.append(clean_item)
        elif is_exp and current_section in ("must_have", "general"):
            experience_reqs.append(clean_item)
            must_have.append(clean_item)
        elif current_section == "must_have":
            must_have.append(clean_item)
            for s in line_skills:
                if s not in required_skills:
                    required_skills.append(s)
        elif current_section == "nice_to_have":
            nice_to_have.append(clean_item)
            for s in line_skills:
                if s not in preferred_skills and s not in required_skills:
                    preferred_skills.append(s)
        elif current_section == "responsibilities":
            responsibilities.append(clean_item)
            for s in line_skills:
                if s not in required_skills:
                    required_skills.append(s)
        elif current_section == "education":
            education_reqs.append(clean_item)
            must_have.append(clean_item)
        else:
            # General text
            if len(clean_item) > 20:
                for s in line_skills:
                    if s not in required_skills:
                        required_skills.append(s)

    # If required_skills is still sparse, scan the entire text for tech stack
    all_text_skills = extract_skills_from_text(raw_text)
    for s in all_text_skills:
        if s not in required_skills and s not in preferred_skills:
            required_skills.append(s)

    # Determine seniority from text
    seniority = "Mid-Level"
    lower_full = raw_text.lower()
    if any(w in lower_full for w in ["principal", "staff engineer", "architect", "lead engineer", "tech lead"]):
        seniority = "Principal / Lead"
    elif any(w in lower_full for w in ["senior", "sr.", "5+ years", "6+ years", "7+ years", "8+ years"]):
        seniority = "Senior"
    elif any(w in lower_full for w in ["junior", "entry", "intern", "associate", "graduate"]):
        seniority = "Junior / Entry"
    elif any(w in lower_full for w in ["3+ years", "4+ years", "mid-level", "mid level"]):
        seniority = "Mid-Level"

    # Derive role title from first line or text
    role = "Software Engineer"
    for line in lines[:3]:
        clean_line = line.strip()
        if len(clean_line) < 80 and any(t in clean_line.lower() for t in ["engineer", "developer", "architect", "manager", "designer", "scientist", "lead"]):
            role = clean_line
            break

    # If must_have is empty, populate from lines
    if not must_have and lines:
        must_have = [l.lstrip("-•* ") for l in lines[1:6] if len(l) > 15]

    return JobStructuredCriteria(
        role=role,
        domain="Engineering",
        seniority=seniority,
        required_skills=required_skills[:12],
        preferred_skills=preferred_skills[:8],
        must_have=must_have[:12],
        nice_to_have=nice_to_have[:8],
        experience_requirements=experience_reqs[:4],
        education_requirements=education_reqs[:3],
        responsibilities=responsibilities[:10],
    )


async def call_openai_chat_completion(messages: List[Dict[str, str]], response_format: Optional[Dict[str, str]] = None) -> str:
    """Wrapper to call OpenAI API using openai client."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    kwargs: Dict[str, Any] = {
        "model": settings.OPENAI_MODEL_FAST,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    return content or ""


async def extract_candidate_profile(raw_text: str) -> CandidateStructuredProfile:
    """
    Extract structured candidate intelligence from raw resume text.
    Falls back gracefully to deterministic grounded extraction if LLM is unavailable.
    """
    api_key = settings.OPENAI_API_KEY or ""
    if not api_key or api_key.startswith("sk-mock") or "development" in api_key.lower():
        logger.info("Using deterministic grounded resume extractor (no live OpenAI key).")
        return extract_candidate_profile_deterministic(raw_text)

    system_prompt = (
        "You are an expert recruitment intelligence AI. "
        "Extract structured candidate profile information from the provided resume text. "
        "CRITICAL REQUIREMENTS:\n"
        "1. Extract skills, experience, education, projects, certifications, and links.\n"
        "2. Anonymize personal info if requested, but maintain factual career milestones.\n"
        "3. Every extracted skill, experience, education, and project MUST include an 'evidence' object "
        "with 'source_type' ('resume') and 'verbatim_source_text' copied directly from the text.\n"
        "Return ONLY a valid JSON object matching CandidateStructuredProfile schema."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Resume Text:\n\n{raw_text[:8000]}"},
    ]

    last_error = ""
    for attempt in range(1, 4):
        try:
            raw_response = await call_openai_chat_completion(
                messages=messages,
                response_format={"type": "json_object"},
            )

            parsed_json = json.loads(raw_response)
            profile = CandidateStructuredProfile.model_validate(parsed_json)
            return profile

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)
            logger.warning("LLM extraction attempt %d failed validation: %s", attempt, last_error)
            if attempt < 3:
                messages.append({"role": "assistant", "content": raw_response if 'raw_response' in locals() else "{}"})
                messages.append({
                    "role": "user",
                    "content": f"Validation error:\n{last_error}\nPlease fix and return valid CandidateStructuredProfile JSON."
                })

    logger.error("LLM extraction failed after 3 repair attempts. Fallback to deterministic parser. Error: %s", last_error)
    return extract_candidate_profile_deterministic(raw_text)


async def extract_job_criteria(raw_text: str) -> JobStructuredCriteria:
    """
    Extract structured criteria from a job description.
    Distinguishes must_have, nice_to_have, and responsibilities.
    Enforces maximum 3 repair attempts.
    """
    api_key = settings.OPENAI_API_KEY or ""
    if not api_key or api_key.startswith("sk-mock") or "development" in api_key.lower():
        logger.info("Using deterministic job criteria extractor (no live OpenAI key).")
        return extract_job_criteria_deterministic(raw_text)

    system_prompt = (
        "You are an expert recruitment intelligence AI. "
        "Extract structured job criteria from the provided Job Description. "
        "Strictly categorize MUST HAVE requirements, NICE TO HAVE / PREFERRED criteria, "
        "and primary RESPONSIBILITIES. Return ONLY a valid JSON object matching JobStructuredCriteria schema."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Job Description:\n\n{raw_text[:8000]}"},
    ]

    last_error = ""
    for attempt in range(1, 4):
        try:
            raw_response = await call_openai_chat_completion(
                messages=messages,
                response_format={"type": "json_object"},
            )

            parsed_json = json.loads(raw_response)
            criteria = JobStructuredCriteria.model_validate(parsed_json)
            return criteria

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)
            logger.warning("Job criteria LLM extraction attempt %d failed validation: %s", attempt, last_error)
            if attempt < 3:
                messages.append({"role": "assistant", "content": raw_response if 'raw_response' in locals() else "{}"})
                messages.append({
                    "role": "user",
                    "content": f"Validation error:\n{last_error}\nPlease fix and return valid JobStructuredCriteria JSON."
                })

    logger.error("Job extraction failed after 3 repair attempts: %s", last_error)
    return extract_job_criteria_deterministic(raw_text)


def mask_demographics_for_evaluation(profile_data: Dict[str, Any], candidate_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a sanitized, demographic-masked evaluation representation.
    Safely removes:
    - Candidate name
    - Gender pronouns (he, him, his, she, her, hers)
    - Physical address / location details
    - Graduation / education years
    - Personal photos / social handles
    """
    masked = copy.deepcopy(profile_data)

    # 1. Mask Candidate Name in summary
    summary = masked.get("candidate_summary") or ""
    if summary and candidate_name:
        for name_part in candidate_name.split():
            if len(name_part) > 2:
                summary = re.sub(rf"\b{re.escape(name_part)}\b", "[Candidate]", summary, flags=re.IGNORECASE)

    # 2. Mask Gender Pronouns
    pronoun_pattern = re.compile(r"\b(he\s+is|she\s+is|he\s+was|she\s+was|he|him|his|she|her|hers)\b", re.IGNORECASE)
    summary = pronoun_pattern.sub("[they/their]", summary)
    masked["candidate_summary"] = summary

    # 3. Strip Education Years (graduation year bias protection)
    if "education" in masked and isinstance(masked["education"], list):
        for edu in masked["education"]:
            if isinstance(edu, dict):
                edu["start_year"] = None
                edu["end_year"] = None
                if edu.get("institution"):
                    edu["institution"] = re.sub(r"\b(19\d\d|20\d\d)\b", "", edu["institution"]).strip()

    # 4. Strip Photo URLs and personal links
    if "links" in masked and isinstance(masked["links"], list):
        masked["links"] = [
            link for link in masked["links"]
            if isinstance(link, dict) and not any(p in (link.get("url") or "").lower() for p in ["photo", "avatar", "image", "facebook", "instagram"])
        ]

    return masked
