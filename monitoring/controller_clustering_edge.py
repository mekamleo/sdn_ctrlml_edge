#!/usr/bin/env python3

from sklearn.cluster import KMeans


class ControllerClusteringEdge:

    METRICS = [
        "cpu",
        "memory",
        "throughput",
        "latency",
        "flows"
    ]

    STATES = {
        0: "underloaded",
        1: "normal",
        2: "overloaded"
    }

    def __init__(self, n_clusters=3, history_size=30):

        if n_clusters != 3:
            raise ValueError(
                "SDN_CTRLML-Edge utilise exactement 3 etats : "
                "underloaded, normal, overloaded."
            )

        if history_size < 3:
            raise ValueError(
                "history_size doit etre >= 3."
            )

        self.n_clusters = n_clusters
        self.history_size = history_size

        self.history = []

    # --------------------------------------------------------
    # Construction du vecteur d'un controleur
    # --------------------------------------------------------

    def build_vector(self, metrics):

        vector = []

        for metric in self.METRICS:

            if metric not in metrics:
                raise ValueError(
                    f"Metrique absente : {metric}"
                )

            vector.append(
                float(metrics[metric])
            )

        return vector

    # --------------------------------------------------------
    # Ajout d'une observation
    # --------------------------------------------------------

    def add_observations(self, normalized_metrics):

        for controller, data in normalized_metrics.items():

            vector = self.build_vector(data)

            self.history.append({
                "controller": controller,
                "vector": vector
            })

        # Limitation de l'historique
        if len(self.history) > self.history_size:

            self.history = self.history[
                -self.history_size:
            ]

    # --------------------------------------------------------
    # Calcul du profil de charge d'un centroide
    # --------------------------------------------------------

    def centroid_load(self, centroid):

        if centroid is None or len(centroid) == 0:
            return 0.0

        return sum(
            float(value)
            for value in centroid
        ) / len(centroid)

    # --------------------------------------------------------
    # Classification K-means++
    # --------------------------------------------------------

    def cluster(self, normalized_metrics):

        if not normalized_metrics:
            raise ValueError(
                "Aucune metrique de controleur fournie."
            )

        # Ajouter les observations courantes
        self.add_observations(
            normalized_metrics
        )

        # Il faut au minimum 3 observations
        # pour identifier les 3 etats.
        if len(self.history) < self.n_clusters:

            return {
                "ready": False,
                "controllers": list(
                    normalized_metrics.keys()
                ),
                "states": {},
                "clusters": {},
                "centers": [],
                "message":
                    "Historique insuffisant pour K=3."
            }

        vectors = [
            item["vector"]
            for item in self.history
        ]

        model = KMeans(
            n_clusters=self.n_clusters,
            init="k-means++",
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(
            vectors
        )

        centers = model.cluster_centers_

        # ----------------------------------------------------
        # Classer les clusters selon leur charge moyenne
        # ----------------------------------------------------

        cluster_loads = {}

        for cluster_id, center in enumerate(centers):

            cluster_loads[
                cluster_id
            ] = self.centroid_load(center)

        ordered_clusters = sorted(
            cluster_loads,
            key=cluster_loads.get
        )

        # Le cluster avec la charge la plus faible
        # devient C1.
        #
        # Le cluster intermediaire devient C2.
        #
        # Le cluster avec la charge la plus forte
        # devient C3.

        state_mapping = {
            ordered_clusters[0]: "C1",
            ordered_clusters[1]: "C2",
            ordered_clusters[2]: "C3"
        }

        state_names = {
            "C1": "underloaded",
            "C2": "normal",
            "C3": "overloaded"
        }

        # ----------------------------------------------------
        # Etat des observations courantes
        # ----------------------------------------------------

        current_states = {}

        current_scores = {}

        for controller, data in normalized_metrics.items():

            vector = self.build_vector(data)

            # Distance aux centroïdes
            distances = [
                sum(
                    (vector[i] - center[i]) ** 2
                    for i in range(len(vector))
                )
                for center in centers
            ]

            cluster_id = min(
                range(len(distances)),
                key=distances.__getitem__
            )

            state = state_mapping[
                cluster_id
            ]

            current_states[
                controller
            ] = state

            # Score de charge du contrôleur
            current_scores[
                controller
            ] = sum(vector) / len(vector)

        # ----------------------------------------------------
        # Profils des centroïdes
        # ----------------------------------------------------

        profiles = {}

        for cluster_id, center in enumerate(centers):

            state = state_mapping[
                cluster_id
            ]

            profiles[state] = {
                "state": state_names[state],
                "cpu": float(center[0]),
                "memory": float(center[1]),
                "throughput": float(center[2]),
                "latency": float(center[3]),
                "flows": float(center[4]),
                "load_score":
                    float(cluster_loads[cluster_id])
            }

        return {
            "ready": True,
            "controllers": list(
                normalized_metrics.keys()
            ),
            "states": current_states,
            "state_names": state_names,
            "scores": current_scores,
            "clusters": state_mapping,
            "centers": profiles,
            "history_size": len(self.history),
            "metrics": self.METRICS
        }
