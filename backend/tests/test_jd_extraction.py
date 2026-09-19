"""
Test Job Description Criteria Extraction.
Verifies:
1. Extraction removes header-only lines like 'Education:'
2. Properly categorizes education, experience, technical skills, and responsibilities
3. Extracts core technical competencies like Python, React, Docker, AWS, PostgreSQL
"""
import pytest
from app.services.intelligence_extractor import extract_job_criteria_deterministic


def test_job_criteria_extraction_cleanliness():
    sample_jd = """
    Senior Full-Stack Engineer
    Engineering Department
    
    About the Role:
    We are seeking a Senior Full-Stack Engineer to build resilient distributed services and responsive React applications.
    
    Responsibilities:
    - Develop responsive frontend applications using React.js.
    - Build scalable microservices using Python and FastAPI.
    - Design and optimize PostgreSQL databases.
    - Containerize applications using Docker.
    - Deploy and maintain applications on AWS.
    - Write clean, maintainable, and well-tested code.
    - Collaborate with frontend and product teams to deliver production-ready features.
    
    Requirements:
    - Minimum 3 years of software development experience.
    - At least 2 years of backend development experience.
    - Experience building and deploying production APIs.
    - Experience working with cloud platforms such as AWS.
    
    Education:
    - Bachelor's degree in Computer Science, Information Technology, Engineering, or a related field.
    
    Nice to Have:
    - Experience with Kubernetes and Terraform.
    - Familiarity with LLMs and AI APIs.
    """

    criteria = extract_job_criteria_deterministic(sample_jd)

    # 1. Verify no header-only items in must_have or nice_to_have
    assert "Education:" not in criteria.must_have
    assert "Requirements:" not in criteria.must_have
    assert "Responsibilities:" not in criteria.must_have
    assert "Nice to Have:" not in criteria.must_have
    assert "About the Role:" not in criteria.must_have

    # 2. Verify skills are properly extracted
    assert "Python" in criteria.required_skills
    assert "React" in criteria.required_skills
    assert "PostgreSQL" in criteria.required_skills
    assert "Docker" in criteria.required_skills
    assert "AWS" in criteria.required_skills

    # 3. Verify nice-to-have skills
    assert any(s in criteria.preferred_skills or s in criteria.required_skills for s in ["Kubernetes", "Terraform", "LLMs / AI"])

    # 4. Verify seniority
    assert criteria.seniority in ("Senior", "Principal / Lead")

    # 5. Verify education is extracted
    assert any("Bachelor" in req for req in criteria.education_requirements)

    # 6. Verify responsibilities
    assert len(criteria.responsibilities) >= 4
