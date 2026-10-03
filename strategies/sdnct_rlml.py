#!/usr/bin/env python3

"""
Baseline SDNCT-RLML-inspired.

Cette implementation realise une affectation des switches
aux controleurs en fonction de leur charge observee.

Elle est utilisee comme baseline inspiree de SDNCT-RLML
et non comme reproduction exacte de l'algorithme original.
"""


class SDNCTRLML:

    def __init__(self, controller_loads):
        """
        controller_loads :
        dictionnaire {controleur: charge}

        Exemple :
        {
            "ryu1": 20.0,
            "ryu2": 35.0
        }
        """

        if not controller_loads:
            raise ValueError(
                "La liste des charges des controleurs est vide."
            )

        self.controller_loads = controller_loads.copy()

    def select_controller(self):
        """
        Selectionne le controleur ayant la plus faible charge.
        """

        return min(
            self.controller_loads,
            key=self.controller_loads.get
        )

    def update_load(self, controller, load):
        """
        Met a jour la charge observee d'un controleur.
        """

        if controller not in self.controller_loads:
            raise ValueError(
                "Controleur inconnu : %s" % controller
            )

        self.controller_loads[controller] = float(load)

    def get_loads(self):
        """
        Retourne l'etat courant des charges.
        """

        return self.controller_loads.copy()


class DomainSDNCTRLML:

    def __init__(self, domains, controller_loads=None):
        """
        domains :
        {
            "edge1": ["ryu1", "ryu2"],
            "edge2": ["ryu3", "ryu4"]
        }

        controller_loads :
        charges initiales optionnelles.
        """

        if not domains:
            raise ValueError(
                "Aucun domaine defini."
            )

        self.domains = domains

        self.schedulers = {}

        for domain, controllers in domains.items():

            if not controllers:
                raise ValueError(
                    "Aucun controleur pour le domaine %s"
                    % domain
                )

            if controller_loads is None:

                loads = {
                    controller: 0.0
                    for controller in controllers
                }

            else:

                loads = {
                    controller:
                    float(
                        controller_loads.get(
                            controller,
                            0.0
                        )
                    )
                    for controller in controllers
                }

            self.schedulers[domain] = SDNCTRLML(
                loads
            )

    def select_controller(self, domain):
        """
        Selectionne le controleur le moins charge
        dans le domaine.
        """

        if domain not in self.schedulers:
            raise ValueError(
                "Domaine inconnu : %s" % domain
            )

        return self.schedulers[
            domain
        ].select_controller()

    def update_controller_load(
        self,
        domain,
        controller,
        load
    ):
        """
        Met a jour la charge d'un controleur
        dans un domaine.
        """

        if domain not in self.schedulers:
            raise ValueError(
                "Domaine inconnu : %s" % domain
            )

        self.schedulers[
            domain
        ].update_load(
            controller,
            load
        )

    def get_controller_loads(self, domain):
        """
        Retourne les charges des controleurs
        d'un domaine.
        """

        if domain not in self.schedulers:
            raise ValueError(
                "Domaine inconnu : %s" % domain
            )

        return self.schedulers[
            domain
        ].get_loads()

    def get_all_loads(self):
        """
        Retourne les charges de tous les controleurs.
        """

        result = {}

        for domain, scheduler in self.schedulers.items():

            result[domain] = scheduler.get_loads()

        return result


if __name__ == "__main__":

    domains = {
        "edge1": [
            "ryu1",
            "ryu2"
        ],
        "edge2": [
            "ryu3",
            "ryu4"
        ]
    }

    initial_loads = {
        "ryu1": 20.0,
        "ryu2": 35.0,
        "ryu3": 15.0,
        "ryu4": 40.0
    }

    scheduler = DomainSDNCTRLML(
        domains,
        initial_loads
    )

    print("========== TEST SDNCT-RLML ==========")

    print(
        "Edge 1 -> %s"
        % scheduler.select_controller("edge1")
    )

    print(
        "Edge 2 -> %s"
        % scheduler.select_controller("edge2")
    )

    print(
        "Charges : %s"
        % scheduler.get_all_loads()
    )
