"""Local Streamlit demo for the SabiPass AI FastAPI endpoint.

This interface is for development and investor demos only. It sends the same
canonical request shape documented for the Node.js backend.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Any

import requests


DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/neural/chat"
API_URL_ENV = "SABI_AI_API_URL"
OPERATOR_DEBUG_ENV = "SABI_STREAMLIT_SHOW_OPERATOR_JSON"
REQUEST_TIMEOUT_SECONDS = 8
DEMO_STUDENT_TIER = "free"
DEMO_STUDENT_TIER_LABEL = "Freemium"
DEFAULT_MODEL_KEY = "gemini_active"
LOCKED_MODEL_KEY = "claude_46_opus"
DEFAULT_STUDY_MODE_KEY = "exam"
ROUTING_CHECK_PROMPT = (
    "I have tried three times. Solve x^2 - 5x + 6 = 0 and explain why the factors give the roots."
)
DEFAULT_STUDENT_PROMPT = "How I go solve this linear equation: 2x + 4 = 10?"
PIPELINE_STEPS = ("zero_pass", "single_pass", "two_pass")
PIPELINE_LABELS = {
    "zero_pass": "Instant Check",
    "single_pass": "Guided Tutor",
    "two_pass": "Deep Tutor",
}


@dataclass(frozen=True)
class ModelOption:
    key: str
    label: str
    badge: str
    locked: bool
    description: str


@dataclass(frozen=True)
class StudyMode:
    key: str
    label: str
    app_execution_mode: str
    topic_node: str
    academic_scope: str
    exam_target: str
    placeholder: str
    sample_prompts: tuple[tuple[str, str], ...]
    progress_label: str
    progress_percent: int


MODEL_OPTIONS: tuple[ModelOption, ...] = (
    ModelOption(
        key=DEFAULT_MODEL_KEY,
        label="Gemini",
        badge="Active",
        locked=False,
        description="Student-facing default for the VC demo.",
    ),
    ModelOption(
        key=LOCKED_MODEL_KEY,
        label="Claude 4.6 Opus",
        badge="Premium",
        locked=True,
        description="Locked premium model shown for monetization strategy.",
    ),
)
MODEL_OPTIONS_BY_KEY = {option.key: option for option in MODEL_OPTIONS}


STUDY_MODES: tuple[StudyMode, ...] = (
    StudyMode(
        key="curriculum",
        label="Curriculum-Based Tutor",
        app_execution_mode="curriculum_coach",
        topic_node="linear_equations",
        academic_scope="senior_secondary_1",
        exam_target="WAEC",
        placeholder="Ask about the current curriculum topic",
        sample_prompts=(
            ("Term topic", "Explain linear equations for SS1 Term 1 with one class example."),
            ("Misconception", "Why do we subtract 4 from both sides in 2x + 4 = 10?"),
            ("Practice", "Give me one guided practice question on simple linear equations."),
        ),
        progress_label="SS1 Mathematics | Term 1",
        progress_percent=45,
    ),
    StudyMode(
        key="homework",
        label="Homework Explainer",
        app_execution_mode="homework_explainer",
        topic_node="linear_equations",
        academic_scope="senior_secondary",
        exam_target="WAEC",
        placeholder="Paste or ask about the assignment",
        sample_prompts=(
            ("Step-by-step", "My homework says solve 5x - 7 = 18. Explain it step by step."),
            ("Check work", "I got x = 4 for 3x + 6 = 18. Check my working."),
            ("Hint mode", "Give me hints only for this equation: 4x + 5 = 21."),
        ),
        progress_label="Homework Support | Algebra",
        progress_percent=30,
    ),
    StudyMode(
        key="exam",
        label="Exam Preparation",
        app_execution_mode="exam_prep",
        topic_node="linear_equations",
        academic_scope="senior_secondary",
        exam_target="WAEC",
        placeholder="Ask a WAEC or JAMB exam-prep question",
        sample_prompts=(
            ("WAEC algebra", DEFAULT_STUDENT_PROMPT),
            ("JAMB speed", "Show the fastest exam method for solving x^2 - 5x + 6 = 0."),
            ("Pidgin surds", "Abeg show me how to simplify sqrt(50) without calculator."),
        ),
        progress_label="WAEC/JAMB Mathematics | Algebra",
        progress_percent=62,
    ),
)
STUDY_MODES_BY_KEY = {mode.key: mode for mode in STUDY_MODES}


CURRICULUM_TERMS: tuple[dict[str, Any], ...] = (
    {
        "session": "Senior Secondary 1",
        "term": "Term 1",
        "progress": 45,
        "topics": ("Number bases", "Linear equations", "Angles and triangles"),
    },
    {
        "session": "Senior Secondary 1",
        "term": "Term 2",
        "progress": 18,
        "topics": ("Simultaneous equations", "Ratios", "Mensuration"),
    },
    {
        "session": "Senior Secondary 1",
        "term": "Term 3",
        "progress": 0,
        "topics": ("Statistics", "Probability", "Revision clinic"),
    },
)


EXAM_QUIZ_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "waec_linear_001",
        "exam": "WAEC",
        "topic": "Linear equations",
        "question": "If 3x + 4 = 19, what is x?",
        "choices": {"A": "3", "B": "5", "C": "7", "D": "15"},
        "answer": "B",
    },
    {
        "id": "jamb_factor_001",
        "exam": "JAMB",
        "topic": "Quadratics",
        "question": "The roots of x^2 - 5x + 6 = 0 are",
        "choices": {"A": "1 and 6", "B": "2 and 3", "C": "-2 and -3", "D": "5 and 6"},
        "answer": "B",
    },
    {
        "id": "waec_surd_001",
        "exam": "WAEC",
        "topic": "Surds",
        "question": "Simplify sqrt(50).",
        "choices": {"A": "5sqrt(2)", "B": "10sqrt(5)", "C": "25sqrt(2)", "D": "2sqrt(5)"},
        "answer": "A",
    },
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_neural_chat_payload(
    *,
    student_input: str,
    tier: str = DEMO_STUDENT_TIER,
    efficiency_mode: bool = False,
    app_execution_mode: str = "exam_prep",
    topic_node: str = "linear_equations",
    exam_target: str = "WAEC",
    academic_scope: str = "senior_secondary",
    errors_on_same_concept_space: int = 1,
    detected_frustration_signals: list[str] | None = None,
    sentiment_trends: str = "stable",
    scaffolding_flag: str = "medium",
    complexity_tolerance: str = "medium",
    history_tokens: list[str] | None = None,
) -> dict[str, Any]:
    default_history_tokens = [
        "student: I no understand linear equations",
        "assistant: Let's isolate x one step at a time",
    ]
    selected_history_tokens = [] if efficiency_mode else (history_tokens or default_history_tokens)

    return {
        "request_metadata": {
            "uuid_transaction_id": str(uuid.uuid4()),
            "timestamp": utc_timestamp(),
            "device_latency_ms": 0,
        },
        "student_identity": {
            "student_db_id": "demo_student_001",
            "tier": tier,
            "academic_scope": academic_scope,
            "exam_target": exam_target,
        },
        "efficiency_mode": efficiency_mode,
        "app_execution_mode": app_execution_mode,
        "cognitive_aptitude_profile": {
            "regression_slope": 0.12,
            "scaffolding_flag": scaffolding_flag,
            "complexity_tolerance": complexity_tolerance,
            "knowledge_decay_params": "medium",
        },
        "emotional_telemetry": {
            "rage_clicks": [],
            "caps_lock_aggression": [],
            "detected_frustration_signals": detected_frustration_signals or [],
            "sentiment_trends": sentiment_trends,
            "latency_focus_integrity": 0.94,
        },
        "current_interaction_context": {
            "raw_whiteboard_input": student_input,
            "topic_node": topic_node,
            "history_tokens": selected_history_tokens,
            "errors_on_same_concept_space": errors_on_same_concept_space,
            "previous_bot_response_id": None,
        },
        "historical_mastery_map": {
            "active_weakness_arrays": ["linear_equations"],
            "passed_topics_arrays": ["basic_arithmetic"],
        },
        "learning_session_state": {
            "topic": "algebra",
            "subtopic": topic_node,
            "micro_skill": topic_node,
            "phase": "practice",
            "attempt": max(0, errors_on_same_concept_space),
            "streak": 1,
            "mastery_score": 0.62,
            "state_version": 1,
            "current_question_id": None,
            "last_question_ids": [],
            "correct_pattern": [],
            "response_time_ms": None,
            "confidence_level": "medium",
            "hints_used": 0,
            "difficulty_level": "easy",
            "is_retention_check": False,
        },
    }


def post_neural_chat(*, api_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(api_url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def build_routing_verification_payloads(
    *,
    student_input: str = ROUTING_CHECK_PROMPT,
) -> tuple[dict[str, Any], ...]:
    return tuple(
        build_neural_chat_payload(
            student_input=student_input,
            tier=tier,
            efficiency_mode=efficiency_mode,
            topic_node="quadratic_equations",
            errors_on_same_concept_space=3,
            detected_frustration_signals=["stuck"],
            sentiment_trends="declining",
            scaffolding_flag="high",
            complexity_tolerance="low",
        )
        for tier, efficiency_mode in (
            ("free", False),
            ("premium", False),
            ("premium", True),
        )
    )


def summarize_routing_result(
    *,
    payload: dict[str, Any],
    response_data: dict[str, Any],
) -> dict[str, Any]:
    system_metadata = response_data.get("system_metadata") or {}
    interaction_context = payload["current_interaction_context"]
    student_identity = payload["student_identity"]
    return {
        "tier": student_identity["tier"],
        "efficiency_mode": payload["efficiency_mode"],
        "history_turns_sent": len(interaction_context["history_tokens"]),
        "model_env_var": system_metadata.get("model_env_var"),
        "execution_path": system_metadata.get("model_execution_path"),
        "normalized_concept": system_metadata.get("normalized_concept"),
        "llm_status": system_metadata.get("llm_status"),
    }


def verify_routing_matrix(*, api_url: str) -> list[dict[str, Any]]:
    rows = []
    for payload in build_routing_verification_payloads():
        response_data = post_neural_chat(api_url=api_url, payload=payload)
        rows.append(summarize_routing_result(payload=payload, response_data=response_data))
    return rows


def _humanize(value: Any, *, fallback: str = "Not returned") -> str:
    if value is None or value == "":
        return fallback
    return str(value).replace("_", " ").replace("-", " ").title()


def _metadata_from(response_data: dict[str, Any] | None) -> dict[str, Any]:
    if not response_data:
        return {}
    metadata = response_data.get("system_metadata")
    return metadata if isinstance(metadata, dict) else {}


def _current_model_label(metadata: dict[str, Any]) -> str:
    for key in ("model_name", "selected_model", "resolved_model", "model", "model_id"):
        value = metadata.get(key)
        if value:
            return str(value)
    if metadata.get("model_env_var"):
        return str(metadata["model_env_var"])
    return "Awaiting first response"


def _normalize_pipeline_layer(
    response_data: dict[str, Any] | None,
    metadata: dict[str, Any] | None = None,
) -> str:
    response_data = response_data or {}
    metadata = metadata or _metadata_from(response_data)
    response_type = str(response_data.get("response_type") or "").lower()
    execution_path = str(metadata.get("model_execution_path") or "").strip().lower()
    normalized = execution_path.replace("-", "_")

    if response_type == "zero_pass_response" or normalized in {"zero_pass", "zero_pass_response"}:
        return "zero_pass"
    if normalized in {"two_pass", "two"}:
        return "two_pass"
    if normalized in {"single_pass", "single"}:
        return "single_pass"
    return "single_pass"


def _pipeline_label(layer: str) -> str:
    return PIPELINE_LABELS.get(layer, _humanize(layer))


def _parse_source_tag(source_tag: str) -> dict[str, str]:
    parsed = {"raw": source_tag}
    parts = [part for part in source_tag.split(";") if part]
    if parts and "=" not in parts[0]:
        parsed["version"] = parts[0]

    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        parsed[key] = value
    return parsed


def _source_title(parsed_source: dict[str, str], index: int) -> str:
    doc_id = parsed_source.get("doc_id")
    source_type = parsed_source.get("source_type")
    collection = parsed_source.get("collection")
    title = doc_id or source_type or collection or f"Source {index + 1}"
    return str(title).replace("_", " ")


def _build_history_tokens(messages: list[dict[str, Any]], *, max_tokens: int = 3) -> list[str]:
    history_tokens: list[str] = []
    for message in messages:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        history_tokens.append(f"{role}: {content[:260]}")
    return history_tokens[-max_tokens:]


def _response_summary(response_data: dict[str, Any]) -> str:
    text = str(response_data.get("tutor_conversational_text") or "").strip()
    return text or "No tutor response text was returned."


def _safe_response_status(
    response_data: dict[str, Any] | None,
    elapsed_ms: int | None = None,
) -> dict[str, str]:
    metadata = _metadata_from(response_data)
    response_data = response_data or {}
    llm_status = str(metadata.get("llm_status") or "")
    demo_status = str(metadata.get("demo_response_status") or "")
    pipeline_status = str(metadata.get("pipeline_status") or "")
    latency_text = f" Response time: {elapsed_ms} ms." if elapsed_ms is not None else ""

    if not response_data:
        return {
            "label": "Ready",
            "detail": "Choose a tutoring mode and send a sample prompt.",
            "tone": "ready",
        }

    if pipeline_status == "request_failed":
        return {
            "label": "Connection Needed",
            "detail": "The student view is safe; reconnect the local AI service to continue live turns.",
            "tone": "caution",
        }

    if demo_status == "deterministic_supported_prompt" or llm_status in {
        "not_needed_deterministic",
        "not_needed_zero_pass",
    }:
        return {
            "label": "Demo-Safe Response",
            "detail": "Answered from verified SabiPass tutoring logic for this demo prompt." + latency_text,
            "tone": "safe",
        }

    if llm_status == "local_fallback" or demo_status == "safety_fallback":
        return {
            "label": "Safety Response",
            "detail": "SabiPass kept the tutoring flow available with a guided local explanation."
            + latency_text,
            "tone": "safe",
        }

    if llm_status == "completed":
        return {
            "label": "Live Tutor Response",
            "detail": "Answered through the live SabiPass AI route." + latency_text,
            "tone": "live",
        }

    return {
        "label": "Tutor Response Ready",
        "detail": "The student-facing answer is ready." + latency_text,
        "tone": "ready",
    }


def _source_summary(metadata: dict[str, Any]) -> str:
    source_tags = metadata.get("source_tags") or []
    if source_tags:
        return f"{len(source_tags)} verified item(s)"
    if str(metadata.get("llm_status") or "") in {
        "local_fallback",
        "not_needed_deterministic",
        "not_needed_zero_pass",
    }:
        return "Safety layer"
    return "Tutor knowledge"


def _safe_operator_response(response_data: dict[str, Any] | None) -> dict[str, Any]:
    response_data = response_data or {}
    metadata = _metadata_from(response_data)
    safe_metadata_keys = {
        "pipeline_status",
        "normalized_concept",
        "teaching_mode",
        "rag_status",
        "llm_status",
        "demo_mode",
        "demo_response_status",
        "zero_pass_status",
    }
    return {
        "request_id": response_data.get("request_id"),
        "response_type": response_data.get("response_type"),
        "is_atomic": response_data.get("is_atomic"),
        "system_metadata": {
            key: metadata.get(key)
            for key in safe_metadata_keys
            if key in metadata
        },
    }


def _inject_theme(st: Any) -> None:
    st.markdown(
        """
        <style>
        :root{--sabi-bg:#090a0c;--sabi-panel:#111418;--sabi-ink:#f7f8fa;--sabi-muted:#9aa5b1;--sabi-line:rgba(255,255,255,.10);--sabi-accent:#27d3b5;--sabi-accent-2:#f4b84a}
        .stApp{background:linear-gradient(140deg,rgba(39,211,181,.06),transparent 34%),linear-gradient(220deg,rgba(244,184,74,.05),transparent 42%),var(--sabi-bg);color:var(--sabi-ink)}
        header[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{display:none!important;visibility:hidden;height:0;background:transparent!important}
        [data-testid="stSidebar"]{background:#0d0f12;border-right:1px solid var(--sabi-line)}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span{color:var(--sabi-ink)}
        .block-container{max-width:1240px;padding-top:1.35rem;padding-bottom:6rem}
        .sabi-hero{border:1px solid var(--sabi-line);background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.018));border-radius:10px;padding:1rem 1.15rem .95rem;margin-bottom:.85rem}
        .sabi-eyebrow,.sabi-side-label,.sabi-meta-k{color:var(--sabi-accent);font-size:.72rem;font-weight:800;letter-spacing:0;text-transform:uppercase;margin-bottom:.38rem}
        .sabi-hero h1{color:var(--sabi-ink);font-size:clamp(1.65rem,2.4vw,2.45rem);line-height:1.08;letter-spacing:0;margin:0 0 .45rem}
        .sabi-hero p,.sabi-side-subtle,.sabi-source-meta,.sabi-source-raw{color:var(--sabi-muted);font-size:.78rem;overflow-wrap:anywhere}
        .sabi-side-card,.sabi-empty-state{border:1px solid var(--sabi-line);background:rgba(17,20,24,.88);border-radius:12px;padding:1rem;margin:.8rem 0 1rem}
        .sabi-side-value{color:var(--sabi-ink);font-size:1rem;font-weight:750;overflow-wrap:anywhere}
        div[data-testid="stChatMessage"]{border:1px solid var(--sabi-line);border-radius:14px;background:rgba(17,20,24,.72);box-shadow:0 14px 44px rgba(0,0,0,.18)}
        div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]){background:rgba(24,34,31,.82)}
        .sabi-answer{color:var(--sabi-ink);font-size:1rem;line-height:1.62;margin:.15rem 0 .95rem}
        .sabi-pipeline{align-items:center;display:flex;gap:.55rem;margin:.1rem 0 .9rem;flex-wrap:wrap}
        .sabi-step{border:1px solid var(--sabi-line);border-radius:999px;color:var(--sabi-muted);font-size:.78rem;font-weight:700;padding:.32rem .68rem;white-space:nowrap}
        .sabi-step.active{border-color:rgba(39,211,181,.8);background:rgba(39,211,181,.13);color:var(--sabi-ink)}
        .sabi-step.zero-pass.active{border-color:rgba(244,184,74,.82);background:rgba(244,184,74,.14)}
        .sabi-meta-grid{display:grid;gap:.65rem;grid-template-columns:repeat(3,minmax(0,1fr));margin:.9rem 0}
        .sabi-meta-item,.sabi-source{border:1px solid var(--sabi-line);background:rgba(255,255,255,.035);border-radius:10px;padding:.72rem;min-width:0}
        .sabi-meta-v,.sabi-source-name{color:var(--sabi-ink);font-size:.92rem;font-weight:760;overflow-wrap:anywhere}
        .sabi-status-banner{border:1px solid var(--sabi-line);background:rgba(255,255,255,.04);border-radius:10px;padding:.72rem .82rem;margin:.35rem 0 .8rem}
        .sabi-status-top{align-items:center;display:flex;gap:.5rem;color:var(--sabi-ink);font-weight:820;font-size:.92rem}
        .sabi-status-dot{border-radius:999px;display:inline-block;height:.62rem;width:.62rem;background:var(--sabi-muted)}
        .sabi-status-banner.safe .sabi-status-dot{background:var(--sabi-accent)}
        .sabi-status-banner.live .sabi-status-dot{background:#7cb7ff}
        .sabi-status-banner.caution{border-color:rgba(244,184,74,.48);background:rgba(244,184,74,.08)}
        .sabi-status-banner.caution .sabi-status-dot{background:var(--sabi-accent-2)}
        .sabi-status-detail{color:var(--sabi-muted);font-size:.78rem;line-height:1.45;margin-top:.22rem}
        .sabi-sources-title{color:var(--sabi-ink);font-size:.88rem;font-weight:800;margin:1rem 0 .55rem}
        .sabi-source-list{display:grid;gap:.55rem}.sabi-empty-state{color:var(--sabi-muted)}
        .sabi-mode-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:.85rem 0 1rem}
        .sabi-mode-card{border:1px solid var(--sabi-line);background:rgba(255,255,255,.035);border-radius:10px;padding:.82rem;min-width:0}
        .sabi-mode-card.active{border-color:rgba(39,211,181,.72);background:rgba(39,211,181,.105)}
        .sabi-mode-name{color:var(--sabi-ink);font-weight:820;font-size:.95rem;line-height:1.25}
        .sabi-mode-meta{color:var(--sabi-muted);font-size:.76rem;margin-top:.34rem;overflow-wrap:anywhere}
        .sabi-toolbar{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,280px);gap:.85rem;align-items:end;margin:1rem 0 .55rem}
        .sabi-chip-row{display:flex;gap:.45rem;flex-wrap:wrap;margin-top:.45rem}
        .sabi-chip{border:1px solid var(--sabi-line);border-radius:999px;color:var(--sabi-muted);font-size:.74rem;font-weight:760;padding:.26rem .58rem}
        .sabi-chip.active{border-color:rgba(39,211,181,.7);background:rgba(39,211,181,.12);color:var(--sabi-ink)}
        .sabi-lock-note{border:1px solid rgba(244,184,74,.34);background:rgba(244,184,74,.08);border-radius:10px;color:var(--sabi-ink);font-size:.82rem;line-height:1.45;padding:.72rem;margin:.55rem 0}
        .sabi-progress-row{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:.38rem 0 .32rem}
        .sabi-progress-label{color:var(--sabi-ink);font-size:.86rem;font-weight:800}
        .sabi-progress-value{color:var(--sabi-accent);font-size:.82rem;font-weight:850;white-space:nowrap}
        .sabi-term-list{display:grid;gap:.55rem;margin-top:.55rem}
        .sabi-term{border:1px solid var(--sabi-line);border-radius:10px;padding:.68rem;background:rgba(255,255,255,.026)}
        .sabi-term-top{display:flex;justify-content:space-between;gap:.65rem;color:var(--sabi-ink);font-size:.82rem;font-weight:780}
        .sabi-term-topic{color:var(--sabi-muted);font-size:.75rem;margin-top:.26rem;overflow-wrap:anywhere}
        .sabi-price-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.65rem;margin:.85rem 0}
        .sabi-price{border:1px solid var(--sabi-line);border-radius:10px;background:rgba(255,255,255,.035);padding:.78rem}
        .sabi-price.featured{border-color:rgba(39,211,181,.72);background:rgba(39,211,181,.10)}
        .sabi-price-name{font-weight:850;color:var(--sabi-ink);font-size:.92rem}
        .sabi-price-amount{font-size:1.22rem;font-weight:900;color:var(--sabi-ink);margin:.25rem 0}
        .sabi-price-copy{font-size:.76rem;color:var(--sabi-muted);line-height:1.45}
        .sabi-quiz-question{border:1px solid var(--sabi-line);border-radius:10px;background:rgba(255,255,255,.03);padding:.68rem;margin:.55rem 0}
        .sabi-quiz-meta{color:var(--sabi-accent-2);font-size:.7rem;font-weight:850;text-transform:uppercase}
        .sabi-quiz-text{color:var(--sabi-ink);font-weight:760;font-size:.84rem;line-height:1.35;margin-top:.2rem}
        .sabi-bottom-spacer{height:9rem}
        .stButton>button,[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{border-radius:9px;border:1px solid var(--sabi-line);background:rgba(255,255,255,.055);color:var(--sabi-ink);min-height:2.55rem;font-weight:750}
        .stButton>button:hover,[data-testid="stBaseButton-secondary"]:hover,[data-testid="stBaseButton-primary"]:hover{border-color:rgba(39,211,181,.7);color:var(--sabi-ink)}
        [data-testid="stChatInput"]{border:1px solid var(--sabi-line)!important;border-radius:12px;background:rgba(9,10,12,.72);box-shadow:0 12px 36px rgba(0,0,0,.35)}
        [data-testid="stTextInputRootElement"],[data-testid="stTextInputRootElement"]>div{background:rgba(255,255,255,.06)!important;border:1px solid var(--sabi-line)!important}
        textarea,input,[data-baseweb="select"]>div,[data-baseweb="input"]>div{border-radius:9px;color:var(--sabi-ink)!important}
        [data-testid="stChatInput"] *,[data-testid="stChatInput"] textarea{background:rgba(17,20,24,.96)!important;color:var(--sabi-ink)!important}
        [data-testid="stChatInput"] textarea::placeholder{color:var(--sabi-muted)!important;opacity:1!important}
        [data-testid="stChatInputSubmitButton"]{background:rgba(39,211,181,.14)!important;color:var(--sabi-ink)!important}
        [data-testid="stBottom"],[data-testid="stBottom"]>div,[data-testid="stBottomBlockContainer"],[data-testid="stBottomBlockContainer"]>div{background:linear-gradient(180deg,rgba(9,10,12,.02),var(--sabi-bg) 28%)!important}
        div[data-testid="stExpander"]{border:1px solid var(--sabi-line);border-radius:10px;background:rgba(255,255,255,.025)}
        @media(max-width:900px){.sabi-mode-grid,.sabi-price-grid{grid-template-columns:1fr}.sabi-toolbar{grid-template-columns:1fr}}
        @media(max-width:760px){.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem}.sabi-meta-grid{grid-template-columns:1fr}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state(st: Any) -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_system_metadata", {})
    st.session_state.setdefault("last_response_data", {})
    st.session_state.setdefault("selected_model_key", DEFAULT_MODEL_KEY)
    st.session_state.setdefault("show_premium_modal", False)
    st.session_state.setdefault("study_mode_key", DEFAULT_STUDY_MODE_KEY)
    st.session_state.setdefault("exam_target", "WAEC")
    st.session_state.setdefault("quiz_feedback", None)


def _render_sidebar(st: Any) -> tuple[str, bool]:
    st.sidebar.markdown(
        """
        <div class="sabi-side-card">
            <div class="sabi-side-label">SabiPass AI</div>
            <div class="sabi-side-value">VC Demo Console</div>
            <div class="sabi-side-subtle">Student experience simulator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"""
        <div class="sabi-side-card">
            <div class="sabi-side-label">Student Plan</div>
            <div class="sabi-side-value">{escape(DEMO_STUDENT_TIER_LABEL)}</div>
            <div class="sabi-side-subtle">Demo account with the active student model.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar.expander("Operator settings", expanded=False):
        api_url = st.text_input(
            "FastAPI endpoint",
            value=os.getenv(API_URL_ENV, DEFAULT_API_URL),
        )
        efficiency_mode = st.toggle("Efficiency mode", value=False)

    metadata = st.session_state.get("last_system_metadata") or {}
    last_response = st.session_state.get("last_response_data") or {}
    status = _safe_response_status(last_response)
    st.sidebar.markdown(
        f"""
        <div class="sabi-side-card">
            <div class="sabi-side-label">Current Model</div>
            <div class="sabi-side-value">Gemini</div>
            <div class="sabi-side-subtle">Live route when available, demo-safe tutoring when needed.</div>
        </div>
        <div class="sabi-side-card">
            <div class="sabi-side-label">Last Tutor Status</div>
            <div class="sabi-side-value">{escape(status["label"])}</div>
            <div class="sabi-side-subtle">Topic: {escape(_humanize(metadata.get("normalized_concept"), fallback="Waiting for prompt"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_system_metadata = {}
        st.session_state.last_response_data = {}
        _rerun(st)

    return api_url, efficiency_mode


def _render_hero(st: Any) -> None:
    st.markdown(
        """
        <section class="sabi-hero">
            <div class="sabi-eyebrow">SabiPass AI VC demo</div>
            <h1>Maths tutor workspace for WAEC, JAMB, homework, and curriculum coaching.</h1>
            <p>Ask a real tutoring question, switch modes, or open the Premium model upsell while the safety layer keeps demo prompts predictable.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _study_mode_from_key(key: str | None) -> StudyMode:
    return STUDY_MODES_BY_KEY.get(key or "", STUDY_MODES_BY_KEY[DEFAULT_STUDY_MODE_KEY])


def _render_study_mode_selector(st: Any) -> StudyMode:
    current_mode = _study_mode_from_key(st.session_state.get("study_mode_key"))
    labels = [mode.label for mode in STUDY_MODES]
    # st.session_state.setdefault("study_mode_label", current_mode.label)

    selected_label = st.radio(
        "Study mode",
        options=labels,
        horizontal=True,
        # index=labels.index(current_mode.label),
        key="study_mode_label",
    )
    selected_mode = next(mode for mode in STUDY_MODES if mode.label == selected_label)
    st.session_state.study_mode_key = selected_mode.key
    _render_mode_cards(st, selected_mode)
    return selected_mode


def _render_mode_cards(st: Any, selected_mode: StudyMode) -> None:
    cards = ['<div class="sabi-mode-grid">']
    for mode in STUDY_MODES:
        active_class = " active" if mode.key == selected_mode.key else ""
        cards.append(
            '<div class="sabi-mode-card{active}">'
            '<div class="sabi-mode-name">{label}</div>'
            '<div class="sabi-mode-meta">Topic: {topic} | Track: {exam}</div>'
            '<div class="sabi-mode-meta">Ready for guided student prompts.</div>'
            "</div>".format(
                active=active_class,
                label=escape(mode.label),
                topic=escape(_humanize(mode.topic_node)),
                exam=escape(mode.exam_target),
            )
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def _render_exam_target_picker(st: Any, selected_mode: StudyMode) -> str:
    if selected_mode.key != "exam":
        return selected_mode.exam_target

    return st.radio(
        "Exam track",
        options=["WAEC", "JAMB"],
        horizontal=True,
        key="exam_target",
    )


def _render_mode_workspace(
    st: Any,
    *,
    selected_mode: StudyMode,
    api_url: str,
    efficiency_mode: bool,
    exam_target: str,
) -> None:
    if selected_mode.key == "curriculum":
        _render_curriculum_scope(st)
        return

    if selected_mode.key == "homework":
        _render_homework_workspace(
            st,
            selected_mode=selected_mode,
            api_url=api_url,
            efficiency_mode=efficiency_mode,
            exam_target=exam_target,
        )
        return

    st.markdown(
        f"""
        <div class="sabi-lock-note">
            <strong>{escape(exam_target)} exam prep is active.</strong>
            Sample prompts below show algebra, surds, and stuck-student coaching on the {escape(DEMO_STUDENT_TIER_LABEL)} plan.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_curriculum_scope(st: Any) -> None:
    term_html = ['<div class="sabi-term-list">']
    for term in CURRICULUM_TERMS:
        topics = ", ".join(term["topics"])
        term_html.append(
            '<div class="sabi-term">'
            '<div class="sabi-term-top">'
            f'<span>{escape(str(term["session"]))} | {escape(str(term["term"]))}</span>'
            f'<span>{escape(str(term["progress"]))}% complete</span>'
            "</div>"
            f'<div class="sabi-term-topic">{escape(topics)}</div>'
            "</div>"
        )
    term_html.append("</div>")
    st.markdown(
        '<div class="sabi-side-label">Government Curriculum Mock</div>',
        unsafe_allow_html=True,
    )
    st.markdown("".join(term_html), unsafe_allow_html=True)


def _render_homework_workspace(
    st: Any,
    *,
    selected_mode: StudyMode,
    api_url: str,
    efficiency_mode: bool,
    exam_target: str,
) -> None:
    with st.expander("Homework workspace", expanded=True):
        uploaded_files = st.file_uploader(
            "Upload assignment",
            type=["txt", "md", "csv", "pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="homework_uploads",
        )
        typed_assignment = st.text_area(
            "Type assignment",
            key="homework_assignment_text",
            placeholder="Paste the exact homework question here.",
            height=118,
        )
        if st.button("Explain homework", use_container_width=True):
            upload_text = _extract_uploaded_assignment_text(uploaded_files)
            prompt_parts = [
                part.strip()
                for part in (typed_assignment, upload_text)
                if str(part or "").strip()
            ]
            if not prompt_parts:
                st.warning("Add an assignment first, then I can route it to the tutor.")
                return

            _submit_prompt(
                st,
                api_url=api_url,
                selected_mode=selected_mode,
                efficiency_mode=efficiency_mode,
                exam_target=exam_target,
                prompt="Homework explainer request:\n\n" + "\n\n".join(prompt_parts),
            )
            _rerun(st)


def _extract_uploaded_assignment_text(uploaded_files: list[Any] | None) -> str:
    snippets: list[str] = []
    for uploaded_file in uploaded_files or []:
        name = str(getattr(uploaded_file, "name", "uploaded_assignment"))
        raw_bytes = uploaded_file.getvalue()
        if name.lower().endswith((".txt", ".md", ".csv")):
            try:
                decoded = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded = raw_bytes.decode("latin-1", errors="replace")
            snippets.append(f"Uploaded file {name}:\n{decoded[:1800]}")
        else:
            snippets.append(
                f"Uploaded file {name}: {len(raw_bytes)} bytes received in the demo workspace. "
                "Use the visible text or pasted assignment details for step-by-step guidance."
            )
    return "\n\n".join(snippets)


def _format_model_option(model_key: str) -> str:
    option = MODEL_OPTIONS_BY_KEY.get(model_key, MODEL_OPTIONS_BY_KEY[DEFAULT_MODEL_KEY])
    return f"{option.label} - {option.badge}"


def _handle_model_selection_change(st: Any) -> None:
    selected_key = st.session_state.get("selected_model_key", DEFAULT_MODEL_KEY)
    selected_option = MODEL_OPTIONS_BY_KEY.get(selected_key, MODEL_OPTIONS_BY_KEY[DEFAULT_MODEL_KEY])
    if selected_option.locked:
        st.session_state.show_premium_modal = True
        st.session_state.selected_model_key = DEFAULT_MODEL_KEY


def _render_model_picker(st: Any) -> ModelOption:
    option_keys = [option.key for option in MODEL_OPTIONS]
    selected_option = MODEL_OPTIONS_BY_KEY.get(
        st.session_state.get("selected_model_key", DEFAULT_MODEL_KEY),
        MODEL_OPTIONS_BY_KEY[DEFAULT_MODEL_KEY],
    )
    st.selectbox(
        "Model",
        options=option_keys,
        index=option_keys.index(selected_option.key),
        format_func=_format_model_option,
        key="selected_model_key",
        on_change=_handle_model_selection_change,
        args=(st,),
    )
    active_option = MODEL_OPTIONS_BY_KEY.get(
        st.session_state.get("selected_model_key", DEFAULT_MODEL_KEY),
        MODEL_OPTIONS_BY_KEY[DEFAULT_MODEL_KEY],
    )
    st.markdown(
        f"""
        <div class="sabi-chip-row">
            <span class="sabi-chip active">{escape(active_option.label)}</span>
            <span class="sabi-chip">{escape(DEMO_STUDENT_TIER_LABEL)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return active_option


def _render_premium_modal(st: Any) -> None:
    if not st.session_state.get("show_premium_modal"):
        return

    dialog_factory = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog_factory is None:
        st.info("Claude 4.6 Opus is locked for Premium. Gemini remains active for this demo.")
        if st.button("Continue with Gemini"):
            st.session_state.show_premium_modal = False
            _rerun(st)
        return

    @dialog_factory("Claude 4.6 Opus is Premium")
    def _premium_dialog() -> None:
        st.markdown(
            """
            <div class="sabi-lock-note">
                Claude 4.6 Opus is visible to students as a Premium upgrade.
                The Freemium demo account stays on Gemini and no payment or subscription record is changed.
            </div>
            <div class="sabi-price-grid">
                <div class="sabi-price">
                    <div class="sabi-price-name">Freemium</div>
                    <div class="sabi-price-amount">N0</div>
                    <div class="sabi-price-copy">Gemini tutor, limited history, curriculum progress preview.</div>
                </div>
                <div class="sabi-price featured">
                    <div class="sabi-price-name">Premium Student</div>
                    <div class="sabi-price-amount">N2,500/mo</div>
                    <div class="sabi-price-copy">Claude 4.6 Opus, deeper reasoning, WAEC/JAMB exam packs.</div>
                </div>
                <div class="sabi-price">
                    <div class="sabi-price-name">School Plan</div>
                    <div class="sabi-price-amount">Custom</div>
                    <div class="sabi-price-copy">Class analytics, term dashboards, and admin-managed seats.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Continue with Gemini", use_container_width=True):
            st.session_state.show_premium_modal = False
            st.session_state.selected_model_key = DEFAULT_MODEL_KEY
            _rerun(st)

    _premium_dialog()


def _render_progress_panel(st: Any, selected_mode: StudyMode) -> None:
    st.markdown(
        f"""
        <div class="sabi-side-card">
            <div class="sabi-side-label">Curriculum Progress</div>
            <div class="sabi-progress-row">
                <div class="sabi-progress-label">{escape(selected_mode.progress_label)}</div>
                <div class="sabi-progress-value">{selected_mode.progress_percent}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(selected_mode.progress_percent / 100, text=f"Term 1: {selected_mode.progress_percent}% Completed")


def _render_exam_quiz_widget(st: Any) -> None:
    st.markdown(
        """
        <div class="sabi-side-card">
            <div class="sabi-side-label">WAEC/JAMB Drill</div>
            <div class="sabi-side-value">3-question sample quiz</div>
            <div class="sabi-side-subtle">Investor demo widget</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for index, item in enumerate(EXAM_QUIZ_ITEMS, start=1):
        st.markdown(
            """
            <div class="sabi-quiz-question">
                <div class="sabi-quiz-meta">{exam} | {topic}</div>
                <div class="sabi-quiz-text">{index}. {question}</div>
            </div>
            """.format(
                exam=escape(str(item["exam"])),
                topic=escape(str(item["topic"])),
                index=index,
                question=escape(str(item["question"])),
            ),
            unsafe_allow_html=True,
        )
        choices = [f"{key}. {value}" for key, value in item["choices"].items()]
        st.radio(
            f"Answer for question {index}",
            choices,
            index=None,
            key=f"quiz_answer_{item['id']}",
            label_visibility="collapsed",
        )

    if st.button("Check quiz", use_container_width=True):
        score = 0
        for item in EXAM_QUIZ_ITEMS:
            selected = st.session_state.get(f"quiz_answer_{item['id']}")
            selected_key = str(selected or "")[:1]
            if selected_key == item["answer"]:
                score += 1
        st.session_state.quiz_feedback = f"{score}/{len(EXAM_QUIZ_ITEMS)} correct"

    if st.session_state.get("quiz_feedback"):
        st.success(st.session_state.quiz_feedback)


def _render_composer_toolbar(st: Any, selected_mode: StudyMode, exam_target: str) -> None:
    left_column, right_column = st.columns([0.68, 0.32])
    with left_column:
        st.markdown(
            f"""
            <div class="sabi-side-label">Composer</div>
            <div class="sabi-chip-row">
                <span class="sabi-chip active">{escape(selected_mode.label)}</span>
                <span class="sabi-chip">{escape(exam_target)}</span>
                <span class="sabi-chip">{escape(DEMO_STUDENT_TIER_LABEL)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right_column:
        _render_model_picker(st)


def _render_pipeline_indicator(st: Any, active_layer: str) -> None:
    step_html = []
    for step in PIPELINE_STEPS:
        active_class = " active" if step == active_layer else ""
        step_class = step.replace("_", "-")
        step_html.append(
            f'<span class="sabi-step {step_class}{active_class}">{escape(PIPELINE_LABELS[step])}</span>'
        )
    st.markdown(f'<div class="sabi-pipeline">{"".join(step_html)}</div>', unsafe_allow_html=True)


def _render_meta_grid(st: Any, response_data: dict[str, Any], elapsed_ms: int | None) -> None:
    metadata = _metadata_from(response_data)
    active_layer = _normalize_pipeline_layer(response_data, metadata)
    status = _safe_response_status(response_data, elapsed_ms)
    items = (
        ("Tutor Status", status["label"]),
        ("Learning Route", _pipeline_label(active_layer)),
        ("Topic", _humanize(metadata.get("normalized_concept"))),
        ("Study Support", _humanize(response_data.get("response_type"), fallback="Tutor Chat")),
        ("Materials", _source_summary(metadata)),
        ("Latency", f"{elapsed_ms} ms" if elapsed_ms is not None else "Not measured"),
    )
    html = ['<div class="sabi-meta-grid">']
    for key, value in items:
        html.append(
            '<div class="sabi-meta-item">'
            f'<div class="sabi-meta-k">{escape(key)}</div>'
            f'<div class="sabi-meta-v">{escape(str(value))}</div>'
            "</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_sources(st: Any, response_data: dict[str, Any]) -> None:
    metadata = _metadata_from(response_data)
    source_tags = metadata.get("source_tags") or []
    normalized_concept = str(metadata.get("normalized_concept") or "unknown concept")

    st.markdown('<div class="sabi-sources-title">Learning material used</div>', unsafe_allow_html=True)
    if source_tags:
        source_html = ['<div class="sabi-source-list">']
        for index, source_tag in enumerate(source_tags):
            parsed = _parse_source_tag(str(source_tag))
            details = [
                ("collection", parsed.get("collection")),
                ("topic", parsed.get("topic")),
                ("exam", parsed.get("exam_type")),
                ("year", parsed.get("year")),
                ("rank", parsed.get("rank")),
            ]
            detail_text = " | ".join(
                f"{label}: {value}" for label, value in details if value not in {None, ""}
            )
            source_html.append(
                """
                <div class="sabi-source">
                    <div class="sabi-source-name">{name}</div>
                    <div class="sabi-source-meta">{details}</div>
                </div>
                """.format(
                    name=escape(_source_title(parsed, index)),
                    details=escape(detail_text or "Verified SabiPass study content"),
                )
            )
        source_html.append("</div>")
        st.markdown("".join(source_html), unsafe_allow_html=True)
        return

    if _source_summary(metadata) == "Safety layer":
        st.markdown(
            f"""
            <div class="sabi-source">
                <div class="sabi-source-name">SabiPass safety guidance</div>
                <div class="sabi-source-meta">Topic: {escape(_humanize(normalized_concept).lower())}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="sabi-source">
            <div class="sabi-source-name">SabiPass tutor knowledge</div>
            <div class="sabi-source-meta">Topic: {escape(_humanize(normalized_concept).lower())}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_json_expander(
    st: Any,
    *,
    request_payload: dict[str, Any] | None,
    response_data: dict[str, Any] | None,
) -> None:
    with st.expander("Operator payload summary", expanded=False):
        request_col, response_col = st.columns(2)
        with request_col:
            st.caption("Request")
            st.json(request_payload or {})
        with response_col:
            st.caption("Response")
            st.json(_safe_operator_response(response_data))


def _render_assistant_turn(st: Any, message: dict[str, Any]) -> None:
    response_data = message.get("response") or {}
    request_payload = message.get("request")
    elapsed_ms = message.get("elapsed_ms")
    metadata = _metadata_from(response_data)
    active_layer = _normalize_pipeline_layer(response_data, metadata)
    answer = escape(_response_summary(response_data)).replace("\n", "<br>")
    status = _safe_response_status(response_data, elapsed_ms)

    _render_pipeline_indicator(st, active_layer)
    st.markdown(
        f"""
        <div class="sabi-status-banner {escape(status["tone"])}">
            <div class="sabi-status-top"><span class="sabi-status-dot"></span>{escape(status["label"])}</div>
            <div class="sabi-status-detail">{escape(status["detail"])}</div>
        </div>
        <div class="sabi-chip-row"><span class="sabi-chip active">SabiPass tutor</span></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="sabi-answer">{answer}</div>', unsafe_allow_html=True)
    _render_meta_grid(st, response_data, elapsed_ms)
    _render_sources(st, response_data)
    if os.getenv(OPERATOR_DEBUG_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        _render_json_expander(
            st,
            request_payload=request_payload,
            response_data=response_data,
        )


def _render_chat_history(st: Any) -> None:
    messages = st.session_state.get("messages", [])
    if not messages:
        st.markdown(
            """
            <div class="sabi-empty-state">
                <strong>Ready for a tutoring turn.</strong><br>
                Choose a sample prompt or ask a curriculum, homework, WAEC, or JAMB question.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for message in messages:
        role = message.get("role", "assistant")
        with st.chat_message(role):
            if role == "assistant":
                _render_assistant_turn(st, message)
            else:
                st.markdown(escape(str(message.get("content") or "")))


def _submit_prompt(
    st: Any,
    *,
    api_url: str,
    selected_mode: StudyMode,
    efficiency_mode: bool,
    exam_target: str,
    prompt: str,
) -> None:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        return

    history_tokens = _build_history_tokens(st.session_state.messages)
    payload = build_neural_chat_payload(
        student_input=cleaned_prompt,
        tier=DEMO_STUDENT_TIER,
        efficiency_mode=efficiency_mode,
        app_execution_mode=selected_mode.app_execution_mode,
        topic_node=selected_mode.topic_node,
        academic_scope=selected_mode.academic_scope,
        exam_target=exam_target,
        history_tokens=history_tokens,
    )

    st.session_state.messages.append({"role": "user", "content": cleaned_prompt})
    started_at = time.perf_counter()
    try:
        with st.spinner("Preparing SabiPass response"):
            response_data = post_neural_chat(api_url=api_url, payload=payload)
    except requests.RequestException:
        response_data = {
            "tutor_conversational_text": (
                "SabiPass is ready, but the local AI service is not connected right now. "
                "Choose a sample prompt again after the service is reconnected."
            ),
            "response_type": "text_only",
            "system_metadata": {
                "pipeline_status": "request_failed",
                "rag_mode": "none",
                "llm_status": "connection_unavailable",
                "source_tags": [],
                "demo_response_status": "connection_unavailable",
            },
        }
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)

    st.session_state.last_system_metadata = _metadata_from(response_data)
    st.session_state.last_response_data = response_data
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": _response_summary(response_data),
            "request": payload,
            "response": response_data,
            "elapsed_ms": elapsed_ms,
        }
    )


def _render_sample_prompts(
    st: Any,
    *,
    api_url: str,
    selected_mode: StudyMode,
    efficiency_mode: bool,
    exam_target: str,
) -> None:
    samples = selected_mode.sample_prompts
    columns = st.columns(len(samples))
    for column, (label, prompt) in zip(columns, samples):
        with column:
            if st.button(label, use_container_width=True):
                _submit_prompt(
                    st,
                    api_url=api_url,
                    selected_mode=selected_mode,
                    efficiency_mode=efficiency_mode,
                    exam_target=exam_target,
                    prompt=prompt,
                )
                _rerun(st)


def _rerun(st: Any) -> None:
    if hasattr(st, "rerun"):
        st.rerun()
        return
    st.experimental_rerun()


def run_app() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="SabiPass AI Demo",
        page_icon="S",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_theme(st)
    _init_session_state(st)

    api_url, efficiency_mode = _render_sidebar(st)
    _render_hero(st)
    selected_mode = _render_study_mode_selector(st)
    exam_target = _render_exam_target_picker(st, selected_mode)
    _render_premium_modal(st)

    chat_column, side_column = st.columns([0.68, 0.32], gap="large")
    with chat_column:
        _render_mode_workspace(
            st,
            selected_mode=selected_mode,
            api_url=api_url,
            efficiency_mode=efficiency_mode,
            exam_target=exam_target,
        )
        _render_composer_toolbar(st, selected_mode, exam_target)
        _render_sample_prompts(
            st,
            api_url=api_url,
            selected_mode=selected_mode,
            efficiency_mode=efficiency_mode,
            exam_target=exam_target,
        )
        _render_chat_history(st)

    with side_column:
        _render_progress_panel(st, selected_mode)
        _render_exam_quiz_widget(st)

    st.markdown('<div class="sabi-bottom-spacer"></div>', unsafe_allow_html=True)

    prompt = st.chat_input(selected_mode.placeholder)
    if prompt:
        _submit_prompt(
            st,
            api_url=api_url,
            selected_mode=selected_mode,
            efficiency_mode=efficiency_mode,
            exam_target=exam_target,
            prompt=prompt,
        )
        _rerun(st)


if __name__ == "__main__":
    run_app()
