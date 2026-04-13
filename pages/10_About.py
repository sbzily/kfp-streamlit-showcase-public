import streamlit as st
from src.utils.layout import apply_base_style

st.set_page_config(
    page_title='About | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('About')

col1, col2 = st.columns([2, 1], gap='large')

with col1:
    st.markdown(
        """
**About the author**

My name is Muhammad, and I'm a full stack data scientist currently working at a major broadcaster. My focus is on building predictive models based on viewing behavior, which means I spend a lot of time thinking about how to architect reliable, reproducible data pipelines that feed ML systems.

**Background**

My academic journey started in pure chemistry, which might seem unrelated to data science, but it shaped how I approach problems. Chemistry is about understanding systems at scale, predicting outcomes based on underlying principles, and rigorously testing hypotheses. That mindset carries over to data work. My master's degree focused on the intersection between chemistry and data science/ML, where I explored how computational methods and machine learning can accelerate research and discovery.

**Why this guide exists**

Working in production data science means I build pipelines that need to be reproducible, traceable, and reliable. Whether you're building for a broadcaster, an e-commerce platform, or an internal data team, the principles are the same: organize your code, automate your releases, containerize your dependencies, and monitor your systems.

This guide is designed for data engineers and data scientists who are familiar with SQL, Python, and the general concepts of ETL, but may be new to managed cloud infrastructure like Vertex AI Pipelines. It's written to acknowledge that not everyone comes from a software engineering background, but everyone deserves to understand how their production systems work.

**Questions or feedback?**

If you find this guide helpful, have suggestions for improvements, or want to discuss data pipelines, predictive modeling, or anything at the intersection of ML and data engineering, reach out on LinkedIn. I'm always interested in learning how other teams solve these problems.
        """
    )

with col2:
    st.markdown('**Connect**')
    st.markdown(
        """
[Muhammad on LinkedIn](https://linkedin.com/in/muhammad-a-46402915a/)

*Full Stack Data Scientist*
        
        """
    )

st.divider()
