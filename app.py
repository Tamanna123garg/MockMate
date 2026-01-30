import json
import os
import time

import pandas as pd
import streamlit as st

from evaluator import evaluate_answer
from questions import questions

THEME_CSS = """
<style>
    :root {
        --bg: #999999;
        --card: #ffffff;
        --accent: #1f7a8c;
        --accent-strong: #16697a;
        --text: #0f172a;
    }

    .stApp { background-color: var(--bg); color: var(--text); }
    h1, h2, h3 { color: var(--text); }

    .stButton > button {
        background-color: var(--accent);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.25rem;
    }
    .stButton > button:hover { background-color: var(--accent-strong); }

    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background-color: var(--card);
        border-radius: 8px;
        border: 1px solid #d7dde7;
        color: #000000;
    }

    textarea { color: #ffffff !important; }

    [data-testid="stAlert"] {
        border-radius: 10px;
        background-color: var(--card);
        border-left: 4px solid var(--accent);
        color: var(--text);
    }
    [data-testid="stAlert"] p { color: var(--text); }

    /* Hide Streamlit's toolbar (Stop/Deploy) */
    [data-testid="stToolbar"] { display: none !important; }
</style>
"""

TOTAL_TIME = 600
PROGRESS_FILE = "progress.json"


def init_state() -> None:
    defaults = {
        "started": False,
        "submitted": False,
        "total_score": 0,
        "progress_data": [],
        "name": "",
        "domain": "",
        "start_time": None,
        "last_results": {},
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)


def load_progress(path: str) -> list:
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
    try:
        with open(path, "r") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except json.JSONDecodeError:
        return []


def save_progress(path: str, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def show_history(progress_data: list, name: str) -> None:
    if not name:
        return
    df = pd.DataFrame(progress_data)
    if df.empty:
        return
    user_hist = df[df["name"] == name]
    if user_hist.empty:
        return
    st.subheader("Previous Performance")
    st.dataframe(user_hist.sort_values("date", ascending=False).head(5))


def render_questions(domain: str, domain_questions: dict) -> list:
    levels = ["Easy", "Medium"]
    collected = []
    q_counter = 1
    for level in levels:
        for idx, q in enumerate(domain_questions.get(level, [])):
            st.markdown(f"*Q{q_counter}: {level}*")
            key = f"{domain}{level}{idx}"
            collected.append((q, st.text_area(q, key=key, height=150)))
            q_counter += 1
    return collected


def show_results() -> None:
    res = st.session_state.get("last_results", {})
    if not res:
        return

    st.write("### Feedback per Question")
    for entry in res.get("feedback_entries", []):
        st.write(f"*Q:* {entry['question']}")
        st.write(f"*Score:* {entry['score']}/10")
        st.write(f"*Feedback:* {entry['feedback']}")
        st.write("---")

    st.success(f"Total Score: {res.get('total', 0)}/{res.get('total_q', 0) * 10}")

    weak_topics = res.get("weak_topics", [])
    if weak_topics:
        st.warning("Recommended Topics to Revise")
        for t in weak_topics:
            st.write("- ", t)

    df = pd.DataFrame(st.session_state.progress_data)
    user_df = df[df["name"] == st.session_state.name]
    if not user_df.empty:
        st.subheader("Your Performance Over Time")
        st.line_chart(user_df.set_index("date")["score"])

    if st.button("Home Page"):
        st.session_state.update(
            started=False,
            submitted=False,
            start_time=None,
            last_results={},
        )
        st.rerun()


st.set_page_config(page_title="MockMate", layout="centered")
st.markdown(THEME_CSS, unsafe_allow_html=True)
st.title("MockMate - Mock Interview Platform")

init_state()

st.session_state.progress_data = load_progress(PROGRESS_FILE)

name = st.text_input("Enter your name", value=st.session_state.get("name", ""))
domain = st.selectbox("Choose Interview Domain", list(questions.keys()))
st.session_state.update(name=name, domain=domain)

if st.button("Start Mock Interview") and name:
    st.session_state.update(
        started=True,
        submitted=False,
        last_results={},
        total_score=0,
        start_time=time.time(),
    )
    for key in list(st.session_state.keys()):
        if key.startswith(f"{domain}_"):
            del st.session_state[key]

if not st.session_state.started and not st.session_state.submitted:
    show_history(st.session_state.progress_data, name)

if st.session_state.started:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(TOTAL_TIME - elapsed)

    if remaining <= 0:
        st.error("Interview Time Over! Auto-submitting answers")
        st.session_state.started = False
        st.rerun()

    minutes, seconds = divmod(remaining, 60)
    st.warning(f"Time Left: {minutes}:{seconds:02d}")

    st.subheader(f"Domain: {domain}")
    domain_questions = questions[domain]
    total_q = sum(len(v) for v in domain_questions.values())
    st.info(f"Found {total_q} questions in {domain}")

    collected_q_and_ans = render_questions(domain, domain_questions)

    if st.button("Submit Answers"):
        total = 0
        weak_topics = []
        feedback_entries = []

        for q, ans in collected_q_and_ans:
            if ans.strip():
                score, feedback, suggestions = evaluate_answer(ans)
                total += score
                feedback_entries.append({"question": q, "score": score, "feedback": feedback, "answered": True})
                if suggestions:
                    weak_topics.extend(suggestions)
            else:
                feedback_entries.append({"question": q, "score": 0, "feedback": "No answer provided", "answered": False})

        progress_data = st.session_state.progress_data.copy()
        progress_data.append(
            {
                "name": name,
                "domain": domain,
                "score": total,
                "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        save_progress(PROGRESS_FILE, progress_data)

        st.session_state.update(
            progress_data=progress_data,
            started=False,
            submitted=True,
            last_results={
                "feedback_entries": feedback_entries,
                "weak_topics": sorted(set(weak_topics)),
                "total": total,
                "total_q": total_q,
            },
        )
        st.rerun()

    if st.session_state.started and not st.session_state.submitted:
        time.sleep(1)
        st.rerun()

if st.session_state.get("submitted") and st.session_state.get("last_results"):
    show_results()

st.markdown("---")
st.markdown("Built for interview preparation with AI-powered feedback")