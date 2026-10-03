#!/usr/bin/env python3

import csv
import datetime
import re
import subprocess
import time


OUTPUT = "results_round_robin.csv"

SWITCHES = ["s1", "s2", "s3", "s4", "s5", "s6"]
CONTROLLERS = ["ryu1", "ryu2", "ryu3", "ryu4"]


def docker_stats():
    """Récupère CPU et mémoire de chaque contrôleur Ryu."""

    cmd = [
        "docker", "stats", "--no-stream",
        "--format",
        "{{.Name}},{{.CPUPerc}},{{.MemPerc}}"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    stats = {}

    for line in result.stdout.splitlines():

        parts = line.strip().split(",")

        if len(parts) != 3:
            continue

        name, cpu, memory = parts

        if name in CONTROLLERS:
            stats[name] = {
                "cpu": float(cpu.replace("%", "")),
                "memory": float(memory.replace("%", ""))
            }

    return stats


def flow_count(switch):
    """Compte les flux OpenFlow hors table-miss."""

    result = subprocess.run(
        ["sudo", "ovs-ofctl", "dump-flows", switch],
        capture_output=True,
        text=True
    )

    count = 0

    for line in result.stdout.splitlines():

        if "priority=0" in line:
            continue

        if "actions=" in line:
            count += 1

    return count


def latency(host1="h1", host2="10.0.0.12"):
    """
    Mesure la latence directement depuis l'espace réseau
    de h1 via mnexec.
    """

    pid_result = subprocess.run(
        ["sudo", "mnexec", "-a", "$(pgrep", "-f", "mininet:h1", ")"],
        capture_output=True,
        text=True
    )

    # Recherche du processus h1 dans les namespaces Mininet
    ps = subprocess.run(
        ["pgrep", "-f", "mininet:h1"],
        capture_output=True,
        text=True
    )

    if ps.returncode != 0:
        return None

    pid = ps.stdout.splitlines()[0].strip()

    result = subprocess.run(
        [
            "sudo", "mnexec", "-a", pid,
            "ping", "-c", "3", "-W", "1", host2
        ],
        capture_output=True,
        text=True
    )

    match = re.search(
        r"rtt .* = [^/]+/([^/]+)/",
        result.stdout
    )

    if match:
        return float(match.group(1))

    return None


def collect():

    timestamp = datetime.datetime.now().isoformat()

    stats = docker_stats()

    flows = {
        switch: flow_count(switch)
        for switch in SWITCHES
    }

    total_flows = sum(flows.values())

    latency_ms = latency()

    row = {
        "timestamp": timestamp,
        "strategy": "round_robin",
        "latency_ms": latency_ms,
        "total_flows": total_flows
    }

    for controller in CONTROLLERS:

        row[f"{controller}_cpu"] = stats.get(
            controller, {}
        ).get("cpu")

        row[f"{controller}_memory"] = stats.get(
            controller, {}
        ).get("memory")

    for switch in SWITCHES:
        row[f"{switch}_flows"] = flows[switch]

    fields = list(row.keys())

    try:
        with open(OUTPUT, "x", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)

    except FileExistsError:

        with open(OUTPUT, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writerow(row)

    print()
    print("==========================================")
    print("     ROUND ROBIN - EXPERIMENT")
    print("==========================================")

    print(f"Latence moyenne : {latency_ms} ms")

    for controller in CONTROLLERS:
        if controller in stats:
            print(
                f"{controller}: "
                f"CPU={stats[controller]['cpu']:.2f}% "
                f"MEM={stats[controller]['memory']:.2f}%"
            )

    print(f"Flux totaux : {total_flows}")

    print(f"CSV : {OUTPUT}")
    print("==========================================")


if __name__ == "__main__":
    collect()
