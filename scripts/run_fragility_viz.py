from __future__ import annotations

import os
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = "outputs"
IN_CSV = os.path.join(OUTDIR, "sample_fragility_edges.csv")
OUT_PNG = os.path.join(OUTDIR, "sample_fragility_top10.png")


def main() -> None:
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(f"Missing {IN_CSV}. Run: python -m scripts.run_fragility")

    df = pd.read_csv(IN_CSV)
    for c in ["u", "v", "delta"]:
        if c not in df.columns:
            raise ValueError(f"{IN_CSV} missing required column '{c}'")

    df["delta"] = pd.to_numeric(df["delta"], errors="coerce").fillna(0.0)

    top = df.sort_values("delta", ascending=False).head(10).copy()
    top["edge"] = top["u"].astype(str) + " → " + top["v"].astype(str)

    # Reverse for nicer horizontal bar ordering (largest at top)
    top = top.iloc[::-1]

    plt.figure(figsize=(11, 6))
    plt.barh(top["edge"], top["delta"])
    plt.xlabel("Increase in average shortage (Δ)")
    plt.title("Top 10 Most Fragile Trade Links")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    plt.close()

    print("Saved fragility chart to:", OUT_PNG)


if __name__ == "__main__":
    main()
