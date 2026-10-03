#!/usr/bin/env python3

from monitoring.controller_workload_monitor import (
    ControllerWorkloadMonitor
)

from monitoring.metric_normalizer import (
    MetricNormalizer
)

from monitoring.controller_clustering_edge import (
    ControllerClusteringEdge
)

from monitoring.ema import (
    ExponentialMovingAverage
)


class SchedulingLayer:

    def __init__(
        self,
        controllers,
        n_clusters=3,
        ema_alpha=0.3
    ):

        if not controllers:
            raise ValueError(
                "Aucun controleur fourni."
            )

        self.controllers = controllers

        self.monitor = ControllerWorkloadMonitor(
            controllers
        )

        self.normalizer = MetricNormalizer()

        self.ema = {
            controller: {
                metric: ExponentialMovingAverage(
                    alpha=ema_alpha
                )
                for metric in [
                    "cpu",
                    "memory",
                    "throughput",
                    "latency",
                    "flows"
                ]
            }
            for controller in controllers
        }

        self.clustering = ControllerClusteringEdge(
            n_clusters=n_clusters
        )

        self.last_result = None

    # ========================================================
    # METRIQUES DES CONTROLEURS
    # ========================================================

    def get_controller_workloads(self):

        workloads = self.monitor.get_all_workloads()

        result = {}

        for controller in self.controllers:

            workload = workloads.get(
                controller,
                {}
            )

            result[controller] = {
                "cpu": float(
                    workload.get("cpu", 0.0)
                ),

                "memory": float(
                    workload.get("memory", 0.0)
                )
            }

        return result

    # ========================================================
    # CONSTRUCTION DES 5 METRIQUES
    # ========================================================

    def get_controller_metrics(
        self,
        network_metrics=None,
        controller_flows=None
    ):

        workloads = self.get_controller_workloads()

        network_metrics = (
            network_metrics
            if network_metrics is not None
            else {}
        )

        controller_flows = (
            controller_flows
            if controller_flows is not None
            else {}
        )

        throughput = float(
            network_metrics.get(
                "throughput",
                0.0
            )
        )

        latency = float(
            network_metrics.get(
                "latency",
                0.0
            )
        )

        metrics = {}

        for controller in self.controllers:

            metrics[controller] = {

                "cpu":
                    workloads[controller]["cpu"],

                "memory":
                    workloads[controller]["memory"],

                "throughput":
                    throughput,

                "latency":
                    latency,

                "flows":
                    float(
                        controller_flows.get(
                            controller,
                            0.0
                        )
                    )
            }

        return metrics

    # ========================================================
    # EMA
    # ========================================================

    def apply_ema(self, metrics):

        smoothed = {}

        for controller, values in metrics.items():

            smoothed[controller] = {}

            for metric, value in values.items():

                smoothed[controller][metric] = (
                    self.ema[controller][metric].update(
                        metric,
                        value
                    )
                )

        return smoothed

    # ========================================================
    # SCORE DE CHARGE
    # ========================================================

    def calculate_load_score(
        self,
        normalized_metrics
    ):

        scores = {}

        for controller, metrics in (
            normalized_metrics.items()
        ):

            values = [
                float(metrics["cpu"]),
                float(metrics["memory"]),
                float(metrics["throughput"]),
                float(metrics["latency"]),
                float(metrics["flows"])
            ]

            scores[controller] = (
                sum(values) / len(values)
            )

        return scores

    # ========================================================
    # SELECTION DU CONTROLEUR
    # ========================================================

    def select_controller_from_result(
        self,
        result
    ):

        controllers = result["controllers"]

        if not controllers:
            return None

        scores = result.get(
            "scores",
            {}
        )

        states = result.get(
            "states",
            {}
        )

        if len(controllers) == 1:
            return controllers[0]

        state_rank = {
            "C1": 1,
            "C2": 2,
            "C3": 3
        }

        ranked = sorted(
            controllers,
            key=lambda controller: (
                state_rank.get(
                    states.get(
                        controller,
                        "C3"
                    ),
                    3
                ),
                scores.get(
                    controller,
                    float("inf")
                )
            )
        )

        return ranked[0]

    # ========================================================
    # PLANIFICATION
    # ========================================================

    def schedule(
        self,
        network_metrics=None,
        controller_flows=None
    ):

        raw_metrics = self.get_controller_metrics(
            network_metrics=network_metrics,
            controller_flows=controller_flows
        )

        smoothed_metrics = self.apply_ema(
            raw_metrics
        )

        normalized_metrics = (
            self.normalizer.transform(
                smoothed_metrics
            )
        )

        clustering = self.clustering.cluster(
            normalized_metrics
        )

        if not clustering["ready"]:

            scores = self.calculate_load_score(
                normalized_metrics
            )

            selected = min(
                scores,
                key=scores.get
            )

            result = {

                "raw_metrics":
                    raw_metrics,

                "smoothed_metrics":
                    smoothed_metrics,

                "normalized_metrics":
                    normalized_metrics,

                "scores":
                    scores,

                "clustering":
                    clustering,

                "selected_controller":
                    selected
            }

            self.last_result = result

            return result

        selected = (
            self.select_controller_from_result(
                clustering
            )
        )

        result = {

            "raw_metrics":
                raw_metrics,

            "smoothed_metrics":
                smoothed_metrics,

            "normalized_metrics":
                normalized_metrics,

            "scores":
                clustering["scores"],

            "clustering":
                clustering,

            "selected_controller":
                selected
        }

        self.last_result = result

        return result
