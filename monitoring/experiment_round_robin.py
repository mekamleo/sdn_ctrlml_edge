import csv
import datetime
import re
import subprocess
import time

OUTPUT = "results_round_robin.csv"

CONTROLLERS = ["ryu1", "ryu2", "ryu3", "ryu4"]
SWITCHES = ["s1", "s2", "s3", "s4", "s5", "s6"]


# ============================================================
# STATISTIQUES CPU / MEMOIRE DES CONTROLEURS
# ============================================================

def get_controller_stats():

    cmd = [
        "docker",
        "stats",
        "--no-stream",
        "--format",
        "{{.Name}},{{.CPUPerc}},{{.MemPerc}}"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=15
    )

    stats = {}

    for line in result.stdout.splitlines():

        parts = line.strip().split(",")

        if len(parts) != 3:
            continue

        name, cpu, memory = parts

        if name in CONTROLLERS:

            try:

                stats[name] = {
                    "cpu": float(
                        cpu.replace("%", "")
                    ),
                    "memory": float(
                        memory.replace("%", "")
                    )
                }

            except ValueError:
                pass

    return stats


# ============================================================
# EVENEMENTS RYU
# ============================================================

def get_controller_events():

    events = {}

    pattern = re.compile(
        r"METRICS Packet-In=(\d+) "
        r"Packet-Out=(\d+) "
        r"Flow-Mod=(\d+)"
    )

    for controller in CONTROLLERS:

        command = [
            "docker",
            "logs",
            controller
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15
        )

        packet_in = 0
        packet_out = 0
        flow_mod = 0

        matches = pattern.findall(
            result.stdout
        )

        if matches:

            last_match = matches[-1]

            packet_in = int(
                last_match[0]
            )

            packet_out = int(
                last_match[1]
            )

            flow_mod = int(
                last_match[2]
            )

        events[controller] = {
            "packet_in": packet_in,
            "packet_out": packet_out,
            "flow_mod": flow_mod
        }

    return events


# ============================================================
# FLUX OPENFLOW
# ============================================================

