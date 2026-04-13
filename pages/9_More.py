import streamlit as st
from src.utils.layout import apply_base_style
from src.viz.diagrams import build_docker_flow_diagram

ANNOTATED_CLOUDBUILD_YAML = """
steps:
  # 1) Build the exact container image that Vertex components will run later.
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"  # Tag the image with the git commit SHA.
      - "."  # Use the repo root as the Docker build context, so Docker reads ./Dockerfile.

  # 2) Push the image so Vertex can pull the same immutable tag at runtime.
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "push"
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"

  # 3) Compile the KFP pipeline and inject the image tag built above.
  - name: "python:3.11"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        pip install -r requirements.txt
        export PIPELINE_COMPONENT_IMAGE=us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA
        python build/deploy_vx_pipeline.py --env=${_ENV}

  # 4) Optionally refresh the recurring trigger for this environment.
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        gcloud scheduler jobs update http daily-orders-${_ENV} \
          --location=us-central1 \
          --schedule="0 3 * * *"
"""

ANNOTATED_DOCKERFILE = """
FROM python:3.11-slim  # Start from a small Python base image.

WORKDIR /app  # All following COPY/RUN commands happen inside /app.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # Bake Python dependencies into the image.

COPY build ./build  # Include deploy and pipeline wiring code.
COPY components ./components  # Include the KFP component implementations.

ENV PYTHONPATH=/app  # Let Python import build.* and components.* directly.
ENV PYTHONUNBUFFERED=1  # Stream logs immediately to Cloud Logging and Vertex logs.
"""

st.set_page_config(
    page_title='Glossary & More Help | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Glossary & More Help')
st.caption('Extra plain-English explainers for Cloud Build and Docker')
st.write(
    'This page holds the extra primer content that supports the main walkthrough but is not essential to the story flow. '
    'If you want a slower, simpler explanation of Cloud Build and Docker, start here.'
)

st.subheader('Cloud Build and Docker, In Plain English')
st.info(
    'Cloud Build does not run the data pipeline itself. It reads `cloudbuild.yaml`, executes those build/release steps in order, '
    'and produces versioned artifacts that Vertex runs later.'
)

primer_left, primer_right = st.columns(2)
with primer_left:
    st.markdown('**What `cloudbuild.yaml` is**')
    st.write(
        'It is the release recipe. A trigger fires after a merge, Cloud Build opens this file, '
        'and each item in `steps:` becomes one command block in the managed build job.'
    )

with primer_right:
    st.markdown('**What `Dockerfile` is**')
    st.write(
        'It is the runtime recipe. Docker reads it to build the container image that your KFP components '
        'will actually run inside when Vertex executes the pipeline.'
    )

build_tab, docker_tab, outputs_tab = st.tabs(
    ['Annotated cloudbuild.yaml', 'Annotated Dockerfile', 'What the build produces']
)

with build_tab:
    st.write(
        'This file is the ordered list of release actions: build image, push image, compile the pipeline, '
        'and optionally refresh the recurring trigger.'
    )
    st.code(ANNOTATED_CLOUDBUILD_YAML.strip(), language='yaml')
    st.markdown(
        """
- `steps` is the sequence Cloud Build runs from top to bottom.
- `docker build` uses the repo's `Dockerfile` to create the runtime image.
- `$SHORT_SHA` makes the image and release traceable to one commit.
- `PIPELINE_COMPONENT_IMAGE` connects the built image to the compiled Vertex template.
- `deploy_vx_pipeline.py` is where template/config/SQL publishing happens.
"""
    )

with docker_tab:
    st.write(
        'This file explains what goes inside the runtime image. If a component imports code or needs Python packages, '
        'the Dockerfile is where that environment gets defined.'
    )
    st.code(ANNOTATED_DOCKERFILE.strip(), language='dockerfile')
    st.markdown(
        """
- `FROM` chooses the starting operating system and Python runtime.
- `RUN pip install ...` freezes dependencies into the image before release.
- `COPY build` and `COPY components` package your pipeline code into the container.
- The resulting image is what Artifact Registry stores and Vertex later pulls.
"""
    )

with outputs_tab:
    st.write(
        'One successful build should leave you with a complete, versioned release package rather than a single file.'
    )
    st.graphviz_chart(build_docker_flow_diagram(), use_container_width=True)
    output_cols = st.columns(4)
    output_cols[0].markdown('**Image**\n\nA SHA-tagged container in Artifact Registry.')
    output_cols[1].markdown('**Template**\n\nA compiled pipeline YAML in GCS.')
    output_cols[2].markdown('**Config**\n\nAn environment config file uploaded with the same version.')
    output_cols[3].markdown('**SQL**\n\nA SQL bundle uploaded so the run uses the reviewed logic.')

