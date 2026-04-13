import streamlit as st
from src.utils.layout import apply_base_style

ANNOTATED_DEPLOY_FILE = """
from pathlib import Path
import yaml
from google.cloud import storage
from kfp import compiler

from build.pipeline import daily_orders_pipeline


def upload_file(client: storage.Client, local_path: str, gcs_uri: str) -> None:
    # Helper that copies one local file to one exact GCS path.
    bucket_name, blob_name = gcs_uri.replace("gs://", "", 1).split("/", 1)
    client.bucket(bucket_name).blob(blob_name).upload_from_filename(local_path)


def upload_sql_bundle(client: storage.Client, local_dir: str, gcs_prefix: str) -> None:
    # Upload every SQL file so Vertex can use the full reviewed ETL bundle at runtime.
    for path in Path(local_dir).rglob("*.sql"):
        rel_path = path.relative_to(local_dir).as_posix()
        upload_file(client, str(path), f"{gcs_prefix}/{rel_path}")


def deploy(env: str) -> None:
    # Load the user/environment config that tells us which bucket paths to publish to.
    cfg = yaml.safe_load(Path(f"config/{env}.yaml").read_text())

    # Compile the Python KFP pipeline into the YAML template Vertex will submit.
    compiler.Compiler().compile(
        pipeline_func=daily_orders_pipeline,
        package_path="/tmp/daily_orders.yaml",
    )

    client = storage.Client(project=cfg["project_id"])

    # 1) Upload the compiled pipeline template.
    upload_file(client, "/tmp/daily_orders.yaml", cfg["template_uri"])

    # 2) Upload the selected user config for this environment.
    upload_file(client, f"config/{env}.yaml", cfg["config_uri"])

    # 3) Upload the whole SQL folder, not just fct_orders.sql.
    upload_sql_bundle(client, "sql", cfg["sql_uri"])
"""

GCS_PATHS = """
template_path = gs://vertex-pipelines-prod/pipelines/19ab42f/daily_orders.yaml
config_path = gs://vertex-pipelines-prod/config/19ab42f/prod.yaml
sql_path = gs://vertex-pipelines-prod/sql/19ab42f
"""

SQL_BUNDLE = """
sql/
  staging/orders_delta.sql
  staging/order_items_delta.sql
  intermediate/order_lines_enriched.sql
  intermediate/customer_order_day.sql
  marts/fct_orders.sql
"""

st.set_page_config(
    page_title='GCS | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('GCS (runtime artifacts)')
st.caption('Chapter 4: upload the runtime files Vertex will actually read')
st.write(
    'This GCS step exists because Vertex needs fixed file addresses it can read at runtime, not just repo files. '
    'By the time a run starts, Vertex should be able to fetch one compiled template, one selected user config, and one versioned SQL bundle from GCS.'
)
st.write(
    'That is why Build & Release uploads artifacts here: the repo is the source of truth for development, '
    'but GCS is the runtime handoff point for execution, reruns, rollback, and audit.'
)
st.write(
    'When I say "URI" here, I just mean the full file address, like `gs://vertex-pipelines-prod/sql/19ab42f/marts/fct_orders.sql`. '
    'If "URI" is noisy, read it as "GCS path" or "address".'
)

st.subheader('Annotated `build/deploy_vx_pipeline.py` example')
st.write(
    'This is the file that actually pushes the runtime artifacts to GCS. The important part is not just compiling the pipeline, '
    'but also uploading the user config and the full SQL folder under versioned paths.'
)
st.code(ANNOTATED_DEPLOY_FILE.strip(), language='python')

st.markdown(
    """
**Loading the environment configuration:** The first step loads `config/{env}.yaml`, which contains the settings specific to this environment (production, staging, etc.). This config file tells the script exactly which GCS buckets and paths to upload to, so each environment can have its own separate storage location.

**Compiling and uploading the template:** The script uses KFP [Kubeflow Pipelines, a framework for defining data pipelines] to compile `daily_orders_pipeline` into a YAML file (`daily_orders.yaml`). This YAML is the actual template that Vertex AI Pipelines will read and execute later. Once compiled, it gets uploaded to GCS at the path specified in the config.

**Uploading the environment-specific configuration:** The selected config file for this environment also gets uploaded to GCS. This ensures that when Vertex runs the pipeline, it uses the correct parameter values and table names for this specific environment rather than defaults or values from a different environment.

**Uploading the complete SQL bundle:** Instead of uploading just the final query (`fct_orders.sql`), the code uploads every SQL file in the `sql/` folder. This is crucial because each SQL file might depend on outputs from earlier stages in the pipeline, so all files must be versioned and published together. If any one of those upstream files changes, the entire release changes.
"""
)

runtime_col, sql_col = st.columns(2)

with runtime_col:
    st.markdown('**GCS paths Vertex will use**')
    st.code(GCS_PATHS.strip(), language='text')

with sql_col:
    st.markdown('**SQL bundle uploaded to GCS**')
    st.code(SQL_BUNDLE.strip(), language='text')

st.write(
    'Uploading the whole SQL bundle matters because `fct_orders.sql` depends on the earlier stages: '
    '`orders_delta.sql`, `order_items_delta.sql`, `order_lines_enriched.sql`, and `customer_order_day.sql`. '
    'If one of those changes, the release has changed.'
)

st.info(
    '**Story checkpoint: Your release artifacts are now safely stored in GCS with fixed, addressable paths.** '
    'The compiled pipeline template (the YAML that Vertex will submit), your environment-specific configuration file, and your entire SQL folder are all uploaded to GCS. '
    'Each artifact is versioned using the same commit SHA, creating a complete release package. '
    'GCS serves as the handoff point between your build system and your runtime system. '
    'Vertex does not fetch code from GitHub during execution; instead, it reads the versioned artifacts from GCS. '
    'This separation means you can rerun old data by using old artifact versions, rollback to a known-good configuration, and audit exactly which SQL ran on which day.'
)
st.success(
    '**Next: Vertex AI Pipelines (Chapter 5).** '
    'Now it is time to see how Vertex actually executes your pipeline. '
    'You will learn how the pipeline components you defined in Python become managed steps that run in containers, '
    'how Vertex passes the GCS paths to each step so it knows which config and SQL to use, '
    'and how the pipeline defines dependencies between steps using the directed acyclic graph.'
)