def get_flows():

    flow_counts = {}

    for switch in SWITCHES:

        cmd = [
            "sudo",
            "ovs-ofctl",
            "-O",
            "OpenFlow13",
            "dump-flows",
            switch
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            print(
                "Erreur dump-flows %s : %s"
                % (
                    switch,
                    result.stderr.strip()
                )
            )

            flow_counts[switch] = 0
            continue

        count = 0

        for line in result.stdout.splitlines():

            line = line.strip()

            if not line:
                continue

            # Ignore l'en-tête de réponse OVS
            if line.startswith("NXST_FLOW"):
                continue

            # Ignore la règle table-miss
            if "priority=0" in line:
                continue

            # Une entrée de flux OpenFlow possède généralement actions=
            if "actions=" in line:
                count += 1

        flow_counts[switch] = count

    total_flows = sum(
        flow_counts.values()
    )

    return total_flows, flow_counts


# ============================================================
# LATENCE
# ============================================================

def parse_latency(output):

    match = re.search(
        r"rtt .* = [0-9.]+/([0-9.]+)/[0-9.]+/[0-9.]+",
        output
    )

    if match:

        return float(
            match.group(1)
        )

    return None


def measure_latency(h1, h12):

    output = h1.cmd(
        f"ping -c 5 -W 1 {h12.IP()}"
    )

    return parse_latency(output)


# ============================================================
# DEBIT IPERF
# ============================================================

def measure_iperf(h1, h12):

    """
    Mesure TCP avec iperf directement
    dans les namespaces Mininet.

    Serveur : h12
    Client  : h1
    Durée   : 10 secondes
    Timeout : 15 secondes
    """

    # Nettoyage

    h1.cmd(
        "killall -q iperf 2>/dev/null"
    )

    h12.cmd(
        "killall -q iperf 2>/dev/null"
    )

    # Serveur

    h12.cmd(
        "iperf -s > /tmp/iperf_server.log 2>&1 &"
    )

    time.sleep(1)

    # Client

    output = h1.cmd(
        f"timeout 15 "
        f"iperf -c {h12.IP()} -t 10"
    )

    # Nettoyage

    h1.cmd(
        "killall -q iperf 2>/dev/null"
    )

    h12.cmd(
        "killall -q iperf 2>/dev/null"
    )

    matches = re.findall(
        r"([0-9.]+)\s+"
        r"(Gbits/sec|Mbits/sec|Kbits/sec)",
        output
    )

    if not matches:

        print(
            "ATTENTION : débit iperf non récupéré."
        )

        print(output)

        return None

    value, unit = matches[-1]

    value = float(value)

    if unit == "Gbits/sec":

        return value * 1000

    if unit == "Kbits/sec":

        return value / 1000

    return value


# ============================================================
# EXECUTION D'UN RUN
# ============================================================

def run_experiment(net, run_number, strategy="round_robin"):

    print()
    print("=" * 60)
    print(
        f"{strategy.replace("_", " ").upper()} - RUN {run_number}"
    )
    print("=" * 60)

    h1 = net["h1"]
    h12 = net["h12"]

    # --------------------------------------------------------
    # MESURE INITIALE DES EVENEMENTS
    # --------------------------------------------------------

    print(
        "[0/4] Lecture des compteurs Ryu..."
    )

    events_before = get_controller_events()

    experiment_start = time.monotonic()

    # --------------------------------------------------------
    # 1. LATENCE
    # --------------------------------------------------------

    print(
        "[1/4] Mesure de latence..."
    )

    latency_ms = measure_latency(
        h1,
        h12
    )

    if latency_ms is not None:

        print(
            f"Latence moyenne : "
            f"{latency_ms:.3f} ms"
        )

    else:

        print(
            "Latence moyenne : N/A"
        )

    # --------------------------------------------------------
    # 2. DEBIT
    # --------------------------------------------------------

    print(
        "[2/4] Mesure du débit iperf..."
    )

    print(
        "      Durée maximale : 15 secondes"
    )

    throughput_mbps = measure_iperf(
        h1,
        h12
    )

    if throughput_mbps is not None:

        print(
            f"Débit : "
            f"{throughput_mbps:.2f} Mbps"
        )

    else:

        print(
            "Débit : N/A"
        )

    # --------------------------------------------------------
    # 3. CONTROLEURS
    # --------------------------------------------------------

    print(
        "[3/4] Mesure des contrôleurs..."
    )

    controller_stats = get_controller_stats()

    for controller in CONTROLLERS:

        if controller in controller_stats:

            cpu = controller_stats[
                controller
            ]["cpu"]

            memory = controller_stats[
                controller
            ]["memory"]

            print(
                f"{controller}: "
                f"CPU={cpu:.2f}% "
                f"MEM={memory:.2f}%"
            )

        else:

            print(
                f"{controller}: N/A"
            )

    # --------------------------------------------------------
    # 4. FLUX
    # --------------------------------------------------------
        # 4. FLUX
    # --------------------------------------------------------

    print("[4/4] Comptage des flux...")

    total_flows, flow_counts = get_flows()

    print(
        "Flux actifs totaux : %d"
        % total_flows
    )

    print(
        "Flux par switch : %s"
        % flow_counts
    )

    # --------------------------------------------------------
    # MESURE FINALE DES EVENEMENTS
    # --------------------------------------------------------

    experiment_duration = (
        time.monotonic()
        - experiment_start
    )

    if experiment_duration <= 0:

        experiment_duration = 1.0

    events_after = get_controller_events()

    print()
    print(
        "========== CHARGE DES CONTROLEURS =========="
    )

    event_rates = {}

    for controller in CONTROLLERS:

        before = events_before.get(
            controller,
            {}
        )

        after = events_after.get(
            controller,
            {}
        )

        packet_in_delta = (
            after.get("packet_in", 0)
            - before.get("packet_in", 0)
        )

        packet_out_delta = (
            after.get("packet_out", 0)
            - before.get("packet_out", 0)
        )

        flow_mod_delta = (
            after.get("flow_mod", 0)
            - before.get("flow_mod", 0)
        )

        packet_in_rate = (
            packet_in_delta
            / experiment_duration
        )

        packet_out_rate = (
            packet_out_delta
            / experiment_duration
        )

        flow_mod_rate = (
            flow_mod_delta
            / experiment_duration
        )

        event_rates[controller] = {
            "packet_in_rate":
                packet_in_rate,

            "packet_out_rate":
                packet_out_rate,

            "flow_mod_rate":
                flow_mod_rate
        }

        print(
            f"{controller}: "
            f"Packet-In={packet_in_rate:.2f}/s | "
            f"Packet-Out={packet_out_rate:.2f}/s | "
            f"Flow-Mod={flow_mod_rate:.2f}/s"
        )

    print(
        "============================================"
    )

    # --------------------------------------------------------
    # RESULTAT
    # --------------------------------------------------------

        # --------------------------------------------------------
    # RESULTAT
    # --------------------------------------------------------

    row = {
        "timestamp":
            datetime.datetime.now().isoformat(),

        "strategy":
            strategy,

        "run":
            run_number,

        "throughput_mbps":
            throughput_mbps,

        "latency_ms":
            latency_ms,

        "total_flows":
            total_flows
    }

    for switch in SWITCHES:

        row[
            "%s_flows" % switch
        ] = flow_counts[switch]

    # --------------------------------------------------------
    # CPU / MEMOIRE
    # --------------------------------------------------------

    for controller in CONTROLLERS:

        row[
            f"{controller}_cpu"
        ] = controller_stats.get(
            controller,
            {}
        ).get(
            "cpu"
        )

        row[
            f"{controller}_memory"
        ] = controller_stats.get(
            controller,
            {}
        ).get(
            "memory"
        )

    # --------------------------------------------------------
    # EVENEMENTS RYU
    # --------------------------------------------------------

    for controller in CONTROLLERS:

        row[
            f"{controller}_packet_in_rate"
        ] = event_rates[
            controller
        ]["packet_in_rate"]

        row[
            f"{controller}_packet_out_rate"
        ] = event_rates[
            controller
        ]["packet_out_rate"]

        row[
            f"{controller}_flow_mod_rate"
        ] = event_rates[
            controller
        ]["flow_mod_rate"]

    # --------------------------------------------------------
    # FLUX PAR SWITCH
    # --------------------------------------------------------

    for switch in SWITCHES:

        
        row[
            "%s_flows" % switch
        ] = flow_counts[switch]
            

    return row


# ============================================================
# EXECUTION DES RUNS
# ============================================================

def run_all(net, repetitions=10, strategy="round_robin", output=OUTPUT):

    rows = []

    for run in range(
        1,
        repetitions + 1
    ):

        row = run_experiment(
            net,
            run,
            strategy
        )

        rows.append(
            row
        )

        print()

        print(
            f"Run {run}/{repetitions} terminé."
        )

        if run < repetitions:

            time.sleep(2)

    # --------------------------------------------------------
    # SAUVEGARDE CSV
    # --------------------------------------------------------

    if not rows:

        print(
            "Aucun résultat à sauvegarder."
        )

        return

    fields = list(
        rows[0].keys()
    )

    with open(
        output,
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print()
    print("=" * 60)
    print(
        f"EXPÉRIMENTATION {strategy.replace("_", " ").upper()} TERMINÉE"
    )
    print("=" * 60)

    print(
        f"Nombre de répétitions : "
        f"{repetitions}"
    )

    print(
        f"Fichier : {output}"
    )

    print("=" * 60)


# ============================================================
# EXECUTION DEPUIS LE CLI MININET
# ============================================================

if __name__ == "__main__":
    print(
        "Erreur : ce script doit être exécuté "
        "depuis la topologie Mininet."
    )
