#!/usr/bin/env python3


class WeightedRoundRobin:
    """
    Ordonnanceur Weighted Round Robin.

    Chaque contrôleur reçoit un poids.
    Un contrôleur de poids plus élevé est sélectionné
    proportionnellement plus souvent.
    """

    def __init__(self, controllers_weights):
        if not controllers_weights:
            raise ValueError("Aucun contrôleur défini")

        if any(weight <= 0 for weight in controllers_weights.values()):
            raise ValueError("Les poids doivent être strictement positifs")

        self.controllers = list(controllers_weights.keys())
        self.weights = controllers_weights
        self.sequence = []

        for controller, weight in controllers_weights.items():
            self.sequence.extend([controller] * weight)

        self.current = 0

    def select_controller(self):
        controller = self.sequence[self.current]
        self.current = (self.current + 1) % len(self.sequence)
        return controller

    def reset(self):
        self.current = 0


class DomainWeightedRoundRobin:
    """
    Weighted Round Robin indépendant pour chaque domaine.
    """

    def __init__(self, domains):
        self.schedulers = {
            domain: WeightedRoundRobin(weights)
            for domain, weights in domains.items()
        }

    def select_controller(self, domain):
        if domain not in self.schedulers:
            raise ValueError(f"Domaine inconnu : {domain}")

        return self.schedulers[domain].select_controller()

    def reset(self):
        for scheduler in self.schedulers.values():
            scheduler.reset()


if __name__ == "__main__":

    domains = {
        "edge1": {
            "ryu1": 1,
            "ryu2": 2
        },
        "edge2": {
            "ryu3": 1,
            "ryu4": 2
        }
    }

    scheduler = DomainWeightedRoundRobin(domains)

    print("=== TEST WEIGHTED ROUND ROBIN PAR DOMAINE ===")

    for domain in ["edge1", "edge2"]:
        print(f"\n--- {domain.upper()} ---")

        for i in range(6):
            controller = scheduler.select_controller(domain)
            print(f"Requête {i + 1} -> {controller}")
