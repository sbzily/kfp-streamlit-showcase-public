import streamlit as st


def apply_base_style() -> None:
    st.markdown(
        """
        <style>
        * { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
        .stApp {
            background: radial-gradient(circle at top, #f8fbff 0%, #f3f6fb 55%, #edf1f7 100%);
        }
        .block-container { max-width: 1280px; padding-top: 2.5rem; }
        h1 { letter-spacing: -0.02em; }
        .stage-card { border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; color: #0b1f44; }
        details summary { font-size: 1.02rem; }
        .detail-block p { margin-bottom: 0.6rem; }
        .stage-card p { margin: 0.45rem 0; }
        div[data-testid="stGraphViz"] { overflow: visible; }
        div[data-testid="stGraphViz"] svg {
            width: 100% !important;
            height: auto !important;
            max-width: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
