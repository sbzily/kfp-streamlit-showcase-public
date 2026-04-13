# Vertex AI Pipelines Explainer (Streamlit)

A Streamlit explainer site that visualizes **KFP-style** pipelines and documents how a production
Vertex AI Pipelines workflow is built, deployed, and operated.

## Live demo
Coming soon (Streamlit Community Cloud).

## What it shows
- Pipeline DAG visualizer with multiple patterns
- CI/CD flow and architecture diagrams with toggles
- Environment promotion, Docker, and ops explainers
- A simplified "pipeline spec" view (V0), ready to be replaced by real KFP compilation output later

## Screenshots
(Add 1–2 screenshots here once the UI stabilizes.)

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
