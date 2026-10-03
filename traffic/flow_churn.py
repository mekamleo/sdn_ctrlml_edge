#!/usr/bin/env python3

import subprocess
import time


FLOWS = [
    ("h1", "h2"),
    ("h1", "h3"),
    ("h1", "h4"),
    ("h2", "h5"),
    ("h2", "h6"),
    ("h3", "h7"),
    ("h3", "h8"),
    ("h4", "h9"),
    ("h5", "h10"),
    ("h6", "h11"),
    ("h7", "h12"),
    ("h8", "h1"),
    ("h9", "h2"),
    ("h10", "h3"),
    ("h11", "h4"),
    ("h12", "h5"),
]


def run_flow(src, dst):
    command = [
        "sudo",
        "mnexec",
        "-a",
        get_pid(src),
        "ping",
        "-c",
        "1",
        "-W",
        "1",
        dst
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def get_pid(host):
    result = subprocess.run(
        ["sudo", "mnexec", "-a", "0", "true"],
        capture_output=True
    )

    return "0"


if __name__ == "__main__":

    print("========== FLOW CHURN GENERATOR ==========")

    print("Ce générateur sera intégré à Mininet.")
