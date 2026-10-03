#!/usr/bin/env python3

import re
import subprocess
import time


class ControllerWorkloadMonitor:

    def __init__(self, controllers):
        if not controllers:
            raise ValueError(
                "Aucun controleur defini."
            )

        self.controllers = controllers

    # ============================================================
    # CPU
    # ============================================================

    def get_cpu_load(self, controller):
        """
        Retourne l'utilisation CPU du conteneur Docker.
        """

        command = [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{.CPUPerc}}",
            controller
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Impossible de lire le CPU de %s"
                % controller
            )

        value = result.stdout.strip()

        if value.endswith("%"):
            value = value[:-1]

        return float(value)

    # ============================================================
    # MEMOIRE
    # ============================================================

    def get_memory_load(self, controller):
        """
        Retourne l'utilisation mémoire du conteneur Docker.
        """

        command = [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{.MemPerc}}",
            controller
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Impossible de lire la memoire de %s"
                % controller
            )

        value = result.stdout.strip()

        if value.endswith("%"):
            value = value[:-1]

        return float(value)

    # ============================================================
    # EVENEMENTS RYU
    # ============================================================

    def get_controller_events(self, controller):
        """
        Lit les derniers compteurs Packet-In,
        Packet-Out et Flow-Mod dans les logs Ryu.
        """

        command = [
            "docker",
            "logs",
            controller
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Impossible de lire les logs de %s"
                % controller
            )

        matches = re.findall(
            r"METRICS Packet-In=(\d+) "
            r"Packet-Out=(\d+) "
            r"Flow-Mod=(\d+)",
            result.stdout
        )

        if not matches:
            return {
                "packet_in": 0,
                "packet_out": 0,
                "flow_mod": 0
            }

        packet_in, packet_out, flow_mod = matches[-1]

        return {
            "packet_in": int(packet_in),
            "packet_out": int(packet_out),
            "flow_mod": int(flow_mod)
        }

    # ============================================================
    # CHARGE COMPLETE D'UN CONTROLEUR
    # ============================================================

    def get_workload(self, controller):
        """
        Retourne l'état actuel du contrôleur.
        """

        events = self.get_controller_events(
            controller
        )

        return {
            "cpu": self.get_cpu_load(
                controller
            ),

            "memory": self.get_memory_load(
                controller
            ),

            "packet_in": events["packet_in"],
            "packet_out": events["packet_out"],
            "flow_mod": events["flow_mod"]
        }

    # ============================================================
    # CHARGE DE TOUS LES CONTROLEURS
    # ============================================================

    def get_all_workloads(self):
        """
        Retourne les mesures de tous les contrôleurs.
        """

        workloads = {}

        for controller in self.controllers:

            workloads[controller] = (
                self.get_workload(
                    controller
                )
            )

        return workloads

    # ============================================================
    # MESURE DES TAUX
    # ============================================================

    def measure_rates(self, interval=10):
        """
        Mesure les taux d'événements pendant
        une période donnée.

        Les taux sont exprimés en événements/seconde.
        """

        if interval <= 0:
            raise ValueError(
                "L'intervalle doit etre > 0."
            )

        # --------------------------------------------------------
        # Première mesure
        # --------------------------------------------------------

        first = self.get_all_workloads()

        print(
            "\n========== PREMIERE MESURE =========="
        )

        for controller in self.controllers:

            data = first[controller]

            print(
                "%s -> CPU=%.2f%% | MEM=%.2f%% | "
                "Packet-In=%d | Packet-Out=%d | "
                "Flow-Mod=%d"
                % (
                    controller,
                    data["cpu"],
                    data["memory"],
                    data["packet_in"],
                    data["packet_out"],
                    data["flow_mod"]
                )
            )

        print(
            "\nAttente de %d secondes..."
            % interval
        )

        # --------------------------------------------------------
        # Attente
        # --------------------------------------------------------

        time.sleep(interval)

        # --------------------------------------------------------
        # Deuxième mesure
        # --------------------------------------------------------

        second = self.get_all_workloads()

        # --------------------------------------------------------
        # Calcul des taux
        # --------------------------------------------------------

        rates = {}

        for controller in self.controllers:

            first_data = first[controller]
            second_data = second[controller]

            packet_in_delta = (
                second_data["packet_in"]
                - first_data["packet_in"]
            )

            packet_out_delta = (
                second_data["packet_out"]
                - first_data["packet_out"]
            )

            flow_mod_delta = (
                second_data["flow_mod"]
                - first_data["flow_mod"]
            )

            rates[controller] = {

                # --------------------------------------------
                # Ressources
                # --------------------------------------------

                "cpu": second_data["cpu"],

                "memory": second_data["memory"],

                # --------------------------------------------
                # Taux d'événements
                # --------------------------------------------

                "packet_in_rate": (
                    packet_in_delta / interval
                ),

                "packet_out_rate": (
                    packet_out_delta / interval
                ),

                "flow_mod_rate": (
                    flow_mod_delta / interval
                ),

                # --------------------------------------------
                # Compteurs totaux
                # --------------------------------------------

                "packet_in_total": (
                    second_data["packet_in"]
                ),

                "packet_out_total": (
                    second_data["packet_out"]
                ),

                "flow_mod_total": (
                    second_data["flow_mod"]
                ),

                # --------------------------------------------
                # Variations pendant la fenêtre
                # --------------------------------------------

                "packet_in_delta": (
                    packet_in_delta
                ),

                "packet_out_delta": (
                    packet_out_delta
                ),

                "flow_mod_delta": (
                    flow_mod_delta
                )
            }

        return rates

    # ============================================================
    # AFFICHAGE
    # ============================================================

    def print_rates(self, rates):
        """
        Affiche les taux de charge de manière lisible.
        """

        print(
            "\n========== TAUX D'EVENEMENTS =========="
        )

        for controller, data in rates.items():

            print(
                "%s -> "
                "CPU=%.2f%% | "
                "MEM=%.2f%% | "
                "Packet-In=%.2f/s | "
                "Packet-Out=%.2f/s | "
                "Flow-Mod=%.2f/s"
                % (
                    controller,
                    data["cpu"],
                    data["memory"],
                    data["packet_in_rate"],
                    data["packet_out_rate"],
                    data["flow_mod_rate"]
                )
            )

        print(
            "========================================\n"
        )
    # ============================================================
    # MESURE SYNCHRONISEE AVEC UNE CHARGE
    # ============================================================

    def measure_during_workload(
        self,
        workload_function,
        duration=20,
        interval=2
    ):
        """
        Mesure la charge des contrôleurs pendant toute la durée
        du trafic.

        Le trafic et la mesure sont exécutés simultanément.
        """

        import time
        import threading

        print(
            "\n========== DEBUT DE LA FORTE DEMANDE =========="
        )

        # Etat initial des compteurs.
        previous = self.get_all_workloads()

        # Lancement du trafic.
        workload_thread = threading.Thread(
            target=workload_function,
            daemon=True
        )

        workload_thread.start()

        measurements = []

        start_time = time.time()

        number_of_windows = int(duration / interval)

        for window_id in range(number_of_windows):

            window_start = time.time()

            # Attendre exactement une fenêtre.
            time.sleep(interval)

            current = self.get_all_workloads()

            elapsed_window = time.time() - window_start

            window = {}

            for controller in self.controllers:

                previous_data = previous[controller]
                current_data = current[controller]

                packet_in_delta = (
                    current_data["packet_in"]
                    - previous_data["packet_in"]
                )

                packet_out_delta = (
                    current_data["packet_out"]
                    - previous_data["packet_out"]
                )

                flow_mod_delta = (
                    current_data["flow_mod"]
                    - previous_data["flow_mod"]
                )

                window[controller] = {
                    "cpu": current_data["cpu"],
                    "memory": current_data["memory"],

                    "packet_in_rate":
                        packet_in_delta / elapsed_window,

                    "packet_out_rate":
                        packet_out_delta / elapsed_window,

                    "flow_mod_rate":
                        flow_mod_delta / elapsed_window,

                    "packet_in_total":
                        current_data["packet_in"],

                    "packet_out_total":
                        current_data["packet_out"],

                    "flow_mod_total":
                        current_data["flow_mod"],

                    "packet_in_delta":
                        packet_in_delta,

                    "packet_out_delta":
                        packet_out_delta,

                    "flow_mod_delta":
                        flow_mod_delta
                }

            measurements.append(window)

            print(
                f"\n--- Fenêtre {window_id + 1}/"
                f"{number_of_windows} ---"
            )

            for controller in self.controllers:

                data = window[controller]

                print(
                    f"{controller} -> "
                    f"CPU={data['cpu']:.2f}% | "
                    f"MEM={data['memory']:.2f}% | "
                    f"Packet-In="
                    f"{data['packet_in_rate']:.2f}/s | "
                    f"Packet-Out="
                    f"{data['packet_out_rate']:.2f}/s | "
                    f"Flow-Mod="
                    f"{data['flow_mod_rate']:.2f}/s"
                )

            previous = current

        # Le trafic doit être terminé avant de continuer.
        workload_thread.join(timeout=5)

        total_elapsed = time.time() - start_time

        print(
            "\n========== FIN DE LA FORTE DEMANDE =========="
        )

        print(
            f"Duree reelle mesuree : "
            f"{total_elapsed:.2f} secondes"
        )

        return measurements

