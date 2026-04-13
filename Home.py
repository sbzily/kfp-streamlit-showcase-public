import streamlit as st
from src.utils.layout import apply_base_style
from src.viz.diagrams import build_architecture_diagram

st.set_page_config(
    page_title='Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Vertex AI Pipelines for Data Engineering')
st.caption('A walkthrough of a production grade Data Engineering Pipeline on Vertex AI')
st.write(
    'Vertex AI can feel unfamiliar to data engineers because it is made for machine learning pipelines, '
    'but a lot of the core principles are the same as those found in traditional data engineering workflows. Under the Vertex AI hood, it is Kuberenetes Kubeflow Pipelines (KFP): '
    'a DAG of containerized steps compiled into a template and executed by a managed control plane on Google Cloud.'
)
st.write(
    'This walkthrough is built to connect the dots for those used to ETL deployment and are looking to adopting Vertex AI Pipelines in production by going through the pipeline of a daily_orders table for a fictional video streaming service: PrimeFlix+'
)
st.write(
    'You are a data engineer serving the data science arm of PrimeFlix+ and therefore have VertexAI as the main framework for production ML pipelines.'
    'You are tasked with building the daily_orders pipeline, which ingests order data from the transactional database, transforms it, and publishes it to daily_orders every morning before business starts.'
    'We start from the repo setup in GitHub, then follow that change through build, artifact storage, pipeline runs, scheduling, and alerts.'
)


st.divider()

st.subheader('Architecture Overview')
st.write(
    'Here is an end-to-end workflow on Vertex AI Pipelines. Under the diagram, each stage expands with a brief overview of what happens in that step. '
    'Use the sidebar to jump between stages and learn more details about each part of the workflow.'
)

st.graphviz_chart(build_architecture_diagram(), use_container_width=True)

st.caption('If you want the extra plain-English Cloud Build and Docker primer, open the `More` page from the sidebar.')

st.subheader('Stage Summaries')

stages = [
    {
        'title': 'GitHub',
        'color': '#e8f5e9',
        'content': 'Your GitHub repo serves as the single source of truth for the entire pipeline. It contains everything needed to build and run daily_orders: the Dockerfile that defines your runtime environment, deployment scripts in `build/`, the pipeline definition in `components/`, environment-specific configuration in `config/`, your SQL transformations in `sql/`, and even your monitoring definitions. When code is merged, the commit SHA becomes the version tag used to track all the artifacts created from that release, making it easy to audit and reproduce any run.',
    },
    {
        'title': 'Build & Release (Cloud Build)',
        'color': '#e3f2fd',
        'content': 'Cloud Build is the automated release engine that runs whenever code is merged. It reads `build/cloudbuild.yaml` and executes the steps in order. First, it builds your Docker image from the Dockerfile in the repo, tags it with the commit SHA, and pushes it to Artifact Registry so Vertex can access it later. Then it compiles your KFP pipeline definition into a YAML template that Vertex understands. Finally, it uploads your environment-specific configuration and your entire SQL folder to Google Cloud Storage with the same version tag. This entire process is automatic and repeatable, meaning every merge becomes a new versioned release in seconds.',
    },
    {
        'title': 'Docker Images (Artifact Registry)',
        'color': '#e0f7fa',
        'content': 'The Docker image built during the release process is stored in Artifact Registry and tagged with the commit SHA. This image contains everything your pipeline steps need to run: your Python libraries, system dependencies, your application code, and your configuration. By pinning specific image versions, you ensure that a pipeline run on Monday uses identical code and dependencies as a pipeline run on Friday. The image tag becomes a guarantee of reproducibility. Keeping the image separate from the deployment also means Vertex workers only need permission to pull the image, not to build or modify it, which is better for security.',
    },
    {
        'title': 'GCS (Artifacts & Templates)',
        'color': '#fff8e1',
        'content': 'After Cloud Build finishes, your compiled pipeline template, environment configuration, and SQL artifacts are stored in Google Cloud Storage. These files live at paths that include the commit SHA, which makes it easy to roll back to an older version if something goes wrong. When you need to rerun yesterday\'s data, you can use the config and SQL from that day\'s release. This separation of artifacts makes debugging straightforward because if a run produces unexpected results, you can inspect the exact template, config, and SQL that was used. Everything is immutable and versioned, so nothing surprises you at runtime.',
    },
    {
        'title': 'Vertex AI Pipelines',
        'color': '#ede7f6',
        'content': 'Vertex AI Pipelines is the managed orchestration service that executes your data pipeline. The key is to understand `components/components.py`, which defines your pipeline steps as Python functions decorated with `@dsl.component`. Each component runs inside the Docker image built in the release process and receives parameters pointing to the config and SQL files uploaded to GCS. Vertex manages the scheduling, execution, logging, and retries automatically, so you do not have to run jobs manually or maintain servers. The pipeline definition wires these components together in the order they need to run, creating a workflow where later steps depend on earlier steps, and Vertex handles all of that orchestration.',
    },
    {
        'title': 'Monitoring & Alerting',
        'color': '#f3e5f5',
        'content': 'Coming Soon!'
        #'content': 'Once your pipeline is running in production, you need to know when something goes wrong. The suggested approach is to define alerts in a `monitoring/alerts.yaml` file that covers both pipeline health (did it fail, is it running slow) and data health (is the output table stale, are there suspiciously few rows). Each alert includes severity levels, notification routing, and a link to a runbook that explains how to respond. By keeping this configuration in your repo like any other code, monitoring thresholds become reviewable and versioned. When an alert fires, responders have documented procedures to follow instead of guessing, which makes recovery faster and more predictable.',
    },
    {
        'title': 'Conclusion',
        'color': '#edeff3',
        'content': 'The complete model ties together GitHub (source of truth), Cloud Build (automated release), Artifact Registry (runtime images), GCS (runtime files), Vertex AI Pipelines (execution), and Monitoring (operations). Each layer has a specific job, and understanding what that job is makes the entire system much easier to reason about and explain to other engineers. The goal is not to memorise Google Cloud products, but to see how they fit together to create a reliable, reproducible, traceable data platform. Once that mental model clicks, you can extend and adapt this pattern to your own pipelines.',
    },
]

col_left, col_right = st.columns(2)
for idx, stage in enumerate(stages):
    col = col_left if idx % 2 == 0 else col_right
    col.markdown(
        f"""
        <details style="background:{stage['color']}; padding: 12px; border-radius: 8px; margin-bottom: 12px;" class="stage-card">
            <summary style="font-weight:700; cursor:pointer; font-size: 1.1em;">{stage['title']}</summary>
            <div style="margin-top:12px; line-height:1.6;">{stage['content']}</div>
        </details>
        """,
        unsafe_allow_html=True,
    )
