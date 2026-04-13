import streamlit as st
from src.utils.layout import apply_base_style

ANNOTATED_DOCKERFILE = """
FROM python:3.11-slim  # Start from a small Python base image.

WORKDIR /app  # Set the working directory inside the container.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # Install runtime dependencies into the image.

COPY build ./build  # Include deploy/pipeline code needed by imports.
COPY components ./components  # Include the KFP component implementations.

ENV PYTHONPATH=/app  # Make build.* and components.* importable.
ENV PYTHONUNBUFFERED=1  # Stream logs immediately instead of buffering them.
"""

st.set_page_config(
    page_title='Docker Images | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Docker Images (Artifact Registry)')
st.caption('Chapter 2: understand the runtime image and why it matters')

# Explanation for data engineers unfamiliar with Docker
st.info(
    '**What is a Docker Image?** '
    'A Docker image is a lightweight, self-contained package that bundles your code, Python libraries, system dependencies, '
    'and configuration into a single unit. Think of it like a snapshot of your entire runtime environment. '
    'When Vertex AI Pipelines runs a step, it starts a container from this image—guaranteeing that the exact same code and dependencies '
    'run every time, regardless of where the pipeline executes. This ensures **reproducibility**: the same image tag always produces identical behavior.'
)

st.write(
    'Once Cloud Build finishes, the daily_orders runtime image lives in Artifact Registry. '
    'That image tag is what keeps runs reproducible: same tag, same code, same dependencies.'
)

st.subheader('Annotated `Dockerfile` example')
st.code(ANNOTATED_DOCKERFILE.strip(), language='dockerfile')
st.markdown(
    """
**Key concepts:**

**Dockerfile vs. pipeline definition:** The Dockerfile defines what goes *inside* the container (code, libraries, environment) and runs during the build phase. This is separate from the pipeline definition [the orchestration file that tells Vertex AI which steps to run and in what order]. Think of it this way: the Dockerfile is like packing a lunch box with specific ingredients, while the pipeline is the schedule that says when to eat lunch.

**Package versions are locked in the image:** When you run `RUN pip install -r requirements.txt` in the Dockerfile, all package versions are downloaded and installed at build time and become part of the final image. Every run using that image tag gets the exact same package versions, so you won't encounter unexpected version differences.

**Your code gets bundled into the image:** The `COPY build` and `COPY components` lines take your application code and bundle it into the container. When Vertex AI Pipelines runs a step, it pulls this image (which already contains your code) and executes it. You don't need to fetch your code from elsewhere during the run.

**Separation of concerns:** Artifact Registry stores the built images, which are read-only artifacts. When Vertex AI Pipeline workers run, they only need the ability to *pull* (download) the image. They don't need permission to build or modify it, which is a security best practice since the workers can't accidentally rebuild or corrupt the image.
"""
)

st.info(
    '**Story checkpoint: You now understand the Docker image and why it matters for reproducibility.** '
    'The Docker image is a complete snapshot of your runtime environment: your Python libraries, your application code (in the `build/` and `components/` folders), and your operating system configuration. '
    'When you tag the image with a git commit SHA and store it in Artifact Registry, that tag becomes a promise: '
    'any pipeline run using that image tag will execute with the exact same packages, the exact same code, and the exact same dependencies. '
    'If daily_orders produces different results on different days, checking the image tag is one of the first troubleshooting steps.'
)
st.success(
    '**Next: Build & Release (Chapter 3).** '
    'Now that you understand what goes inside the Docker image, the next chapter shows how Cloud Build automates the building of this image. '
    'Cloud Build will compile your pipeline, build the Docker image, and publish everything with a commit-based version tag. '
    'This automation ensures that every merge becomes a new release that Vertex can later execute.'
)
