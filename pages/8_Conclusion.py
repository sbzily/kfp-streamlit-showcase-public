import streamlit as st
from src.utils.layout import apply_base_style

st.set_page_config(
    page_title='Conclusion | Vertex AI Pipelines Explainer',
    page_icon='🧩',
    layout='wide',
    initial_sidebar_state='expanded',
)

apply_base_style()

st.title('Conclusion')
st.caption('Chapter 7: how the whole daily_orders operating model fits together')

st.write(
    'You now have a complete picture of how to build a production-ready data pipeline on Vertex AI Pipelines. '
    'The key insight is that Vertex is not just "run some Python code somewhere." Instead, it is a structured release flow where your repo code is transformed into versioned runtime assets, and those assets become a managed pipeline execution.'
)

st.write(
    'Here is how the pieces connect: Your source code, SQL files, configuration, Dockerfile, and even your monitoring definitions all live in GitHub [your version control system]. '
    'When you merge changes, Cloud Build automatically reads that repo state and transforms it into a release. It builds a Docker container image and uploads it to Artifact Registry [where Vertex can pull it later]. '
    'At the same time, Cloud Build compiles your pipeline definition, uploads your config file, and packages your SQL folder, all to GCS [shared cloud storage that Vertex can access at runtime]. '
    'Finally, Vertex executes your pipeline steps using the exact image and configuration from that release. '
    'If something goes wrong, your monitoring alerts notify the team with context to help them debug and recover.'
)

st.write(
    'Organizing your pipeline this way has real benefits. Every pipeline run is traceable to a specific commit. If you need to rerun yesterday\'s data, you know exactly which code and configuration was used. '
    'If you need to roll back to an older version, all the artifacts are versioned and saved in your storage locations. '
    'Team members and new engineers can read your Git history to understand why monitoring thresholds are set a certain way, because those thresholds are versioned in your repo like any other code.'
)

st.subheader('Practical next steps if you build this')

st.write(
    'If you are ready to implement this for your own pipeline, start by setting up the repository structure with folders for your components, configuration files, SQL, and Dockerfile. '
    'Then create your Cloud Build trigger to automate the build and release process whenever you merge to a specific branch. '
    'You can start with the simplest possible alerts for pipeline failures and data freshness, then refine your monitoring as you learn what matters most in production. '
    'As your pipeline grows, add automated tests for your SQL queries and component logic before they reach production. '
    'Keep your environment promotion strategy simple at first: dev and prod might be enough to start, and you can add staging later if you need it.'
)

st.write(
    'The most important thing is to have a repeatable, documented process. '
    'When a new team member joins or an engineer needs to debug a failure at 2 AM, having everything versioned and documented in your repo saves time and reduces confusion. '
    'Your monitoring runbooks become tribal knowledge that survives team changes. Your versioned artifacts make root cause analysis straightforward instead of speculative.'
)

st.info(
    '**You have now completed the full walkthrough of a production Vertex AI Pipelines system.** '
    'You started with a well-organized GitHub repo (Chapter 1), moved through Docker Images to understand containerization (Chapter 2), '
    'then saw how Cloud Build automation creates versioned release artifacts (Chapter 3). '
    'You learned how GCS stores runtime files in fixed, addressable locations (Chapter 4) and how Vertex AI Pipelines executes your components as managed steps (Chapter 5). '
    'Monitoring and alerting guidance is coming soon as a detailed guide to keeping your system healthy. '
    'The daily_orders example ties all these pieces together into one cohesive operating model.'
)

st.write(
    '**Why this architecture matters:** Every pipeline run is traceable to a specific commit. Every artifact is versioned and immutable. '
    'When something goes wrong, you can examine the exact code, dependencies, configuration, and SQL that caused it. '
    'When you need to rerun historical data, roll back to a previous release, or audit what happened on a specific day, all the information is there in your versioned artifacts. '
    'New team members can read your Git history and your monitoring runbooks to understand the system without tribal knowledge. '
    'Your pipeline is not a mysterious black box on someone\'s laptop; it is a documented, repeatable, accountable process.'
)

st.success(
    '**You are ready to build.** '
    'Start by setting up your repo structure with folders for components, SQL, and configuration. '
    'Create a simple Cloud Build trigger to automate the release process. Set up basic alerts for failures and data freshness. '
    'Deploy to a dev environment first, verify everything works, then move to production. '
    'This template and walkthrough give you a proven starting point for a production-quality data pipeline on Vertex AI.'
)

