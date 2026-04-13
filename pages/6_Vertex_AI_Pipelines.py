import streamlit as st
from src.utils.layout import apply_base_style

ANNOTATED_COMPONENTS_FILE = """
import os
from kfp import dsl

BASE_IMAGE = os.environ.get(
    "PIPELINE_COMPONENT_IMAGE",
    "us-docker.pkg.dev/shared-data-platform/pipelines/daily-orders:latest",
)
# Every component below runs inside this image.
# Build & Release injects the exact SHA-tagged image when the pipeline is compiled.


@dsl.component(base_image=BASE_IMAGE)
def extract_orders(project_id: str, config_uri: str) -> str:
    # @dsl.component tells KFP/Vertex: treat this Python function as one pipeline step.
    # base_image says which container Vertex should start for that step.
    print(f"Loading config from {config_uri}")
    print(f"Extracting raw orders in {project_id}")
    return "gs://vertex-pipelines-dev/tmp/orders_delta.parquet"
    # The return value becomes an output that later steps can depend on.


@dsl.component(base_image=BASE_IMAGE)
def run_sql(config_uri: str, sql_path: str, upstream_ref: str = "") -> str:
    # config_uri is just the full GCS address of the uploaded config file.
    # sql_path is the full GCS address of the SQL file this step should execute.
    print(f"Running {sql_path} with params from {config_uri}")
    if upstream_ref:
        # Downstream steps can wait for the earlier step and use its output.
        print(f"Waiting for upstream ref: {upstream_ref}")
    return "bq://analytics.fct_orders"
    # In a real pipeline this would usually point at the table or artifact produced.
"""

EXECUTION_FLOW = """
extract_orders(...)
run_sql(..., "staging/orders_delta.sql")
run_sql(..., "staging/order_items_delta.sql")
run_sql(..., "intermediate/order_lines_enriched.sql")
run_sql(..., "intermediate/customer_order_day.sql")
run_sql(..., "marts/fct_orders.sql")
"""

st.set_page_config(
    page_title='Vertex AI Pipelines | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Vertex AI Pipelines')
st.caption('Chapter 5: this is the code Vertex turns into managed pipeline steps')
st.write(
    'This page is really about the `components/components.py` file. '
    'It is where plain Python functions get declared as pipeline steps that Vertex can run.'
)
st.write(
    'The key mental model: Vertex is not reading raw SQL files directly from GitHub. '
    'It runs component steps defined in Python, and those steps are told which config file and SQL file to use at runtime.'
)

st.write(
    'This file defines the executable steps of the pipeline. Each function decorated with `@dsl.component` becomes one step that Vertex will run. '
    'When Vertex executes your pipeline, it needs to know three things: which Docker container image to use, what inputs each step requires, and what outputs each step produces. '
    'The step parameters point directly at the config file and SQL files that were previously uploaded to GCS [from the earlier release steps]. '
    'This is the crucial layer where your Python code in the repo transitions into actual managed pipeline execution in Vertex.'
)

st.subheader('Annotated `components/components.py` example')
st.code(ANNOTATED_COMPONENTS_FILE.strip(), language='python')

st.markdown(
    """
**Turning Python functions into pipeline steps:** The `@dsl.component` decorator [from KFP's domain-specific language module, it marks this function as a containerized component that Vertex can execute as an isolated pipeline step] tells KFP [Kubeflow Pipelines] and Vertex to treat your regular Python function as a reusable pipeline step. Without this decorator, it's just a normal function. With it, Vertex knows to run it in a managed environment.

**Specifying which container image to use:** The `base_image=BASE_IMAGE` parameter tells Vertex which Docker container image to start when running this step. This is where the image built in the Build & Release step comes full circle. The Build & Release process injects the exact SHA-tagged image into the components file during compilation, so every pipeline run uses the exact same versioned image.

**Passing configuration at runtime:** The `config_uri` parameter is the GCS address pointing to the environment-specific config file that was uploaded earlier. The `sql_path` parameter points to the specific SQL file in the uploaded SQL bundle. Instead of hardcoding these paths into your component code, they're passed as arguments, which means the same component code can run different SQL files and use different configurations depending on what parameters Vertex passes to it.

**Building dependencies between steps:** The return value from one component becomes an output that later components can depend on. This creates the directed acyclic graph [DAG, the workflow structure that tells Vertex which steps must run before others and which can run in parallel]. When one step returns a value and another step uses that value as input, Vertex automatically knows to run the first step before the second one, and it passes the result from step one to step two.
"""
)

st.subheader('How the pipeline uses these components')
st.write(
    'The pipeline file wires these same component functions together in order. For `daily_orders`, '
    'it calls `extract_orders` once and then reuses `run_sql` for each SQL stage in the ETL.'
)
st.code(EXECUTION_FLOW.strip(), language='text')

st.info(
    '**Story checkpoint: Your pipeline is now running as a managed workflow on Vertex AI.** '
    'Vertex takes your compiled KFP template and executes each component step in the order defined by your directed acyclic graph. '
    'Each component runs inside a container started from the Docker image built in the release process. '
    'Vertex passes your GCS paths (configuration and SQL files) to each step as parameters, so every component knows exactly which config to use and which SQL to run. '
    'Vertex handles scheduling, logging, retries, and monitoring automatically. '
    'If a step fails, Vertex captures the error logs. If a step takes too long, it stores that information. '
    'Your data processing is no longer a script running on your laptop or a Cron job on a random server; it is a managed pipeline with visibility and control.'
)
st.success(
    '**Next: Monitoring & Alerting (Chapter 6).** '
    'Now that your pipeline is running, you need to know when something goes wrong and what to do about it. '
    'The next chapter shows how to set up alerts that watch both the pipeline infrastructure (did it fail, is it slow) and the data quality of what it produces (is the data stale, are row counts suspiciously low). '
    'You will learn how to define runbooks that guide your team to quick recovery when alerts fire.'
)
