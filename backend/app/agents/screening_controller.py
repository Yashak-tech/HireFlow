"""
Screening Controller State Machine (Phase 5).

Manages the turn-by-turn interview state machine with states:
  VERIFY_NAME → CHECK_READINESS → INTERVIEW → WRAPUP

Handles adaptive follow-up probing (up to 2 attempts for vague answers),
skip handling, and state transitions. Integrates anti-tamper guard checks
on every candidate input.
"""
import logging
from typing import Optional, Dict, Any, Tuple

from app.agents.anti_tamper_guard import classify_tamper_attempt, is_empty_or_skip

logger = logging.getLogger(__name__)


# ─── Interview States ────────────────────────────────────────────────────

class InterviewState:
    """Interview state constants matching DB status column."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ABORTED = "aborted"  # Tamper-terminated


def evaluate_answer_quality(answer_text: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluate whether an answer is sufficiently detailed to proceed.
    Returns (is_sufficient, follow_up_prompt).

    Simple heuristic: answers under 20 words or very generic are
    considered vague and receive a follow-up probe.
    """
    clean = answer_text.strip()
    word_count = len(clean.split())

    if word_count < 15:
        return False, (
            "Thank you for your response. Could you elaborate a bit more? "
            "I'm looking for specific examples, technologies used, "
            "or concrete outcomes from your experience."
        )

    # Check for overly generic responses
    generic_phrases = [
        "i have experience", "i am familiar", "i know how to",
        "i've worked with", "i can do", "yes i have", "i think so",
    ]
    lower = clean.lower()
    if any(phrase in lower for phrase in generic_phrases) and word_count < 30:
        return False, (
            "I appreciate that. Could you give me a specific example? "
            "Perhaps a project or situation where you applied this skill, "
            "including the challenges you faced and how you overcame them?"
        )

    return True, None


def generate_transition_message(
    from_state: str,
    to_state: str,
    candidate_name: str,
    question_text: Optional[str] = None,
    question_index: int = 0,
    total_questions: int = 5,
) -> str:
    """Generate appropriate AI message for state transitions."""

    if to_state == InterviewState.IN_PROGRESS and question_index == 0:
        return (
            f"Great, let's begin the interview! I'll ask you {total_questions} questions "
            f"covering technical depth, problem-solving, and culture fit. "
            f"Take your time with each answer — quality matters more than speed.\n\n"
            f"**Question 1 of {total_questions}:**\n{question_text}"
        )

    if to_state == InterviewState.IN_PROGRESS and question_text:
        return (
            f"Thank you for that response.\n\n"
            f"**Question {question_index + 1} of {total_questions}:**\n{question_text}"
        )

    if to_state == InterviewState.COMPLETED:
        return (
            f"Thank you, {candidate_name}! That concludes our interview. "
            f"I've recorded all your responses. The hiring team will review your "
            f"interview along with your resume assessment and get back to you soon. "
            f"Thank you for your time and thoughtful answers!"
        )

    if to_state == InterviewState.ABORTED:
        return (
            "This interview session has been terminated due to a security policy violation. "
            "The incident has been logged and will be reviewed by the hiring team."
        )

    return ""


def process_interview_turn(
    candidate_input: str,
    current_status: str,
    current_question_index: int,
    total_questions: int,
    candidate_name: str,
    current_question_text: Optional[str] = None,
    next_question_text: Optional[str] = None,
    attempt_number: int = 1,
) -> Dict[str, Any]:
    """
    Process a single turn in the interview state machine.

    Returns a dict with:
        - new_status: updated interview status
        - new_question_index: updated question index
        - tamper_flag: whether tamper was detected
        - tamper_details: details of tamper if detected
        - follow_up_prompt: if answer needs clarification
        - ai_message: response message to send to candidate
        - should_save_answer: whether to persist the answer
        - answer_skipped: whether the answer was skipped
    """
    result = {
        "new_status": current_status,
        "new_question_index": current_question_index,
        "tamper_flag": False,
        "tamper_details": None,
        "follow_up_prompt": None,
        "ai_message": "",
        "should_save_answer": True,
        "answer_skipped": False,
    }

    # 1. Anti-tamper check on every input
    is_tamper, tamper_details = classify_tamper_attempt(candidate_input)
    if is_tamper:
        result["new_status"] = InterviewState.ABORTED
        result["tamper_flag"] = True
        result["tamper_details"] = tamper_details
        result["should_save_answer"] = True
        result["ai_message"] = generate_transition_message(
            current_status, InterviewState.ABORTED, candidate_name
        )
        logger.warning(
            "Interview aborted due to tamper detection for candidate '%s': %s",
            candidate_name, tamper_details
        )
        return result

    # 2. Handle skip/empty answers
    if is_empty_or_skip(candidate_input):
        result["answer_skipped"] = True
        result["should_save_answer"] = True

        # Move to next question or wrap up
        next_index = current_question_index + 1
        if next_index >= total_questions:
            result["new_status"] = InterviewState.COMPLETED
            result["new_question_index"] = next_index
            result["ai_message"] = generate_transition_message(
                current_status, InterviewState.COMPLETED, candidate_name
            )
        else:
            result["new_question_index"] = next_index
            result["ai_message"] = generate_transition_message(
                current_status, InterviewState.IN_PROGRESS,
                candidate_name, next_question_text, next_index, total_questions
            )
        return result

    # 3. Evaluate answer quality
    is_sufficient, follow_up = evaluate_answer_quality(candidate_input)

    if not is_sufficient and attempt_number < 2:
        # Request follow-up (max 2 attempts per question)
        result["follow_up_prompt"] = follow_up
        result["should_save_answer"] = True
        result["ai_message"] = follow_up or "Could you provide more detail?"
        return result

    # 4. Answer accepted — advance to next question or finish
    result["should_save_answer"] = True
    next_index = current_question_index + 1

    if next_index >= total_questions:
        result["new_status"] = InterviewState.COMPLETED
        result["new_question_index"] = next_index
        result["ai_message"] = generate_transition_message(
            current_status, InterviewState.COMPLETED, candidate_name
        )
    else:
        result["new_question_index"] = next_index
        result["ai_message"] = generate_transition_message(
            current_status, InterviewState.IN_PROGRESS,
            candidate_name, next_question_text, next_index, total_questions
        )

    return result
