import streamlit as st
from src.utils.layout import apply_base_style

st.set_page_config(
    page_title='GitHub | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('GitHub Repo Structure: chapter 1 of the daily_orders story')
st.write(
    'We have one concrete goal: publish daily_orders by 6:00 AM every day. '
    'This page is the exact repo walkthrough for that build.'
)
st.write(
    'For this walkthrough, the repo owns deployment logic, components, project config, SQL, a suggested monitoring config, and the Dockerfile used for the component runtime image. '
    'That image is built from the repo, published with an immutable tag, and referenced from the component code at compile time.'
)
st.write(
    'The repo structure in this walkthrough is centered on a `Dockerfile`, `build/`, `components/`, `config/`, and `sql/`: '
    'the image is built from source, deployment logic lives in `build/`, component definitions live in `components/`, '
    'environment settings live in `config/`, and the ETL SQL stays first-class in `sql/`.'
)

REPO_STRUCTURE = (
    '.\n'
    '|-- Dockerfile                   # runtime image definition for components\n'
    '|-- requirements.txt             # Python dependencies for build/runtime\n'
    '|-- build/\n'
    '|   |-- cloudbuild.yaml          # CI/CD entrypoint for deploy\n'
    '|   |-- deploy_vx_pipeline.py    # compile pipeline and upload artifacts\n'
    '|   `-- pipeline.py              # KFP pipeline definition\n'
    '|-- components/\n'
    '|   `-- components.py            # all pipeline components\n'
    '|-- config/\n'
    '|   |-- dev.yaml                 # dev project/runtime config\n'
    '|   |-- test.yaml                # test project/runtime config\n'
    '|   `-- prod.yaml                # prod project/runtime config\n'
    '|-- monitoring/\n'
    '|   `-- alerts.yaml              # suggested alert definitions for pipeline ops\n'
    '|-- sql/\n'
    '|   |-- staging/\n'
    '|   |   |-- orders_delta.sql\n'
    '|   |   `-- order_items_delta.sql\n'
    '|   |-- intermediate/\n'
    '|   |   |-- order_lines_enriched.sql\n'
    '|   |   `-- customer_order_day.sql\n'
    '|   `-- marts/\n'
    '|       `-- fct_orders.sql\n'
    '`-- README.md\n'
)

SAMPLE_FILES = {
    'Dockerfile': {
        'language': 'dockerfile',
        'what': 'Defines the runtime image used by the KFP components.',
        'story': 'Keeping the Dockerfile in the repo makes the runtime explicit: dependency changes travel through code review, the image can be rebuilt deterministically, and the compiled pipeline can point to a SHA-tagged artifact. Config and SQL are published separately as versioned release assets.',
        'content': """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY build ./build
COPY components ./components

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
""",
    },
    'build/cloudbuild.yaml': {
        'language': 'yaml',
        'what': 'Defines the CI job that runs when code is merged.',
        'story': 'This is the production deploy entrypoint for daily_orders: it builds the runtime image, publishes it with the commit SHA, then compiles and deploys the pipeline artifacts. It can also refresh the recurring trigger for the new release.',
        'content': """
steps:
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"
      - "."

  - name: "gcr.io/cloud-builders/docker"
    args:
      - "push"
      - "us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA"

  - name: "python:3.11"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        pip install -r requirements.txt
        export PIPELINE_COMPONENT_IMAGE=us-docker.pkg.dev/$PROJECT_ID/pipelines/daily-orders:$SHORT_SHA
        python build/deploy_vx_pipeline.py --env=${_ENV}

  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        gcloud scheduler jobs update http daily-orders-${_ENV} \
          --location=us-central1 \
          --schedule="0 3 * * *"
""",
    },
    'build/deploy_vx_pipeline.py': {
        'language': 'python',
        'what': 'Compiles the pipeline and uploads deploy artifacts to GCS.',
        'story': 'This is the operational bridge between source code and runtime: it compiles the template against the freshly built image, uploads the selected config, and publishes the SQL folder for daily_orders.',
        'content': """
import os
from pathlib import Path
import yaml
from kfp import compiler

from build.pipeline import daily_orders_pipeline

def deploy(env: str) -> None:
    cfg = yaml.safe_load(Path(f"config/{env}.yaml").read_text())
    image_uri = os.environ["PIPELINE_COMPONENT_IMAGE"]
    compiler.Compiler().compile(
        pipeline_func=daily_orders_pipeline,
        package_path="/tmp/daily_orders.yaml",
    )
    print(f"Compiled with component image {image_uri}")
    print(f"Upload /tmp/daily_orders.yaml to {cfg['template_uri']}")
    print(f"Upload config/{env}.yaml to {cfg['config_uri']}")
    print(f"Upload sql/ to {cfg['sql_uri']}")

if __name__ == "__main__":
    deploy(env="dev")
""",
    },
    'build/pipeline.py': {
        'language': 'python',
        'what': 'The KFP pipeline definition that connects each step.',
        'story': 'This stays in build because it is part of the deployable contract. It wires together a believable ETL flow: stage raw orders, stage line items, enrich them, aggregate daily customer behavior, then publish the final fact table.',
        'content': """
from kfp import dsl
from components.components import extract_orders, run_sql

@dsl.pipeline(name="daily-orders")
def daily_orders_pipeline(project_id: str, config_uri: str, sql_uri: str):
    extract = extract_orders(project_id=project_id, config_uri=config_uri)

    stage_orders = run_sql(
        config_uri=config_uri,
        sql_path=f"{sql_uri}/staging/orders_delta.sql",
        upstream_ref=extract.output,
    )
    stage_items = run_sql(
        config_uri=config_uri,
        sql_path=f"{sql_uri}/staging/order_items_delta.sql",
        upstream_ref=extract.output,
    )
    enriched_lines = run_sql(
        config_uri=config_uri,
        sql_path=f"{sql_uri}/intermediate/order_lines_enriched.sql",
        upstream_ref=stage_orders.output,
    ).after(stage_items)
    customer_order_day = run_sql(
        config_uri=config_uri,
        sql_path=f"{sql_uri}/intermediate/customer_order_day.sql",
        upstream_ref=enriched_lines.output,
    )
    run_sql(
        config_uri=config_uri,
        sql_path=f"{sql_uri}/marts/fct_orders.sql",
        upstream_ref=customer_order_day.output,
    )
""",
    },
    'components/components.py': {
        'language': 'python',
        'what': 'Contains the KFP components used by the pipeline.',
        'story': 'This keeps the business steps in one place while still making the runtime image explicit. The compile step injects the image URI so each deployed pipeline points at the exact container built from the repo Dockerfile.',
        'content': """
import os
from kfp import dsl

BASE_IMAGE = os.environ.get(
    "PIPELINE_COMPONENT_IMAGE",
    "us-docker.pkg.dev/shared-data-platform/pipelines/daily-orders:latest",
)

@dsl.component(base_image=BASE_IMAGE)
def extract_orders(project_id: str, config_uri: str) -> str:
    print(f"Loading config from {config_uri}")
    print(f"Extracting raw orders in {project_id}")
    return "gs://vertex-pipelines-dev/tmp/orders_delta.parquet"

@dsl.component(base_image=BASE_IMAGE)
def run_sql(config_uri: str, sql_path: str, upstream_ref: str = "") -> str:
    print(f"Running {sql_path} with params from {config_uri}")
    if upstream_ref:
        print(f"Waiting for upstream ref: {upstream_ref}")
    return "bq://analytics.fct_orders"
""",
    },
    'sql/staging/orders_delta.sql': {
        'language': 'sql',
        'what': 'Staging SQL for incremental extraction.',
        'story': 'This is still standard ETL SQL. Parameters come from config and are injected at runtime instead of being hardcoded into the pipeline definition.',
        'content': """
CREATE OR REPLACE TABLE ${orders_delta_table} AS
SELECT *
FROM ${orders_raw_table}
WHERE updated_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @watermark_days DAY)
""",
    },
    'sql/staging/order_items_delta.sql': {
        'language': 'sql',
        'what': 'Staging SQL for the line-item grain linked to the current orders delta.',
        'story': 'A believable order mart usually needs order headers and order lines. This step limits order_items to the active incremental order set so later transforms stay scoped and cheaper.',
        'content': """
CREATE OR REPLACE TABLE ${order_items_delta_table} AS
SELECT
  oi.order_id,
  oi.line_number,
  oi.product_id,
  oi.quantity,
  oi.extended_amount
FROM ${order_items_raw_table} oi
INNER JOIN ${orders_delta_table} o
  ON oi.order_id = o.order_id
""",
    },
    'sql/intermediate/order_lines_enriched.sql': {
        'language': 'sql',
        'what': 'Intermediate SQL that joins staged order headers to staged order lines.',
        'story': 'This is where the ETL becomes more realistic: the pipeline moves from raw deltas to a reusable analytical grain with one row per order line.',
        'content': """
CREATE OR REPLACE TABLE ${order_lines_enriched_table} AS
SELECT
  o.order_id,
  o.customer_id,
  DATE(o.created_at) AS order_date,
  o.status,
  oi.line_number,
  oi.product_id,
  oi.quantity,
  oi.extended_amount
FROM ${orders_delta_table} o
LEFT JOIN ${order_items_delta_table} oi
  ON o.order_id = oi.order_id
""",
    },
    'sql/intermediate/customer_order_day.sql': {
        'language': 'sql',
        'what': 'Intermediate aggregation for customer-level daily activity.',
        'story': 'This kind of reusable rollup is common in production: it supports the final fact table and can also feed downstream reporting or feature logic.',
        'content': """
CREATE OR REPLACE TABLE ${customer_order_day_table} AS
SELECT
  order_date,
  customer_id,
  COUNT(DISTINCT order_id) AS customer_order_count,
  SUM(extended_amount) AS customer_gross_revenue
FROM ${order_lines_enriched_table}
GROUP BY 1, 2
""",
    },
    'sql/marts/fct_orders.sql': {
        'language': 'sql',
        'what': 'Final transform SQL that builds the analytics table.',
        'story': 'This is the output stakeholders care about. It now reads like a real mart build: final rows come from enriched order lines and pull in a reusable customer-day aggregate.',
        'content': """
CREATE OR REPLACE TABLE ${daily_orders_table} AS
SELECT
  l.order_id,
  l.customer_id,
  l.order_date,
  l.product_id,
  l.quantity,
  l.extended_amount,
  d.customer_order_count,
  d.customer_gross_revenue
FROM ${order_lines_enriched_table} l
LEFT JOIN ${customer_order_day_table} d
  ON l.order_date = d.order_date
 AND l.customer_id = d.customer_id
""",
    },
    'config/dev.yaml': {
        'language': 'yaml',
        'what': 'Dev environment runtime config.',
        'story': 'This file holds the project-level settings, output table names, and SQL parameters used by the dev deployment.',
        'content': """
project_id: my-project-dev
region: us-central1
template_uri: gs://vertex-pipelines-dev/pipelines/${SHORT_SHA}/daily_orders.yaml
config_uri: gs://vertex-pipelines-dev/config/${SHORT_SHA}/dev.yaml
sql_uri: gs://vertex-pipelines-dev/sql/${SHORT_SHA}
tables:
  orders_raw_table: raw_dev.orders
  order_items_raw_table: raw_dev.order_items
  orders_delta_table: staging_dev.orders_delta
  order_items_delta_table: staging_dev.order_items_delta
  order_lines_enriched_table: intermediate_dev.order_lines_enriched
  customer_order_day_table: intermediate_dev.customer_order_day
  daily_orders_table: analytics_dev.fct_orders
sql_params:
  watermark_days: 2
""",
    },
    'config/test.yaml': {
        'language': 'yaml',
        'what': 'Test environment config.',
        'story': 'This mirrors dev and prod but points at the test project so daily_orders can be validated before promotion.',
        'content': """
project_id: my-project-test
region: us-central1
template_uri: gs://vertex-pipelines-test/pipelines/${SHORT_SHA}/daily_orders.yaml
config_uri: gs://vertex-pipelines-test/config/${SHORT_SHA}/test.yaml
sql_uri: gs://vertex-pipelines-test/sql/${SHORT_SHA}
tables:
  orders_raw_table: raw_test.orders
  order_items_raw_table: raw_test.order_items
  orders_delta_table: staging_test.orders_delta
  order_items_delta_table: staging_test.order_items_delta
  order_lines_enriched_table: intermediate_test.order_lines_enriched
  customer_order_day_table: intermediate_test.customer_order_day
  daily_orders_table: analytics_test.fct_orders
sql_params:
  watermark_days: 2
""",
    },
    'config/prod.yaml': {
        'language': 'yaml',
        'what': 'Production runtime config.',
        'story': 'This is the live daily_orders contract: production project, artifact locations, target tables, and SQL parameters.',
        'content': """
project_id: my-project-prod
region: us-central1
template_uri: gs://vertex-pipelines-prod/pipelines/${SHORT_SHA}/daily_orders.yaml
config_uri: gs://vertex-pipelines-prod/config/${SHORT_SHA}/prod.yaml
sql_uri: gs://vertex-pipelines-prod/sql/${SHORT_SHA}
tables:
  orders_raw_table: raw.orders
  order_items_raw_table: raw.order_items
  orders_delta_table: staging.orders_delta
  order_items_delta_table: staging.order_items_delta
  order_lines_enriched_table: intermediate.order_lines_enriched
  customer_order_day_table: intermediate.customer_order_day
  daily_orders_table: analytics.fct_orders
sql_params:
  watermark_days: 2
""",
    },
    'monitoring/alerts.yaml': {
        'language': 'yaml',
        'what': 'Suggested declarative alert config for the pipeline.',
        'story': 'This is a practical starting point if you have not built Vertex monitoring before: keep the desired alerts, thresholds, channels, and runbook links in one repo file, then wire that into whatever provisioning approach you adopt later.',
        'content': """
notification_channels:
  email_oncall: data-platform-oncall@primeflix.com
  slack_channel: "#data-platform-alerts"

alerts:
  - name: daily-orders-pipeline-failed
    source: vertex_pipeline
    severity: critical
    condition:
      pipeline_name: daily-orders
      states: [FAILED, CANCELLED]
    notify: [email_oncall, slack_channel]
    runbook: gs://vertex-pipelines-prod/runbooks/daily_orders_failure.md

  - name: daily-orders-runtime-too-long
    source: vertex_pipeline
    severity: warning
    condition:
      pipeline_name: daily-orders
      duration_minutes_gt: 45
    notify: [email_oncall]

  - name: daily-orders-freshness-late
    source: bigquery_check
    severity: critical
    sql: |
      SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(updated_at), MINUTE) AS freshness_lag_minutes
      FROM analytics.fct_orders
    condition:
      freshness_lag_minutes_gt: 180
    notify: [email_oncall, slack_channel]

  - name: daily-orders-row-count-drop
    source: bigquery_check
    severity: warning
    sql: |
      SELECT COUNT(*) AS row_count
      FROM analytics.fct_orders
      WHERE order_date = CURRENT_DATE() - 1
    condition:
      row_count_lt: 1000
    notify: [email_oncall]
""",
    },
}

if 'github_selected_file' not in st.session_state:
    st.session_state.github_selected_file = 'build/pipeline.py'

if st.session_state.github_selected_file not in SAMPLE_FILES:
    st.session_state.github_selected_file = 'build/pipeline.py'


# Small helper to emulate a file-browser click target in the left pane.
def file_picker_button(path: str, label: str) -> None:
    selected = st.session_state.github_selected_file == path
    icon = '📄'
    key = f"github_file_{path.replace('/', '_').replace('.', '_')}"
    if selected:
        st.markdown(
            f'<div class="repo-selected-file">{icon} {label}</div>',
            unsafe_allow_html=True,
        )
        return
    if st.button(f"{icon} {label}", key=key, use_container_width=True):
        st.session_state.github_selected_file = path


st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button {
        text-align: left;
        justify-content: flex-start;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }
    .repo-selected-file {
        background: #dbeafe;
        border: 1px solid #93c5fd;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        color: #0b1f44;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        padding: 0.45rem 0.6rem;
    }
    .file-explainer-card {
        background: #f8fbff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        color: #0b1f44;
        margin-top: 0.2rem;
        padding: 0.8rem 0.9rem;
    }
    .file-explainer-card p {
        margin: 0 0 0.55rem 0;
        line-height: 1.35;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.subheader('Suggested repo structure')
st.write('This is the minimal repo structure we need for the daily_orders walkthrough:')
st.code(REPO_STRUCTURE, language='text')

st.subheader('Interactive repo browser')
st.write('Click files in the left pane to see what each one does in our daily_orders walkthrough.')

browser_tree_col, browser_preview_col = st.columns([0.8, 2.2], gap='medium')

with browser_tree_col:
    st.markdown('**Repo Tree**')
    file_picker_button('Dockerfile', '|-- Dockerfile')

    with st.expander('📁 build/', expanded=False):
        file_picker_button('build/cloudbuild.yaml', '|-- cloudbuild.yaml')
        file_picker_button('build/deploy_vx_pipeline.py', '|-- deploy_vx_pipeline.py')
        file_picker_button('build/pipeline.py', '|-- pipeline.py')

    with st.expander('📁 components/', expanded=False):
        file_picker_button('components/components.py', '|-- components.py')

    with st.expander('📁 sql/', expanded=False):
        file_picker_button('sql/staging/orders_delta.sql', '|-- staging/orders_delta.sql')
        file_picker_button('sql/staging/order_items_delta.sql', '|-- staging/order_items_delta.sql')
        file_picker_button('sql/intermediate/order_lines_enriched.sql', '|-- intermediate/order_lines_enriched.sql')
        file_picker_button('sql/intermediate/customer_order_day.sql', '|-- intermediate/customer_order_day.sql')
        file_picker_button('sql/marts/fct_orders.sql', '|-- marts/fct_orders.sql')

    with st.expander('📁 config/', expanded=False):
        file_picker_button('config/dev.yaml', '|-- dev.yaml')
        file_picker_button('config/test.yaml', '|-- test.yaml')
        file_picker_button('config/prod.yaml', '|-- prod.yaml')

    with st.expander('📁 monitoring/', expanded=False):
        file_picker_button('monitoring/alerts.yaml', '|-- alerts.yaml')

with browser_preview_col:
    selected_file = st.session_state.github_selected_file
    example = SAMPLE_FILES[selected_file]

    details_col, preview_col = st.columns([1.2, 2.3], gap='medium')

    with details_col:
        st.markdown('**File explainer**')
        st.markdown(
            f"""
            <div class="file-explainer-card">
                <p><strong>Selected file:</strong><br><code>{selected_file}</code></p>
                <p><strong>What this file does:</strong><br>{example['what']}</p>
                <p><strong>How it helps daily_orders:</strong><br>{example['story']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with preview_col:
        st.markdown(f'**Preview: `{selected_file}`**')
        st.code(example['content'].strip(), language=example['language'])

st.divider()

st.info(
    '**Story checkpoint: Your GitHub repo is now set up as the single source of truth.** '
    'You have organized your Dockerfile, Python pipeline code, SQL files, and configuration in a way that makes sense. '
    'Your repo structure separates development concerns: the `build/` folder contains deployment logic, `components/` houses your pipeline steps, '
    '`sql/` holds your reviewed ETL queries, `config/` stores your environment-specific settings, and `monitoring/` documents your alerts. '
    'Everything is versioned and reviewable through pull requests.'
)
st.success(
    '**Next: Docker Images (Chapter 2).** '
    'Now that your repo is organized, you need to understand the Docker image that will run your pipeline steps. '
    'The next chapter explains what goes inside the container, why dependencies are frozen at build time, and how the image tag becomes the guarantee of reproducibility.'
)