st.divider()

st.subheader('Jargon Buster: Key Terms Explained')
st.write(
    'This guide uses several terms from the data engineering and cloud computing world. '
    'Here is a plain-English explanation of the most important ones.'
)

cols = st.columns(2)

with cols[0]:
    st.markdown('**Container / Docker Container**')
    st.write(
        'A lightweight, self-contained environment that packages your code, libraries, and operating system configuration. '
        'Think of it like a virtual machine, but much smaller and faster to start. '
        'When Vertex runs a pipeline step, it starts a container from your image and executes your code inside it.'
    )
    
    st.markdown('**Docker Image**')
    st.write(
        'A blueprint or template for creating containers. An image contains all the files, dependencies, and configuration needed to run your code. '
        'Once you build an image, you can create many containers from it, and each one will have the exact same environment.'
    )
    
    st.markdown('**Artifact Registry**')
    st.write(
        'Google Cloud\'s storage service for container images. '
        'After Cloud Build builds your Docker image, it pushes it to Artifact Registry so that Vertex can later pull and run it. '
        'Think of it like a library where all your versioned images live.'
    )
    
    st.markdown('**GCS (Google Cloud Storage)**')
    st.write(
        'Google Cloud\'s object storage service, similar to Amazon S3. '
        'It stores files and data in the cloud. In this pipeline, it holds your compiled pipeline template, configuration files, and SQL scripts.'
    )
    
    st.markdown('**Cloud Build**')
    st.write(
        'A Google Cloud service that automatically builds, tests, and deploys code. '
        'You give it a `cloudbuild.yaml` file with instructions, and it runs those steps whenever a trigger fires (like after a merge to your repo).'
    )

with cols[1]:
    st.markdown('**KFP (Kubeflow Pipelines)**')
    st.write(
        'An open-source framework for defining data pipelines as Python components. '
        'You write Python functions decorated with `@dsl.component`, and KFP turns them into pipeline steps that can run in Kubernetes or on Vertex AI.'
    )
    
    st.markdown('**DAG (Directed Acyclic Graph)**')
    st.write(
        'A workflow structure that shows which steps must run before others. '
        'In a DAG, arrows point from earlier steps to later steps, and there are no loops or circular dependencies. '
        'This tells the orchestrator (Vertex) the order in which to run your steps.'
    )
    
    st.markdown('**Vertex AI Pipelines**')
    st.write(
        'Google Cloud\'s managed service for running data pipelines. '
        'You give it a compiled KFP pipeline template and configuration, and it handles scheduling, monitoring, logging, and retries. '
        'You do not need to manage servers or infrastructure.'
    )
    
    st.markdown('**Component**')
    st.write(
        'A single step in your pipeline. In KFP, a component is a Python function decorated with `@dsl.component`. '
        'When Vertex runs your pipeline, it executes each component in the order defined by your DAG.'
    )
    
    st.markdown('**Runbook**')
    st.write(
        'A documented procedure that describes how to respond to and recover from a specific problem. '
        'When an alert fires, the runbook tells the on-call engineer what to check first, what common causes are, and what steps to take to fix it.'
    )
    
    st.markdown('**SHA / Commit SHA**')
    st.write(
        'A unique identifier for a specific version of your code. Every commit to Git gets a SHA (a long string of letters and numbers), '
        'and you can use it to tag your images and release artifacts so they are always traceable back to that exact code.'
    )

st.divider()

st.info(
    '**Reference page checkpoint: You now have a complete glossary of terms used throughout this guide.** '
    'This page is meant to be revisited whenever you encounter unfamiliar terminology. '
    'Understanding these concepts is not just about knowing definitions, it is about thinking like a data engineer who works with managed cloud infrastructure. '
    'The terms here reflect the real challenges of production pipelines: reproducibility (Docker images, commit SHAs), '
    'workflow orchestration (DAGs, KFP, components), reliability (Vertex AI managing infrastructure), and operational readiness (runbooks, monitoring).'
)

st.success(
    '**Ready to go deeper?** '
    'Return to any of the main chapters (GitHub, Docker Images, Build & Release, GCS, Vertex AI Pipelines, or Monitoring & Alerting) '
    'to dive into the specific implementation details and code examples. '
    'This page is always here as your reference guide while you build your own production pipeline. '
    'When you\'re done, check out the **About** page to learn more about the author and the thinking behind this guide.'
)
