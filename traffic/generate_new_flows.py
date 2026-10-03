#!/usr/bin/env python3

import subprocess
import time


HOSTS = [
    ("h1", "h2"),
    ("h3", "h4"),
    ("h5", "h6"),
    ("h7", "h8"),
    ("h9", "h10"),
    ("h11", "h12"),
]


def generate_flows(duration=30):

    print("========== GENERATION DE NOUVEAUX FLUX ==========")

    processes = []

    for src, dst in HOSTS:

        command = [
            "sudo",
            "mnexec",
            "-a",
            src,
            "ping",
            "-i",
            "0.01",
            "-w",
            str(duration),
            dst
        ]

        print(
            "%s -> %s"
            % (src, dst)
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        processes.append(process)

    print(
        "\n%d flux générés pendant %d secondes."
        % (len(processes), duration)
    )

    time.sleep(duration)

    for process in processes:
        process.terminate()


if __name__ == "__main__":
    generate_flows(30)
