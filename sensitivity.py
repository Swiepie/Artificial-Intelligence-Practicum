"""Genereer results/sensitivity.md: gevoeligheid voor HMM, blokkeerstraf en MAP.

Gebruik (vanuit de hoofdmap):
    python sensitivity.py
    python sensitivity.py --penalties 0 200 10000 --scenarios Scenario1 Scenario2
    python sensitivity.py --output results/sensitivity.md

Elke rij is één volledige simulatie met een andere modelinstelling.
De statistieken worden berekend uit de toewijzingen van die simulatie zelf,
met dezelfde definities als statistics.txt:
  * gemiddelde responstijd: alleen over behandelde incidenten;
  * deadlines gehaald: gehaald / ALLE incidenten (onbehandeld telt als gemist).
"""

import argparse
import time
from pathlib import Path

from algorithms.simulation import Simulator
from input_data.scenario_loader import ScenarioLoader

DEFAULT_SCENARIOS = ("Scenario1", "Scenario2", "Scenario3")
DEFAULT_PENALTIES = (0.0, 50.0, 200.0, 1000.0, 10000.0)


def evaluate(scenario, *, traffic: bool, penalty: float, map_status: bool) -> dict:
    """Draai de simulator met één instelling en geef de kerncijfers terug."""
    result = Simulator().run(
        scenario,
        traffic_enabled=traffic,
        blocked_penalty=penalty,
        use_map_status=map_status,
    )
    assignments = result.assignments
    handled = len(assignments)
    total = len(scenario.incidents)
    met = sum(a.arrival_time <= a.incident.deadline for a in assignments)
    average = sum(a.response_time for a in assignments) / handled if handled else 0.0
    return {
        "handled": handled,
        "total": total,
        "responders": len({a.responder.responder_id for a in assignments}),
        "average": average,
        "met_pct": 100.0 * met / total if total else 100.0,
        "unassigned": ", ".join(
            sorted(i.incident_id for i in result.unassigned_incidents)
        ),
    }


def build_table(root: Path, scenario_names, penalties) -> str:
    """Voer alle combinaties uit en geef een markdown-tabel terug."""
    lines = [
        "# Gevoeligheidsanalyse",
        "",
        "Gegenereerd door `python sensitivity.py`. Elke rij is een volledige simulatie.",
        "",
        "| scenario | HMM-verkeer | blokkeerstraf | status | behandeld | responders "
        "| gem. responstijd (s) | deadlines (%) | onbehandeld |",
        "|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for name in scenario_names:
        scenario = ScenarioLoader().load(root / "Scenarios" / name)
        for traffic in (False, True):
            for penalty in penalties:
                for map_status in (False, True):
                    started = time.perf_counter()
                    row = evaluate(
                        scenario,
                        traffic=traffic,
                        penalty=penalty,
                        map_status=map_status,
                    )
                    lines.append(
                        f"| {name} | {'aan' if traffic else 'uit'} | {penalty:g} "
                        f"| {'MAP' if map_status else 'verwacht'} "
                        f"| {row['handled']}/{row['total']} | {row['responders']} "
                        f"| {row['average']:.1f} | {row['met_pct']:.1f} "
                        f"| {row['unassigned'] or '-'} |"
                    )
                    print(
                        f"{name} HMM={'aan' if traffic else 'uit'} "
                        f"lambda={penalty:g} {'MAP' if map_status else 'verwacht'}: "
                        f"{row['handled']}/{row['total']} "
                        f"({time.perf_counter() - started:.1f}s)",
                        flush=True,
                    )
    lines += [
        "",
        "Standaardconfiguratie: HMM aan, blokkeerstraf 10000, status verwacht.",
        "`status = MAP` gebruikt alleen de meest waarschijnlijke wegtoestand.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genereer sensitivity.md.")
    parser.add_argument("--scenarios", nargs="+", default=list(DEFAULT_SCENARIOS))
    parser.add_argument(
        "--penalties", nargs="+", type=float, default=list(DEFAULT_PENALTIES)
    )
    parser.add_argument("--output", type=Path, default=Path("results/sensitivity.md"))
    args = parser.parse_args()
    root = Path(__file__).parent
    table = build_table(root, args.scenarios, args.penalties)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(table, encoding="utf-8", newline="\n")
    print(f"Geschreven naar {output}")


if __name__ == "__main__":
    main()