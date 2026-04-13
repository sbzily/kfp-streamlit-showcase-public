from graphviz import Digraph


def build_architecture_diagram(include_artifact_registry: bool = True) -> Digraph:
    """
    High-level system diagram:
    GitHub -> Cloud Build -> (GCS) -> Vertex AI Pipelines -> Monitoring/Alerting

    If include_artifact_registry=True, show optional container image build/push.
    """
    g = Digraph()
    g.attr(
        rankdir="TB",
        bgcolor="#f8fafc",
        nodesep="0.2",
        ranksep="0.25",
        pad="0.08",
        ratio="compress",
        size="5.5,6.5!",
        dpi="65",
    )
    g.attr(
        "node",
        style="filled",
        fontname="Helvetica",
        color="#0f5fa8",
        fontcolor="#0b1f44",
        fillcolor="#e6f0fb",
        penwidth="1.4",
        fontsize="15",
        margin="0.06,0.04",
    )
    g.attr("edge", color="#5b7bc6", penwidth="1.0", fontsize="15")

    g.node("GitHub", "GitHub\n(dev/test/prod)", shape="box", fillcolor="#e8f5e9")
    g.node("CB", "Build & Release\n(Cloud Build)", shape="box", fillcolor="#e3f2fd")
    g.node("GCS", "GCS Buckets\n(artifacts)", shape="box", fillcolor="#fff8e1")
    g.node("Vertex", "Vertex Pipelines\n(KFP Components with ETL/ELT Steps)", shape="box", fillcolor="#ede7f6")
    g.node("Obs", "Monitoring\n(alerts)", shape="box", fillcolor="#f3e5f5")

    g.edge("GitHub", "CB", label="push/merge")
    g.edge("CB", "GCS", label="upload artifacts")
    g.edge("CB", "Vertex", label="deploy/update")
    g.edge("Vertex", "Obs", label="logs/metrics")

    if include_artifact_registry:
        g.node("AR", "Docker Images\n(Artifact Registry)", shape="box", fillcolor="#e0f7fa")
        g.edge("CB", "AR", label="optional: build/push")
        g.edge("Vertex", "AR", label="pull images")

    return g



def build_docker_flow_diagram(
    include_base_image: bool = True,
    include_build_cache: bool = True,
) -> Digraph:
    g = Digraph()
    g.attr(rankdir="LR")

    g.node("repo", "Repo (components + Dockerfile)", shape="box")
    g.node("build", "Cloud Build\nruns cloudbuild.yaml", shape="box")
    g.node("ar", "Artifact Registry\nstores image tag", shape="box")
    g.node("template", "Pipeline template\n(image refs)", shape="box")
    g.node("vertex", "Vertex Pipeline Job\n(run container)", shape="box")

    g.edge("repo", "build")
    g.edge("build", "ar")
    g.edge("ar", "template")
    g.edge("template", "vertex")

    if include_base_image:
        g.node("base", "Base image\n(Python/OS)", shape="note")
        g.edge("base", "repo", style="dashed")

    if include_build_cache:
        g.node("cache", "Build cache", shape="note")
        g.edge("cache", "build", style="dashed")

    return g
