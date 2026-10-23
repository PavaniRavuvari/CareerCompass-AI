
import json
from itertools import groupby

import pandas as pd
import plotly.express as px
import streamlit as st

from core import db, gemini
from views.ui import ai_call, go, title


# Midnight Purple palette
PURPLE = "#7957E8"
PURPLE_DARK = "#201747"
PURPLE_MEDIUM = "#9679ED"
PURPLE_LIGHT = "#DCD0FF"
PURPLE_PALE = "#EEE8FF"
TEXT_MUTED = "#77728E"


def render(conn):
    # --------------------------------------------------
    # Page heading
    # --------------------------------------------------
    title(
        "🗺️ Learning Roadmap",
        "Generated from your skill gaps and weekly study hours. Progress is saved.",
    )

    # --------------------------------------------------
    # Load roadmap tasks
    # --------------------------------------------------
    tasks = db.roadmap(conn)

    if not tasks:
        st.info(
            "No roadmap yet. Build one from the Skill-Gap Analysis page."
        )
        st.button(
            "Go to Skill-Gap Analysis →",
            on_click=go,
            args=("🧩 Skill-Gap Analysis",),
            type="primary",
        )
        return

    # --------------------------------------------------
    # Calculate progress
    # --------------------------------------------------
    done = sum(bool(task["done"]) for task in tasks)
    total = len(tasks)
    weeks = max(task["week"] for task in tasks)

    col_career, col_duration, col_completed = st.columns(3)

    col_career.metric("Career", tasks[0]["career"])
    col_duration.metric("Duration", f"{weeks} weeks")
    col_completed.metric("Completed", f"{done}/{total}")

    st.progress(done / total)

    # --------------------------------------------------
    # Weekly study-hours chart — Midnight Purple
    # --------------------------------------------------
    df = pd.DataFrame(tasks)

    weekly = (
        df.groupby("week")
        .agg(
            hours=("hours", "sum"),
            done=("done", "mean"),
        )
        .reset_index()
    )

    weekly["done"] = (weekly["done"] * 100).round()

    figure = px.bar(
        weekly,
        x="week",
        y="hours",
        color="done",
        color_continuous_scale=[
            PURPLE_LIGHT,
            PURPLE_MEDIUM,
            PURPLE,
            PURPLE_DARK,
        ],
        range_color=[0, 100],
        labels={
            "done": "% done",
            "week": "Week",
            "hours": "Hours",
        },
        hover_data={
            "week": True,
            "hours": ":.1f",
            "done": ":.0f",
        },
    )

    figure.update_layout(
        height=300,
        margin=dict(t=20, b=35, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=PURPLE_DARK,
            family="Arial, sans-serif",
        ),
        xaxis=dict(
            title="Week",
            tickmode="linear",
            dtick=1,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Hours",
            gridcolor="#E6E0F3",
            zeroline=False,
        ),
        coloraxis_colorbar=dict(
            title="% done",
            tickfont=dict(color=TEXT_MUTED),
            title_font=dict(color=TEXT_MUTED),
        ),
    )

    figure.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "Week %{x}"
            "<br>Study hours: %{y}"
            "<br>Completed: %{marker.color:.0f}%"
            "<extra></extra>"
        ),
    )

    with st.container(border=True):
        st.markdown("### 📊 Weekly study plan")
        st.plotly_chart(
            figure,
            use_container_width=True,
            config={"displayModeBar": False},
            key="roadmap_weekly_chart",
        )

    # --------------------------------------------------
    # Weekly tasks and completion tracking
    # --------------------------------------------------
    st.markdown("## 📚 Your weekly learning tasks")

    for week, grouped_tasks in groupby(
        tasks,
        key=lambda task: task["week"],
    ):
        items = list(grouped_tasks)

        week_hours = sum(item["hours"] for item in items)
        week_done = sum(bool(item["done"]) for item in items)

        with st.expander(
            f"Week {week} · {week_hours:g} h · "
            f"{week_done}/{len(items)} done",
            expanded=(week == 1),
        ):
            for task in items:
                completed = st.checkbox(
                    f"**{task['title']}** ({task['hours']:g} h) "
                    f"— {task['detail']}",
                    value=bool(task["done"]),
                    key=f"task{task['id']}",
                )

                if completed != bool(task["done"]):
                    db.set_task_done(
                        conn,
                        task["id"],
                        completed,
                    )
                    st.rerun()

    # --------------------------------------------------
    # AI study tips
    # --------------------------------------------------
    st.markdown("## ✨ Personalized study guidance")

    if st.button(
        "✨ Get AI study tips for this roadmap",
        disabled=not gemini.available(),
        type="primary",
        use_container_width=True,
        key="roadmap_ai_tips",
    ):
        profile = db.load_profile(conn) or {}

        roadmap_summary = json.dumps(
            [
                {
                    key: task[key]
                    for key in ("week", "title", "hours", "done")
                }
                for task in tasks
            ]
        )

        prompt = (
            f"Roadmap tasks: {roadmap_summary}\n"
            f"Pace: {profile.get('pace')}, "
            f"hours/week: {profile.get('hours_per_week')}.\n"
            "Give milestone checkpoints, mini-project ideas per phase, "
            "and motivation tips. Keep under 250 words."
        )

        output = ai_call(
            gemini.generate,
            prompt,
            system=gemini.SYSTEM_COACH,
        )

        if output:
            with st.container(border=True):
                st.markdown("### 💜 Your AI study tips")
                st.markdown(output)

    # --------------------------------------------------
    # Export roadmap
    # --------------------------------------------------
    st.download_button(
        "⬇️ Export roadmap (CSV)",
        data=df.to_csv(index=False),
        file_name="roadmap.csv",
        mime="text/csv",
        key="export_roadmap_csv",
    )
