#!/usr/bin/env python3

from monitoring.scheduling_layer import SchedulingLayer


class SDNCTRLMLEdge:

    def __init__(
        self,
        controllers,
        ema_alpha=0.3
    ):

        if not controllers:
            raise ValueError(
                "Aucun controleur defini."
            )

        self.controllers = controllers

        self.scheduler = SchedulingLayer(
            controllers,
            n_clusters=3,
            ema_alpha=ema_alpha
        )

    def select_controller(
        self,
        network_metrics=None,
        controller_flows=None
    ):

        result = self.scheduler.schedule(
            network_metrics=network_metrics,
            controller_flows=controller_flows
        )

        return (
            result["selected_controller"],
            result
        )


class DomainSDNCTRLMLEdge:

    def __init__(
        self,
        domains,
        ema_alpha=0.3
    ):

        if not domains:
            raise ValueError(
                "Aucun domaine defini."
            )

        self.domains = domains
        self.schedulers = {}

        for domain, controllers in domains.items():

            self.schedulers[domain] = (
                SDNCTRLMLEdge(
                    controllers,
                    ema_alpha=ema_alpha
                )
            )

    def select_controller(
        self,
        domain,
        network_metrics=None,
        controller_flows=None
    ):

        if domain not in self.schedulers:

            raise ValueError(
                "Domaine inconnu : %s"
                % domain
            )

        return self.schedulers[
            domain
        ].select_controller(
            network_metrics=network_metrics,
            controller_flows=controller_flows
        )
