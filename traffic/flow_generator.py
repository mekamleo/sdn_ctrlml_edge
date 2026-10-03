#!/usr/bin/env python3

import random
import subprocess
import time


HOSTS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "h7", "h8", "h9", "h10", "h11", "h12"
]


def generate_flows(duration=30, rate=20):

    end_time = time.time() + duration

    count = 0

    while time.time() < end_time:

        src, dst = random.sample(HOSTS, 2)

        port = random.randint(10000, 60000)

        command = (
            "nc -z -w 1 %s %d"
            % (dst, port)
        )

        # Cette fonction est destinée à être
        # appelée depuis la CLI Mininet.
        print(
            "%s -> %s:%d"
            % (src, dst, port)
        )

        count += 1

        time.sleep(1.0 / rate)

    print(
        "Flux générés : %d"
        % count
    )


if __name__ == "__main__":
    generate_flows()
