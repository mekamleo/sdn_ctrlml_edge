#!/usr/bin/env python3


class DomainControllerScheduler:
    """
    Gestionnaire de contrôleurs par domaine.

    Le scheduler maintient une liste de contrôleurs
    disponibles pour chaque domaine et sélectionne
    le prochain contrôleur selon Round Robin.
    """

    def __init__(self, domains):
        if not domains:
            raise ValueError("Aucun domaine défini")

        self.domains = domains

        self.index = {
            domain: 0
            for domain in domains
        }

    def select_controller(self, domain):
        """
        Sélectionne le prochain contrôleur du domaine.
        """

        if domain not in self.domains:
            raise ValueError(
                f"Domaine inconnu : {domain}"
            )

        controllers = self.domains[domain]

        if not controllers:
            raise ValueError(
                f"Aucun contrôleur disponible pour {domain}"
            )

        controller = controllers[
            self.index[domain]
        ]

        self.index[domain] = (
            self.index[domain] + 1
        ) % len(controllers)

        return controller

    def get_current_controller(self, domain):
        """
        Retourne le contrôleur actuellement sélectionné
        sans modifier l'état du Round Robin.
        """

        if domain not in self.domains:
            raise ValueError(
                f"Domaine inconnu : {domain}"
            )

        controllers = self.domains[domain]

        return controllers[
            self.index[domain]
        ]


if __name__ == "__main__":

    domains = {
        "edge1": ["ryu1", "ryu2"],
        "edge2": ["ryu3", "ryu4"]
    }

    scheduler = DomainControllerScheduler(domains)

    print("=== TEST CONTROLLER SCHEDULER ===")

    for i in range(6):

        controller = scheduler.select_controller(
            "edge1"
        )

        print(
            f"EDGE 1 - requête {i + 1} -> "
            f"{controller}"
        )

    for i in range(6):

        controller = scheduler.select_controller(
            "edge2"
        )

        print(
            f"EDGE 2 - requête {i + 1} -> "
            f"{controller}"
        )
