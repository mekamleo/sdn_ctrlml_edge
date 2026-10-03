#!/usr/bin/env python3


class RoundRobin:
    """
    Ordonnanceur Round Robin.

    Chaque nouvelle requête est affectée au prochain
    contrôleur disponible.
    """

    def __init__(self, controllers):
        if not controllers:
            raise ValueError("La liste des contrôleurs est vide")

        self.controllers = controllers
        self.current = 0

    def select_controller(self):
        """
        Retourne le prochain contrôleur.
        """

        controller = self.controllers[self.current]

        self.current = (
            self.current + 1
        ) % len(self.controllers)

        return controller

    def reset(self):
        """
        Réinitialise l'ordonnancement.
        """

        self.current = 0


class DomainRoundRobin:
    """
    Gestionnaire Round Robin pour plusieurs domaines.

    Chaque domaine possède son propre ordonnanceur.
    """

    def __init__(self, domains):
        """
        Exemple :

        domains = {
            "edge1": ["ryu1", "ryu2"],
            "edge2": ["ryu3", "ryu4"]
        }
        """

        self.schedulers = {
            domain: RoundRobin(controllers)
            for domain, controllers in domains.items()
        }

    def select_controller(self, domain):
        """
        Sélectionne un contrôleur pour le domaine indiqué.
        """

        if domain not in self.schedulers:
            raise ValueError(
                f"Domaine inconnu : {domain}"
            )

        return self.schedulers[domain].select_controller()

    def reset(self):
        """
        Réinitialise tous les domaines.
        """

        for scheduler in self.schedulers.values():
            scheduler.reset()


if __name__ == "__main__":

    domains = {
        "edge1": ["ryu1", "ryu2"],
        "edge2": ["ryu3", "ryu4"]
    }

    scheduler = DomainRoundRobin(domains)

    print("=== TEST ROUND ROBIN PAR DOMAINE ===")

    print("\n--- EDGE 1 ---")

    for i in range(6):

        controller = scheduler.select_controller("edge1")

        print(
            f"Requête {i + 1} -> {controller}"
        )

    print("\n--- EDGE 2 ---")

    for i in range(6):

        controller = scheduler.select_controller("edge2")

        print(
            f"Requête {i + 1} -> {controller}"
        )
