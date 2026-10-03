#!/usr/bin/env python3

from sklearn.cluster import KMeans


class ControllerClustering:

    def __init__(self, n_clusters=2):
        if n_clusters < 1:
            raise ValueError("Le nombre de clusters doit être >= 1.")

        self.n_clusters = n_clusters

    def cluster(self, controller_loads):
        if not controller_loads:
            raise ValueError("Aucune charge de controleur fournie.")

        controllers = list(controller_loads.keys())

        values = [
            [float(controller_loads[controller])]
            for controller in controllers
        ]

        # Si le nombre de contrôleurs est inférieur
        # au nombre de clusters demandé.
        n_clusters = min(self.n_clusters, len(controllers))

        model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(values)

        clusters = {}

        for controller, label in zip(controllers, labels):
            clusters.setdefault(int(label), [])
            clusters[int(label)].append(controller)

        centers = model.cluster_centers_.flatten().tolist()

        return {
            "controllers": controllers,
            "labels": labels.tolist(),
            "clusters": clusters,
            "centers": centers
        }


if __name__ == "__main__":

    controller_loads = {
        "ryu1": 10.0,
        "ryu2": 20.0,
        "ryu3": 70.0,
        "ryu4": 80.0
    }

    clustering = ControllerClustering(
        n_clusters=2
    )

    result = clustering.cluster(
        controller_loads
    )

    print("========== K-MEANS CONTROLLER CLUSTERING ==========")

    print("Charges :")
    for controller, load in controller_loads.items():
        print(
            "  %s -> %.2f %%"
            % (controller, load)
        )

    print("\nClusters :")

    for cluster_id, controllers in result["clusters"].items():
        print(
            "  Cluster %d -> %s"
            % (cluster_id, ", ".join(controllers))
        )

    print("\nCentres :")

    for cluster_id, center in enumerate(result["centers"]):
        print(
            "  Cluster %d -> %.2f %%"
            % (cluster_id, center)
        )
