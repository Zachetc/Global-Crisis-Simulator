from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    [sys.executable, "-m", "scripts.run_real_data"],
    [sys.executable, "-m", "scripts.run_network_viz"],
    [sys.executable, "-m", "scripts.run_fragility"],
    [sys.executable, "-m", "scripts.run_fragility_viz"],
]


def main() -> None:
    for cmd in COMMANDS:
        print("\n== Running:", " ".join(cmd))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            raise SystemExit(r.returncode)

    print("\nAll done. Check outputs/ for generated CSV + PNG files.")


if __name__ == "__main__":
    main()
