"""AI Copilot: conversational analytics over verified calculations."""
from __future__ import annotations

import streamlit as st

from .. import ai_copilot as ai
from ..components import tables
from ..components.sidebar import filter_bar
from ..components.styling import page_header


@st.cache_resource(show_spinner=False)
def _llm():
    return ai.make_groq_llm()


def _queue(question: str) -> None:
    st.session_state["pending_q"] = question


def _render_answer(a: ai.CopilotAnswer) -> None:
    badge = {"AI explanation": "nx-badge", "Demo mode": "nx-badge muted", "Verified fallback": "nx-badge warn"}.get(a.mode, "nx-badge muted")
    st.markdown(f'<span class="{badge}">{a.mode}</span> <span class="nx-badge muted">{a.intent_label}</span>', unsafe_allow_html=True)
    st.markdown(a.answer)
    for n in a.notes:
        st.caption(n)
    if a.facts or a.tables:
        with st.expander("Supporting evidence"):
            if a.tables:
                for name, t in a.tables.items():
                    st.markdown(f"**{name}**")
                    tables.show(t.head(25))
            if a.facts:
                st.markdown("**Verified figures passed to the explanation**")
                st.json(a.facts, expanded=False)
    st.markdown(f'<div class="nx-scope">Data used: {a.scope}</div>', unsafe_allow_html=True)


def render(df_all) -> None:
    page_header("AI Copilot", "Ask about your profit. Every number comes from a calculation, not from the model.")
    f = filter_bar(df_all, "cp")
    history = st.session_state.setdefault("copilot_history", [])
    llm = _llm()

    prompt = st.chat_input("Ask about profit, discounts, products, regions or customers...", key="cp_input")
    question = prompt or st.session_state.pop("pending_q", None)
    if question:
        try:
            with st.spinner("Calculating..."):
                answer = ai.answer_question(question, f.df, f.scope, llm)
            history.append(answer)
        except ValueError as exc:
            st.warning(str(exc))

    if not history:
        st.markdown('<div class="nx-hero"><h2>What would you like to know?</h2>'
                    '<p>Pick a question to start, or type your own below.</p></div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, q in enumerate(ai.SUGGESTED_QUESTIONS):
            cols[i % 2].button(q, key=f"sq_{i}", width="stretch", on_click=_queue, args=(q,))
    else:
        for a in history:
            with st.chat_message("user"):
                st.write(a.question)
            with st.chat_message("assistant"):
                _render_answer(a)
        with st.expander("Suggested questions"):
            cols = st.columns(2)
            for i, q in enumerate(ai.SUGGESTED_QUESTIONS):
                cols[i % 2].button(q, key=f"sqh_{i}", width="stretch", on_click=_queue, args=(q,))
        st.button("Clear conversation", key="cp_clear", on_click=lambda: st.session_state.update(copilot_history=[]))
    if llm is None:
        st.caption("Demo mode: answers use deterministic calculations. Add GROQ_API_KEY to .env for AI-written explanations.")
