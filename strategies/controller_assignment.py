#!/usr/bin/env python3

import subprocess

from round_robin import DomainRoundRobin


class ControllerAssignment:

    def __init__(self, controller_addresses):
        self.controller_addresses = controller_addresses

    def assign_controller(self, switch, controller):

        if controller not in self.controller_addresses:
            raise ValueError(
                f"Contrôleur inconnu : {controller}"
            )

        address = self.controller_addresses[controller]

        command = [
            "ovs-vsctl",
            "set-controller",
            switch,
            address
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Erreur pour {switch} -> {controller}: "
                f"{result.stderr}"
            )

        print(
            f"[ASSIGNMENT] {switch} -> {controller} "
            f"({address})"
        )

    def assign_domain(self, assignments):

        for switch, controller in assignments.items():
            self.assign_controller(
                switch,
                controller
            )


if __name__ == "__main__":

    controllers = {
        "ryu1": "tcp:127.0.0.1:6653",
        "ryu2": "tcp:127.0.0.1:6654",
        "ryu3": "tcp:127.0.0.1:6655",
        "ryu4": "tcp:127.0.0.1:6656"
    }

    domains = {
        "edge1": ["ryu1", "ryu2"],
        "edge2": ["ryu3", "ryu4"]
    }

    switches = {
        "edge1": ["s1", "s2", "s3"],
        "edge2": ["s4", "s5", "s6"]
    }

    scheduler = DomainRoundRobin(domains)

    assignment = ControllerAssignment(
        controllers
    )

    assignments = {}

    for domain, domain_switches in switches.items():

        for switch in domain_switches:

            controller = scheduler.select_controller(
                domain
            )

            assignments[switch] = controller

    print("\n========== ROUND ROBIN ==========")

    for switch, controller in assignments.items():
        print(f"{switch} -> {controller}")

    print("=================================\n")

    assignment.assign_domain(assignments)
