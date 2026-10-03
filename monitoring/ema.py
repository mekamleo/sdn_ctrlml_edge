#!/usr/bin/env python3


class ExponentialMovingAverage:

    def __init__(self, alpha=0.3):

        if not 0 < alpha <= 1:
            raise ValueError(
                "alpha doit être compris entre 0 et 1."
            )

        self.alpha = float(alpha)
        self.values = {}

    def update(self, key, value):

        value = float(value)

        if key not in self.values:

            self.values[key] = value

        else:

            self.values[key] = (
                self.alpha * value
                + (1 - self.alpha) * self.values[key]
            )

        return self.values[key]

    def update_all(self, values):

        smoothed = {}

        for key, value in values.items():

            smoothed[key] = self.update(
                key,
                value
            )

        return smoothed

    def get(self, key, default=0.0):

        return self.values.get(
            key,
            default
        )

    def get_all(self):

        return dict(self.values)
