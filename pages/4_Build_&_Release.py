import streamlit as st
from src.utils.layout import apply_base_style

ANNOTATED_CLOUDBUILD_YAML = """
steps:
  # Step 1: Build the runtime image from the repo's Dockerfile.
  - name: "gcr.io/cloud-builders/docker"  # Use Google Cloud's Docker builder tool.
    args:
      - "build"  # Docker command to build an image.
      - "-t"  # Tag flag: assign a name/version to this image.
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"  # Full image path with project ID and commit-based tag.
      - "."  # Build context: "." means use the Dockerfile in the current directory.

  # Step 2: Push the image so Vertex can pull this exact version later.
  - name: "gcr.io/cloud-builders/docker"  # Use Docker builder again.
    args:
      - "push"  # Docker command to upload the image to Artifact Registry.
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"  # Push to the same location.

  # Step 3: Compile the pipeline and publish template/config for one environment.
  - name: "python:3.11"  # Use a Python 3.11 container as the build environment.
    entrypoint: "bash"  # Run bash (shell) commands instead of Python directly.
    args:
      - "-c"  # Execute the following commands as a shell script.
      - |
        pip install -r requirements.txt  # Install dependencies needed to run the compilation script.
        export PIPELINE_COMPONENT_IMAGE=us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA  # Pass the image tag to the Python script.
        python build/deploy_vx_pipeline.py --env=\${_ENV}  # Run the script that compiles and deploys the pipeline.

  # Step 4: Optionally refresh the recurring trigger to point at the new release.
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"  # Use Google Cloud CLI tools.
    entrypoint: "bash"  # Run bash commands.
    args:
      - "-c"  # Execute as a shell script.
      - |
        gcloud scheduler jobs update http daily-orders-\${_ENV} \\  # Update the scheduler job for this environment.
          --location=us-central1 \\  # Specify the region where the job runs.
          --schedule="0 3 * * *"  # Cron expression: run at 3 AM every day (adjust as needed).
"""

st.set_page_config(
    page_title='Build & Release | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Build & Release (Cloud Build)')
st.caption('Chapter 3: Cloud Build reads cloudbuild.yaml and turns repo code into release artifacts')
st.write(
    'In the daily_orders story, Cloud Build is the bridge between code review and execution. '
    'After a merge, it reads `build/cloudbuild.yaml`, runs those steps in order, builds the runtime image, compiles the pipeline, and publishes release artifacts.'
)
st.info(
    'The key mental model: Cloud Build is not where the data pipeline runs. It is the managed release job that prepares the versioned image, template, config, and SQL that Vertex will use later.'
)

st.subheader('Annotated `cloudbuild.yaml` example')
st.code(ANNOTATED_CLOUDBUILD_YAML.strip(), language='yaml')
st.markdown(
    """
**What happens in each step:**

**Build and push the runtime image:** Cloud Build runs `docker build` using the Dockerfile in your repo to create the container image. Once built, it immediately pushes that image to Artifact Registry [Google Cloud's container storage service] with a tag that includes the commit SHA [the unique identifier for this specific version of your code]. This tagging strategy ensures that every build is version-controlled and traceable.

**Compile the pipeline:** The third step runs `build/deploy_vx_pipeline.py`, which takes your pipeline definition from `build/pipeline.py` and compiles it into a Vertex AI template. The script injects the image tag from the previous step into the template so that when Vertex runs the pipeline, it uses the exact image built in this release.

**One commit, one release package:** The `$SHORT_SHA` (commit identifier) flows through the image tag, template, and all configuration artifacts. This means every pipeline run is traceable back to a specific commit, making it easy to debug if something goes wrong.

**Optional: update the scheduler:** The final step can update any recurring Cloud Scheduler jobs [automated triggers that run the pipeline on a schedule] to ensure they use the latest pipeline version, though this is optional depending on your deployment strategy.
"""
)


st.info(
    'Story checkpoint: after this stage, we have a versioned image in Artifact Registry plus a versioned template, config, and SQL bundle ready for deployment.'
)

st.info(
    '**Story checkpoint: Cloud Build has completed the release process.** '
    'Your Docker image has been built from the Dockerfile in your repo, tagged with the git commit SHA for traceability, and pushed to Artifact Registry where Vertex can pull it. '
    'Your pipeline definition has been compiled from the Python code into a YAML template that Vertex understands. '
    'Your environment-specific configuration file and the entire SQL folder have been uploaded to GCS with the same version tag. '
    'All three of these artifacts (image, template, and SQL) are immutable and versioned, meaning if a run produces unexpected results, you can always look up exactly which code and configuration created that run.'
)
st.success(
    '**Next: GCS (Chapter 4).** '
    'Your compiled pipeline template, environment configuration, and SQL queries have been uploaded to GCS. '
    'The next chapter explains how these runtime files are organized and versioned in cloud storage, and how Vertex reads them at runtime to execute your pipeline.'
)
