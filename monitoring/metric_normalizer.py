#!/usr/bin/env python3

import math


class MetricNormalizer:

    METRICS = [
        "cpu",
        "memory",
        "throughput",
        "latency",
        "flows"
    ]

    def __init__(self):
        self.minimums = {}
        self.maximums = {}

    def fit(self, metrics):

        if not metrics:
            raise ValueError(
                "Aucune métrique fournie."
            )

        for metric in self.METRICS:

            values = []

            for controller_data in metrics.values():

                if metric in controller_data:

                    values.append(
                        float(controller_data[metric])
                    )

            if not values:
                continue

            self.minimums[metric] = min(values)
            self.maximums[metric] = max(values)

    def normalize_value(self, metric, value):

        value = float(value)

        minimum = self.minimums.get(
            metric,
            value
        )

        maximum = self.maximums.get(
            metric,
            value
        )

        if math.isclose(
            minimum,
            maximum
        ):
            return 0.0

        return (
            (value - minimum)
            / (maximum - minimum)
        )

    def transform(self, metrics):

        self.fit(metrics)

        normalized = {}

        for controller, data in metrics.items():

            normalized[controller] = {}

            for metric in self.METRICS:

                if metric not in data:
                    raise ValueError(
                        f"Métrique absente : "
                        f"{metric} pour {controller}"
                    )

                normalized[controller][metric] = (
                    self.normalize_value(
                        metric,
                        data[metric]
                    )
                )

        return normalized

    def to_vectors(self, normalized):

        vectors = {}

        for controller, data in normalized.items():

            vectors[controller] = [
                data["cpu"],
                data["memory"],
                data["throughput"],
                data["latency"],
                data["flows"]
            ]

        return vectors
