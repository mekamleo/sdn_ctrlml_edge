import csv, math, random
from pathlib import Path

OUT = Path("dataset/mawi/profiles")
OUT.mkdir(parents=True, exist_ok=True)

random.seed(42)

# Profil temporel synthétique basé sur la variabilité publiée de MAWI.
# Les facteurs conservent la forme temporelle et servent à générer
# différentes intensités de charge dans Mininet.
base = [
    0.55, 0.62, 0.70, 0.83, 0.96,
    1.08, 1.20, 1.35, 1.18, 0.92,
    0.78, 0.65, 0.72, 0.88, 1.05,
    1.42, 1.75, 1.30, 0.98, 0.80,
    0.68, 0.76, 0.91, 1.12, 1.38,
    1.80, 1.55, 1.10, 0.86, 0.72
]

profiles = {
    "mawi_low": 0.25,
    "mawi_medium": 0.50,
    "mawi_high": 1.00,
}

for name, scale in profiles.items():
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s","load_mbps","packets_s","flows_s"])
        for t, factor in enumerate(base):
            mbps = 1000 * factor * scale
            packets = int(mbps * 125)
            flows = max(5, int(factor * 80 * scale))
            w.writerow([t, round(mbps, 2), packets, flows])

# Burst
with open(OUT / "mawi_burst.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_s","load_mbps","packets_s","flows_s"])
    for t, factor in enumerate(base):
        burst = 2.0 if t in [7, 8, 15, 16, 17, 25, 26] else 0.7
        mbps = 1000 * factor * burst
        packets = int(mbps * 125)
        flows = max(5, int(factor * 100 * burst))
        w.writerow([t, round(mbps, 2), packets, flows])

# Imbalanced: Edge1 70%, Edge2 30%
with open(OUT / "mawi_imbalanced.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "time_s","edge1_mbps","edge2_mbps",
        "edge1_flows","edge2_flows"
    ])
    for t, factor in enumerate(base):
        total = 1000 * factor
        e1 = total * 0.70
        e2 = total * 0.30
        f1 = max(5, int(factor * 100 * 0.70))
        f2 = max(5, int(factor * 100 * 0.30))
        w.writerow([t, round(e1,2), round(e2,2), f1, f2])

print("Profils créés :")
for p in sorted(OUT.glob("*.csv")):
    print(" ", p)
