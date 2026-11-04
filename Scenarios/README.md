# Scenario data

Each scenario folder is a complete input dataset.

## Units

- Coordinates and road `distance`: metres.
- Road `speed`: metres per second (30 on main roads, 15 on secondary roads).
- All simulation times and durations: seconds, including incident timestamps, arrival deadlines, handling durations, responder availability, and assignment start times. Fractional seconds are allowed.

## Interpretation

- Road reports are available at time 0. Weather is local to the reported road.
- Traffic observations are historical and available before time 0. `observation_nr` orders a separate sequence for each directed road; it is not a simulation timestamp.
- Traffic levels (Low/Medium/High) differ from road statuses (Open/Congested/Blocked). Define and justify how traffic affects your planning; no fixed traffic multipliers are prescribed.

Document and defend any additional assumptions.

## Code structure

The Python domain model lives next to the scenario data. Related classes are
grouped into thematic modules so the later AI components can use small, testable
interfaces:

- `city_graph.py` and `road.py` model the directed city graph and roads.
- `responder.py` contains responders, responder types, and availability.
- `incident.py` contains incidents and incident priorities.
- `road.py` contains roads, road reports, road states, weather, and road CPTs.
- `traffic.py` contains traffic levels, observations, and traffic CPTs.
- `scenario_data.py` is the complete in-memory scenario.
- `scenario_loader.py` reads all CSV and JSON files and validates node/road references.

The original focused module names remain as compatibility wrappers that re-export
the classes from the grouped modules. This means existing imports continue to
work while new code can import related concepts together.

Run the current loader smoke test from the repository root with:

```text
python -m Scenarios.main
```

The loader currently only creates the domain model. Search, Bayesian road
reasoning, constraint-based allocation, and HMM traffic inference can be added
without changing the scenario file format.
