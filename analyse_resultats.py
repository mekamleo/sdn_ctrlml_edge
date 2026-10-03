import pandas as pd

files = {
    "Round Robin": "results_round_robin.csv",
    "Weighted Round Robin": "results_weighted_round_robin.csv",
    "ONOS statique": "results_onos_static.csv",
    "SDN_CTRLML": "results_sdn_ctrlml.csv",
}

controllers = ["ryu1", "ryu2", "ryu3", "ryu4"]

for name, file in files.items():

    df = pd.read_csv(file)

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    print("Nombre de runs :", len(df))

    # --------------------------------------------------------
    # CPU ET MEMOIRE
    # --------------------------------------------------------

    print()
    print("--- CPU et mémoire ---")

    for controller in controllers:

        cpu_col = controller + "_cpu"
        memory_col = controller + "_memory"

        if cpu_col in df.columns:

            print(
                f"{controller}: "
                f"CPU moyen={df[cpu_col].mean():.3f}% "
                f"(min={df[cpu_col].min():.3f}, "
                f"max={df[cpu_col].max():.3f})"
            )

        if memory_col in df.columns:

            print(
                f"{controller}: "
                f"Mémoire moyenne={df[memory_col].mean():.3f}% "
                f"(min={df[memory_col].min():.3f}, "
                f"max={df[memory_col].max():.3f})"
            )

    # --------------------------------------------------------
    # EVENEMENTS OPENFLOW
    # --------------------------------------------------------

    print()
    print("--- Événements OpenFlow ---")

    for controller in controllers:

        print(f"{controller}:")

        for event in [
            "packet_in_rate",
            "packet_out_rate",
            "flow_mod_rate"
        ]:

            col = controller + "_" + event

            if col in df.columns:

                print(
                    f"  {event}: "
                    f"{df[col].mean():.3f}/s"
                )

    # --------------------------------------------------------
    # MOYENNE GLOBALE CPU
    # --------------------------------------------------------

    cpu_columns = [
        c for c in df.columns
        if c.endswith("_cpu")
    ]

    if cpu_columns:

        print()
        print(
            "CPU moyen global des contrôleurs : "
            f"{df[cpu_columns].mean(axis=1).mean():.3f}%"
        )

    # --------------------------------------------------------
    # MEMOIRE GLOBALE
    # --------------------------------------------------------

    memory_columns = [
        c for c in df.columns
        if c.endswith("_memory")
    ]

    if memory_columns:

        print(
            "Mémoire moyenne globale des contrôleurs : "
            f"{df[memory_columns].mean(axis=1).mean():.3f}%"
        )
