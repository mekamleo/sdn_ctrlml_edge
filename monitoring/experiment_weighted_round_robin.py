import csv
import datetime
import re
import subprocess
import time

OUTPUT = "results_weighted_round_robin.csv"

CONTROLLERS = ["ryu1", "ryu2", "ryu3", "ryu4"]
SWITCHES = ["s1", "s2", "s3", "s4", "s5", "s6"]


def get_controller_stats():
    cmd = [
        "docker", "stats", "--no-stream",
        "--format", "{{.Name}},{{.CPUPerc}},{{.MemPerc}}"
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
                    "cpu": float(cpu.replace("%", "")),
                    "memory": float(memory.replace("%", ""))
                }
            except ValueError:
                pass

    return stats


def get_flows():
    flows = {}

    for switch in SWITCHES:
        try:
            result = subprocess.run(
                ["sudo", "ovs-ofctl", "dump-flows", switch],
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            flows[switch] = 0
            continue

        count = 0

        for line in result.stdout.splitlines():
            if "priority=0" not in line and "actions=" in line:
                count += 1

        flows[switch] = count

    return flows


def parse_latency(output):
    match = re.search(
        r"rtt .* = [0-9.]+/([0-9.]+)/[0-9.]+/[0-9.]+",
        output
    )

    if match:
        return float(match.group(1))

    return None


def measure_latency(h1, h12):
    output = h1.cmd(
        f"ping -c 5 -W 1 {h12.IP()}"
    )

    return parse_latency(output)


def measure_iperf(h1, h12):

    h1.cmd("killall -q iperf 2>/dev/null")
    h12.cmd("killall -q iperf 2>/dev/null")

    h12.cmd(
        "iperf -s > /tmp/iperf_server.log 2>&1 &"
    )

    time.sleep(1)

    output = h1.cmd(
        f"timeout 15 iperf -c {h12.IP()} -t 10"
    )

    h1.cmd("killall -q iperf 2>/dev/null")
    h12.cmd("killall -q iperf 2>/dev/null")

    matches = re.findall(
        r"([0-9.]+)\s+(Gbits/sec|Mbits/sec|Kbits/sec)",
        output
    )

    if not matches:
        print("ATTENTION : débit iperf non récupéré.")
        print(output)
        return None

    value, unit = matches[-1]
    value = float(value)

    if unit == "Gbits/sec":
        return value * 1000

    if unit == "Kbits/sec":
        return value / 1000

    return value


def run_experiment(net, run_number):

    print()
    print("=" * 60)
    print(f"WEIGHTED ROUND ROBIN - RUN {run_number}")
    print("=" * 60)

    h1 = net["h1"]
    h12 = net["h12"]

    print("[1/4] Mesure de latence...")

    latency_ms = measure_latency(h1, h12)

    if latency_ms is not None:
        print(f"Latence moyenne : {latency_ms:.3f} ms")
    else:
        print("Latence moyenne : N/A")

    print("[2/4] Mesure du débit iperf...")
    print("      Durée maximale : 15 secondes")

    throughput_mbps = measure_iperf(h1, h12)

    if throughput_mbps is not None:
        print(f"Débit : {throughput_mbps:.2f} Mbps")
    else:
        print("Débit : N/A")

    print("[3/4] Mesure des contrôleurs...")

    controller_stats = get_controller_stats()

    for controller in CONTROLLERS:
        if controller in controller_stats:
            cpu = controller_stats[controller]["cpu"]
            memory = controller_stats[controller]["memory"]

            print(
                f"{controller}: "
                f"CPU={cpu:.2f}% "
                f"MEM={memory:.2f}%"
            )
        else:
            print(f"{controller}: N/A")

    print("[4/4] Comptage des flux...")

    flows = get_flows()
    total_flows = sum(flows.values())

    for switch in SWITCHES:
        print(f"{switch}: {flows[switch]} flux")

    print(f"Total : {total_flows}")

    row = {
        "timestamp": datetime.datetime.now().isoformat(),
        "strategy": "weighted_round_robin",
        "run": run_number,
        "throughput_mbps": throughput_mbps,
        "latency_ms": latency_ms,
        "total_flows": total_flows
    }

    for controller in CONTROLLERS:
        row[f"{controller}_cpu"] = controller_stats.get(
            controller, {}
        ).get("cpu")

        row[f"{controller}_memory"] = controller_stats.get(
            controller, {}
        ).get("memory")

    for switch in SWITCHES:
        row[f"{switch}_flows"] = flows[switch]

    return row


def run_all(net, repetitions=10):

    rows = []

    for run in range(1, repetitions + 1):

        row = run_experiment(net, run)

        rows.append(row)

        print()
        print(f"Run {run}/{repetitions} terminé.")

        if run < repetitions:
            time.sleep(2)

    if not rows:
        print("Aucun résultat à sauvegarder.")
        return

    fields = list(rows[0].keys())

    with open(
        OUTPUT,
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("=" * 60)
    print("EXPÉRIMENTATION WEIGHTED ROUND ROBIN TERMINÉE")
    print("=" * 60)
    print(f"Nombre de répétitions : {repetitions}")
    print(f"Fichier : {OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    print("Erreur : ce script doit être exécuté depuis une topologie Mininet.")
