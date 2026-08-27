"""
Fitness Intelligence Narrative View: "What is happening to my fitness?"
"""
from typing import List
import streamlit as st

from src.models.metrics import FitnessInsight
from src.ui.components import render_insight_card


def render_insights_view(insights: List[FitnessInsight]) -> None:
    st.markdown("## 🧠 What is Happening to My Fitness?")
    st.caption("Data-driven narrative intelligence that explains physiological adaptations, workload trajectories, and recovery needs.")

    if not insights:
        st.info("No training insights available. Import activity history to generate physiological narratives.")
        return

    # Filter by category if user wants
    categories = ["All Categories"] + sorted(list(set(i.category.title() for i in insights)))
    selected_cat = st.selectbox("Filter Insights by Category", categories, index=0)

    filtered_insights = insights
    if selected_cat != "All Categories":
        filtered_insights = [i for i in insights if i.category.title() == selected_cat]

    for insight in filtered_insights:
        render_insight_card(insight)
