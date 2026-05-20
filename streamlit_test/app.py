"""Local Streamlit demo for the SabiPass AI FastAPI endpoint.

This interface is for development and investor demos only. It sends the same
canonical request shape documented for the Node.js backend.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from html import escape
from typing import Any

import requests


DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/neural/chat"
API_URL_ENV = "SABI_AI_API_URL"
REQUEST_TIMEOUT_SECONDS = 20
ROUTING_CHECK_PROMPT = (
    "I have tried three times. Solve x^2 - 5x + 6 = 0 and explain why the factors give the roots."
)
DEFAULT_STUDENT_PROMPT = "How I go solve this linear equation: 2x + 4 = 10?"
PIPELINE_STEPS = ("zero_pass", "single_pass", "two_pass")
PIPELINE_LABELS = {
    "zero_pass": "Zero-pass",
    "single_pass": "Single-pass",
    "two_pass": "Two-pass",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_neural_chat_payload(
    *,
    student_input: str,
    tier: str,
    efficiency_mode: bool,
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
        "app_execution_mode": "exam_prep",
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


def _inject_theme(st: Any) -> None:
    st.markdown(
        """
        <style>
        :root{--sabi-bg:#090a0c;--sabi-panel:#111418;--sabi-ink:#f7f8fa;--sabi-muted:#9aa5b1;--sabi-line:rgba(255,255,255,.10);--sabi-accent:#27d3b5;--sabi-accent-2:#f4b84a}
        .stApp{background:linear-gradient(140deg,rgba(39,211,181,.06),transparent 34%),linear-gradient(220deg,rgba(244,184,74,.05),transparent 42%),var(--sabi-bg);color:var(--sabi-ink)}
        header[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{display:none!important;visibility:hidden;height:0;background:transparent!important}
        [data-testid="stSidebar"]{background:#0d0f12;border-right:1px solid var(--sabi-line)}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span{color:var(--sabi-ink)}
        .block-container{max-width:1180px;padding-top:2.25rem;padding-bottom:6rem}
        .sabi-hero{border:1px solid var(--sabi-line);background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.018));border-radius:14px;padding:1.2rem 1.35rem 1.15rem;margin-bottom:1.1rem}
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
        .sabi-sources-title{color:var(--sabi-ink);font-size:.88rem;font-weight:800;margin:1rem 0 .55rem}
        .sabi-source-list{display:grid;gap:.55rem}.sabi-empty-state{color:var(--sabi-muted)}
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
        @media(max-width:760px){.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem}.sabi-meta-grid{grid-template-columns:1fr}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state(st: Any) -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_system_metadata", {})
    st.session_state.setdefault("last_response_data", {})


def _render_sidebar(st: Any) -> tuple[str, str, bool]:
    st.sidebar.markdown(
        """
        <div class="sabi-side-card">
            <div class="sabi-side-label">SabiPass AI</div>
            <div class="sabi-side-value">VC Demo Console</div>
            <div class="sabi-side-subtle">Live tutor pipeline view</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_url = st.sidebar.text_input(
        "FastAPI endpoint",
        value=os.getenv(API_URL_ENV, DEFAULT_API_URL),
    )
    tier = st.sidebar.radio(
        "Tier",
        options=["free", "premium"],
        horizontal=True,
        index=0,
    )
    efficiency_mode = st.sidebar.toggle("Efficiency mode", value=False)

    metadata = st.session_state.get("last_system_metadata") or {}
    last_response = st.session_state.get("last_response_data") or {}
    model_label = _current_model_label(metadata)
    pipeline_layer = _normalize_pipeline_layer(last_response, metadata)
    model_key = "model_env_var" if metadata.get("model_env_var") else "metadata pending"
    st.sidebar.markdown(
        f"""
        <div class="sabi-side-card">
            <div class="sabi-side-label">Current Model</div>
            <div class="sabi-side-value">{escape(model_label)}</div>
            <div class="sabi-side-subtle">From API response: {escape(model_key)}</div>
        </div>
        <div class="sabi-side-card">
            <div class="sabi-side-label">Last Pipeline Layer</div>
            <div class="sabi-side-value">{escape(_pipeline_label(pipeline_layer))}</div>
            <div class="sabi-side-subtle">Normalized concept: {escape(str(metadata.get("normalized_concept") or "Not returned"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_system_metadata = {}
        st.session_state.last_response_data = {}
        _rerun(st)

    return api_url, tier, efficiency_mode


def _render_hero(st: Any) -> None:
    st.markdown(
        """
        <section class="sabi-hero">
            <div class="sabi-eyebrow">SabiPass AI cognition service</div>
            <h1>WAEC and JAMB maths tutoring, with routing visible.</h1>
            <p>Tier-aware model selection, normalized concepts, RAG source visibility, and execution-path metadata in one investor-facing chat surface.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


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
    items = (
        ("Execution Path", _pipeline_label(active_layer)),
        ("Normalized Concept", _humanize(metadata.get("normalized_concept"))),
        ("RAG Mode", _humanize(metadata.get("rag_mode"))),
        ("LLM Status", _humanize(metadata.get("llm_status"))),
        ("Response Type", _humanize(response_data.get("response_type"))),
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
    rag_mode = str(metadata.get("rag_mode") or "none")
    normalized_concept = str(metadata.get("normalized_concept") or "unknown concept")

    st.markdown('<div class="sabi-sources-title">RAG sources used</div>', unsafe_allow_html=True)
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
                    <div class="sabi-source-raw">{raw}</div>
                </div>
                """.format(
                    name=escape(_source_title(parsed, index)),
                    details=escape(detail_text or "No parsed source metadata"),
                    raw=escape(str(source_tag)),
                )
            )
        source_html.append("</div>")
        st.markdown("".join(source_html), unsafe_allow_html=True)
        return

    if rag_mode == "fallback":
        st.markdown(
            f"""
            <div class="sabi-source">
                <div class="sabi-source-name">Fallback summary</div>
                <div class="sabi-source-meta">concept: {escape(normalized_concept)} | mode: fallback</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="sabi-source">
            <div class="sabi-source-name">No RAG source tags returned</div>
            <div class="sabi-source-meta">mode: {escape(_humanize(rag_mode).lower())}</div>
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
    with st.expander("Request and response JSON", expanded=False):
        request_col, response_col = st.columns(2)
        with request_col:
            st.caption("Request")
            st.json(request_payload or {})
        with response_col:
            st.caption("Response")
            st.json(response_data or {})


def _render_assistant_turn(st: Any, message: dict[str, Any]) -> None:
    response_data = message.get("response") or {}
    request_payload = message.get("request")
    elapsed_ms = message.get("elapsed_ms")
    metadata = _metadata_from(response_data)
    active_layer = _normalize_pipeline_layer(response_data, metadata)
    answer = escape(_response_summary(response_data)).replace("\n", "<br>")

    _render_pipeline_indicator(st, active_layer)
    st.markdown(f'<div class="sabi-answer">{answer}</div>', unsafe_allow_html=True)
    _render_meta_grid(st, response_data, elapsed_ms)
    _render_sources(st, response_data)
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
                <strong>Ready for a live tutoring turn.</strong><br>
                Try a WAEC algebra prompt, a Pidgin explanation request, or a stuck-student quadratic question.
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
    tier: str,
    efficiency_mode: bool,
    prompt: str,
) -> None:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        return

    history_tokens = _build_history_tokens(st.session_state.messages)
    payload = build_neural_chat_payload(
        student_input=cleaned_prompt,
        tier=tier,
        efficiency_mode=efficiency_mode,
        history_tokens=history_tokens,
    )

    st.session_state.messages.append({"role": "user", "content": cleaned_prompt})
    started_at = time.perf_counter()
    try:
        with st.spinner("Routing through SabiPass AI"):
            response_data = post_neural_chat(api_url=api_url, payload=payload)
    except requests.RequestException as exc:
        response_data = {
            "tutor_conversational_text": (
                "The API request did not complete. Check that the FastAPI service is running "
                "and that the endpoint URL is correct."
            ),
            "response_type": "text_only",
            "system_metadata": {
                "pipeline_status": "request_failed",
                "rag_mode": "none",
                "llm_status": type(exc).__name__,
                "source_tags": [],
            },
            "error": str(exc),
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


def _render_sample_prompts(st: Any, *, api_url: str, tier: str, efficiency_mode: bool) -> None:
    samples = (
        ("Linear equation", DEFAULT_STUDENT_PROMPT),
        ("Quadratic roots", ROUTING_CHECK_PROMPT),
        ("Pidgin surds", "Abeg show me how to simplify sqrt(50) without calculator."),
    )
    columns = st.columns(len(samples))
    for column, (label, prompt) in zip(columns, samples):
        with column:
            if st.button(label, use_container_width=True):
                _submit_prompt(
                    st,
                    api_url=api_url,
                    tier=tier,
                    efficiency_mode=efficiency_mode,
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

    api_url, tier, efficiency_mode = _render_sidebar(st)
    _render_hero(st)
    _render_sample_prompts(st, api_url=api_url, tier=tier, efficiency_mode=efficiency_mode)
    _render_chat_history(st)

    prompt = st.chat_input("Ask a WAEC or JAMB maths question")
    if prompt:
        _submit_prompt(
            st,
            api_url=api_url,
            tier=tier,
            efficiency_mode=efficiency_mode,
            prompt=prompt,
        )
        _rerun(st)


if __name__ == "__main__":
    run_app()
