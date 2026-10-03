#!/usr/bin/env python3

import csv
import json
import os
import re
import subprocess
import time
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT = "results_onos_static.csv"

ONOS_CONTAINER = "onos"
ONOS_USER = "onos"
ONOS_PASSWORD = "rocks"

SWITCHES = [
    "s1",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6"
]

DEVICE_IDS = {
    "s1": "of:0000000000000001",
    "s2": "of:0000000000000002",
    "s3": "of:0000000000000003",
    "s4": "of:0000000000000004",
    "s5": "of:0000000000000005",
    "s6": "of:0000000000000006"
}


# ============================================================
# CPU ET MEMOIRE ONOS
# ============================================================

def get_onos_stats():

    cmd = [
        "docker",
        "stats",
        ONOS_CONTAINER,
        "--no-stream",
        "--format",
        "{{.CPUPerc}},{{.MemPerc}}"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    line = result.stdout.strip()

    if not line:
        return 0.0, 0.0

    cpu_str, memory_str = line.split(",")

    cpu = float(
        cpu_str.replace("%", "")
    )

    memory = float(
        memory_str.replace("%", "")
    )

    return cpu, memory


# ============================================================
# FLOWS ONOS VIA API REST
# ============================================================

def get_onos_flows():

    url = "http://localhost:8181/onos/v1/flows"

    cmd = [
        "docker",
        "exec",
        ONOS_CONTAINER,
        "bash",
        "-lc",
        "curl -s -u %s:%s %s"
        % (
            ONOS_USER,
            ONOS_PASSWORD,
            url
        )
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(
            "Erreur lors de la récupération des flows ONOS :",
            result.stderr
        )

        return 0, {
            switch: 0
            for switch in SWITCHES
        }

    output = result.stdout.strip()

    if not output:

        return 0, {
            switch: 0
            for switch in SWITCHES
        }

    try:

        data = json.loads(output)

    except json.JSONDecodeError:

        print(
            "Erreur : réponse JSON ONOS invalide."
        )

        return 0, {
            switch: 0
            for switch in SWITCHES
        }

    flows = data.get(
        "flows",
        []
    )

    flow_counts = {
        switch: 0
        for switch in SWITCHES
    }

    for flow in flows:

        if flow.get("state") != "ADDED":
            continue

        device_id = flow.get(
            "deviceId",
            ""
        )

        for switch, expected_device in DEVICE_IDS.items():

            if device_id == expected_device:

                flow_counts[switch] += 1
                break

    total_flows = sum(
        flow_counts.values()
    )

    return total_flows, flow_counts


# ============================================================
# LATENCE
# ============================================================

def parse_latency(output):

    match = re.search(
        r"=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+",
        output
    )

    if match:

        return float(
            match.group(1)
        )

    return 0.0


def measure_latency(net):

    h1 = net["h1"]
    h12 = net["h12"]

    result = h1.cmd(
        "ping -c 5 -W 1 %s"
        % h12.IP()
    )

    return parse_latency(result)


# ============================================================
# DEBIT IPERF
# ============================================================

def measure_iperf(net):

    h1 = net["h1"]
    h12 = net["h12"]

    h12.cmd(
        "pkill -f iperf 2>/dev/null"
    )

    h1.cmd(
        "pkill -f iperf 2>/dev/null"
    )

    h12.cmd(
        "iperf -s -p 5001 "
        "> /tmp/iperf_server.log 2>&1 &"
    )

    time.sleep(1)

    result = h1.cmd(
        "timeout 15 "
        "iperf -c %s "
        "-p 5001 "
        "-t 10"
        % h12.IP()
    )

    h12.cmd(
        "pkill -f iperf 2>/dev/null"
    )

    h1.cmd(
        "pkill -f iperf 2>/dev/null"
    )

    match = re.search(
        r"([\d.]+)\s+"
        r"(Gbits/sec|Mbits/sec|Kbits/sec)",
        result
    )

    if not match:
        return 0.0

    value = float(
        match.group(1)
    )

    unit = match.group(2)

    if unit == "Gbits/sec":
        return value * 1000

    if unit == "Mbits/sec":
        return value

    if unit == "Kbits/sec":
        return value / 1000

    return 0.0


# ============================================================
# EXECUTION D'UN RUN
# ============================================================

def run_experiment(net, run_number):

    print()
    print(
        "========== ONOS RUN %d =========="
        % run_number
    )

    latency = measure_latency(net)

    throughput = measure_iperf(net)

    cpu, memory = get_onos_stats()

    total_flows, switch_flows = get_onos_flows()

    row = {
        "timestamp":
            datetime.now().isoformat(),

        "strategy":
            "onos_static",

        "run":
            run_number,

        "throughput_mbps":
            throughput,

        "latency_ms":
            latency,

        "total_flows":
            total_flows,

        "onos_cpu":
            cpu,

        "onos_memory":
            memory
    }

    for switch in SWITCHES:

        row[
            "%s_flows" % switch
        ] = switch_flows[switch]

    print(
        "Throughput : %.2f Mbps"
        % throughput
    )

    print(
        "Latency    : %.3f ms"
        % latency
    )

    print(
        "Flows      : %d"
        % total_flows
    )

    print(
        "ONOS CPU   : %.3f%%"
        % cpu
    )

    print(
        "ONOS Memory: %.3f%%"
        % memory
    )

    print(
        "Flows par switch : %s"
        % switch_flows
    )

    return row


# ============================================================
# EXECUTION DES RUNS
# ============================================================

def run_all(net, repetitions=10):

    fieldnames = [
        "timestamp",
        "strategy",
        "run",
        "throughput_mbps",
        "latency_ms",
        "total_flows",
        "onos_cpu",
        "onos_memory",
        "s1_flows",
        "s2_flows",
        "s3_flows",
        "s4_flows",
        "s5_flows",
        "s6_flows"
    ]

    output_path = os.path.join(
        os.getcwd(),
        OUTPUT
    )

    with open(
        output_path,
        "w",
        newline=""
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for run in range(
            1,
            repetitions + 1
        ):

            row = run_experiment(
                net,
                run
            )

            writer.writerow(
                row
            )

            csvfile.flush()

            if run < repetitions:

                time.sleep(2)

    print()
    print(
        "Résultats sauvegardés dans : %s"
        % output_path
    )


# ============================================================
# EXECUTION DIRECTE
# ============================================================

if __name__ == "__main__":

    print(
        "Erreur : ce script doit être exécuté "
        "depuis une topologie Mininet."
    )
