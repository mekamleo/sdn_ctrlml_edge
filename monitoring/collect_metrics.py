#!/usr/bin/env python3

import time
import subprocess
import psutil


def get_system_metrics():
    """
    Collecte les métriques système de la machine :
    CPU, mémoire et trafic réseau.
    """

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent

    net = psutil.net_io_counters()
    rx_bytes = net.bytes_recv
    tx_bytes = net.bytes_sent

    return {
        "cpu_percent": cpu,
        "memory_percent": memory,
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes
    }


def get_network_throughput(interval=1):
    """
    Calcule le débit réseau global en Mbps.
    """

    net1 = psutil.net_io_counters()
    time.sleep(interval)
    net2 = psutil.net_io_counters()

    rx_mbps = ((net2.bytes_recv - net1.bytes_recv) * 8) / interval / 1_000_000
    tx_mbps = ((net2.bytes_sent - net1.bytes_sent) * 8) / interval / 1_000_000

    return rx_mbps, tx_mbps


def get_latency(host="10.0.0.2"):
    """
    Mesure la latence vers un hôte Mininet.
    """

    try:
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "1", host],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            if "min/avg/max" in line:
                values = line.split("=")[1].strip().split("/")
                return float(values[1])

    except Exception:
        pass

    return None


def get_active_flows(switch):
    """
    Compte les entrées de flux installées sur un switch OVS.

    Le table-miss (priority=0) n'est pas compté.
    """

    try:
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

    except Exception:
        return 0


def collect_metrics():
    """
    Collecte toutes les métriques.
    """

    print("\n==========================================")
    print("       SDN_CTRLML-Edge - METRICS")
    print("==========================================")

    # CPU et mémoire
    system = get_system_metrics()

    print(f"CPU              : {system['cpu_percent']:.2f} %")
    print(f"Mémoire          : {system['memory_percent']:.2f} %")

    # Débit
    rx, tx = get_network_throughput()

    print(f"Débit entrant    : {rx:.3f} Mbps")
    print(f"Débit sortant    : {tx:.3f} Mbps")

    # Latence
    latency = get_latency()

    if latency is not None:
        print(f"Latence moyenne  : {latency:.3f} ms")
    else:
        print("Latence moyenne  : N/A")

    # Flux actifs
    switches = ["s1", "s2", "s3", "s4", "s5", "s6"]

    print("\nFlux actifs par switch :")

    total_flows = 0

    for switch in switches:
        flows = get_active_flows(switch)
        total_flows += flows
        print(f"  {switch} : {flows}")

    print(f"\nTotal flux actifs : {total_flows}")

    print("==========================================\n")


if __name__ == "__main__":
    collect_metrics()
