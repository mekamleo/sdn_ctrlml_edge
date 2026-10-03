#!/usr/bin/env python3

from monitoring.scheduling_layer import SchedulingLayer


class SDNCTRLML:

    def __init__(
        self,
        controllers,
        n_clusters=2
    ):

        self.controllers = controllers

        self.scheduler = SchedulingLayer(
            controllers,
            n_clusters=n_clusters
        )

        self.loads = {}

    def select_controller(self):

        result = self.scheduler.schedule()

        self.loads = result["loads"]

        return (
            result["selected_controller"],
            result
        )


class DomainSDNCTRLML:

    def __init__(
        self,
        domains,
        n_clusters=2
    ):

        if not domains:
            raise ValueError(
                "Aucun domaine defini."
            )

        self.domains = domains

        all_controllers = []

        for controllers in domains.values():

            for controller in controllers:

                if controller not in all_controllers:

                    all_controllers.append(
                        controller
                    )

        self.scheduler = SDNCTRLML(
            all_controllers,
            n_clusters=n_clusters
        )

    def select_controller(self):

        return self.scheduler.select_controller()


if __name__ == "__main__":

    controllers = [
        "ryu1",
        "ryu2",
        "ryu3",
        "ryu4"
    ]

    scheduler = SDNCTRLML(
        controllers,
        n_clusters=2
    )

    controller, result = (
        scheduler.select_controller()
    )

    print(
        "========== SDN CTRLML =========="
    )

    print(
        "Charges : %s"
        % result["loads"]
    )

    print(
        "Clusters : %s"
        % result["clustering"]["clusters"]
    )

    print(
        "Controleur selectionne : %s"
        % controller
    )

