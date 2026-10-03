from monitoring.controller_clustering_edge import ControllerClusteringEdge

metrics = {
    "ryu1": {
        "cpu": 0.20,
        "memory": 0.40,
        "throughput": 0.30,
        "latency": 0.20,
        "flows": 0.30
    },
    "ryu2": {
        "cpu": 0.10,
        "memory": 0.20,
        "throughput": 0.10,
        "latency": 0.10,
        "flows": 0.10
    },
    "ryu3": {
        "cpu": 0.80,
        "memory": 0.70,
        "throughput": 0.90,
        "latency": 0.80,
        "flows": 0.90
    },
    "ryu4": {
        "cpu": 0.70,
        "memory": 0.60,
        "throughput": 0.80,
        "latency": 0.70,
        "flows": 0.80
    }
}

clustering = ControllerClusteringEdge(
    n_clusters=2
)

result = clustering.cluster(
    metrics
)

print("Contrôleurs :", result["controllers"])
print("Labels      :", result["labels"])
print("Clusters    :", result["clusters"])
print("Centres     :", result["centers"])
print("Métriques   :", result["metrics"])
