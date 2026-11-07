# AI-algoritmes

Deze map bevat de algoritmes die het noodhulpsysteem gebruikt. De algoritmes
werken samen in de simulatie, maar kunnen ook afzonderlijk worden
gebruikt voor tests en vergelijkingen.

## Overzicht van de gegevensstroom

De uitvoering begint in `run.py`. De gegevensstroom is:

```text
Scenarios/ScenarioX/
        |
        v
input_data/scenario_loader.py
        |
        v
Bayesiaanse wegschatting + HMM-verkeersschatting
        |
        v
routekosten
        |
        v
A*-routing
        |
        v
CSP-toewijzing
        |
        v
planvalidatie
        |
        v
plan.json + statistics.txt
```

De simulator voert deze stappen uit op de tijdstippen waarop nieuwe
incidenten bekend worden. Toekomstige incidenten worden dus niet gebruikt bij
een eerdere beslissing.

## `bayesian_road.py`

### Doel

Schat voor iedere gerichte weg de kans op de toestanden:

- `Open`;
- `Congested`;
- `Blocked`.

De berekening gebruikt het bekende weer en de meldingen van burgers, politie en
sensoren.

### Belangrijkste klassen

- `RoadBelief`
  - Bevat de posteriorverdeling van één gerichte weg.
  - Kan de meest waarschijnlijke toestand en de blokkeerkans teruggeven.

- `BayesianRoadEstimator`
  - Voert exacte enumeratie uit over de drie mogelijke wegtoestanden.
  - Gebruikt de formule:

    ```text
    P(status | weer, meldingen)
      ∝ P(status | weer)
        × P(melding1 | status)
        × P(melding2 | status)
        × ...
    ```

### Gebruik

In `simulation.py`:

```python
estimator = BayesianRoadEstimator(
    scenario.road_probabilities,
    scenario.road_reports,
)
beliefs = estimator.estimate_all(scenario.graph.roads)
```

De resulterende beliefs worden doorgegeven aan `RoadCostModel`.

### Aanname

De meldingen worden conditioneel onafhankelijk verondersteld zodra de echte
wegtoestand bekend is. Wegen zonder melding gebruiken het meest voorkomende
weer uit de meldingen als standaardweer.

## `hmm_traffic.py`

### Doel

Schat het verborgen verkeersniveau op iedere gerichte weg. Het verkeersniveau
kan `Low`, `Medium` of `High` zijn. De historische waarnemingen zijn noisy
observaties van deze verborgen toestand.

### Belangrijkste klasse

- `TrafficHMM`
  - `filter(road)` berekent de huidige belief met forward filtering.
  - `predict(road, steps)` voorspelt het verkeer vooruit met de
    overgangsmatrix.
  - `viterbi(road)` berekent de meest waarschijnlijke historische
    toestandsreeks.

### Gebruik

`RoadCostModel` gebruikt `predict(road)` om een verwachte
verkeersvermenigvuldiger te berekenen. `viterbi()` is beschikbaar als
vergelijkings- en analysemethode, maar bepaalt niet de standaardroute.

### Aanname

De observaties uit `observed_traffic.csv` worden als historische gegevens
beschouwd. Omdat geen koppeling met simulatietijd is aangeleverd, wordt na de
laatste observatie één stap vooruit voorspeld.

## `routing.py`

### Doel

Vind een route door de gerichte stadsgraaf. De routekosten combineren:

- normale reistijd `distance / speed`;
- de verwachte Bayesiaanse wegstatus;
- de verwachte HMM-verkeersfactor;
- een grote straf voor de kans dat een weg geblokkeerd is.

### Belangrijkste onderdelen

- `RoadCostModel`
  - `cost(road)` geeft de kost voor route-optimalisatie.
  - `travel_time(road)` geeft de verwachte fysieke reistijd voor
    deadlinecontrole.

- `astar(...)`
  - Gebruikt A* met een Euclidische heuristiek.
  - De heuristiek deelt de Euclidische afstand door de hoogste snelheid in de
    graaf.

- `uniform_cost_search(...)`
  - Gebruikt geen heuristiek.
  - Dient als testorakel om A* te vergelijken.

- `RouteResult`
  - Bevat het pad, de routekost, bereikbaarheid en verwachte reistijd.

### Gebruik

De simulator maakt één `RoadCostModel` en zoekt daarna routes met:

```python
astar(
    scenario.graph,
    start,
    goal,
    cost_model.cost,
    cost_model.travel_time,
)
```

De CSP gebruikt deze routezoeker om alleen haalbare responder-incidentparen
te behouden.

### Belangrijke keuze

De blokkeerkans wordt niet genegeerd. De standaard blokkeerpenalty is `10_000`.
Daardoor kan een route met een iets langere normale reistijd toch veiliger en
goedkoper worden gekozen.

## `allocation.py`

### Doel

Wijs responders toe aan incidenten terwijl operationele voorwaarden worden
gerespecteerd.

### `GreedyAllocator`

Dit is de baseline-methode:

1. sorteer incidenten op prioriteit en deadline;
2. zoek haalbare responders;
3. kies de responder met de vroegste aankomst;
4. gebruik een responder maximaal één keer binnen de batch.

De methode is eenvoudig en snel, maar kan toekomstige combinaties minder goed
inschatten.

### `CspAllocator`

Dit is de hoofdallocator. De methode gebruikt backtracking en
branch-and-bound:

- ieder incident is een variabele;
- een responder of onbehandeld is een mogelijke waarde;
- capabilities, routes en deadlines zijn harde voorwaarden;
- een responder kan binnen één batch niet dubbel worden gebruikt;
- de doelfunctie weegt responstijd volgens incidentprioriteit.

De CSP wordt in `simulation.py` op ieder nieuw beslissingstijdstip opnieuw
uitgevoerd. Daardoor kunnen responders na een eerdere opdracht opnieuw worden
gebruikt zodra hun `available_at`-tijd bereikt is.

## `simulation.py`

### Doel

Voer de volledige simulatie uit.

### `Simulator`

De simulator:

1. berekent alle Bayesiaanse wegbeliefs;
2. maakt het HMM voor historische verkeersobservaties;
3. maakt het gecombineerde routekostenmodel;
4. initialiseert de locaties en beschikbaarheid van responders;
5. verwerkt incidenttijdstippen in chronologische volgorde;
6. plant alleen incidenten die op dat moment al bekend zijn;
7. werkt locatie en beschikbaarheid bij na iedere opdracht;
8. bewaart toegewezen en onbehandelde incidenten.

De uitvoer is een `SimulationResult` met:

- `assignments`;
- `unassigned_incidents`.

## `validator.py`

### Doel

Controleer dat een gegenereerd plan operationeel geldig is voordat het wordt
opgeslagen.

De validator controleert:

- of responders en incidenten bestaan;
- of de responder de vereiste capability bezit;
- of de opdracht niet begint vóór het incident bekend is;
- of de responder beschikbaar is;
- of de aankomstdeadline wordt gehaald;
- of de route bestaat uit geldige gerichte wegen;
- of de route bij de juiste responderlocatie begint;
- of de route bij de incidentlocatie eindigt;
- of een incident niet dubbel toegewezen is;
- of opdrachten van één responder niet overlappen.

De validator levert een lijst met `ValidationIssue`-objecten terug. Een lege
lijst betekent dat er geen fouten zijn gevonden.

## `output.py`

### `PlanWriter`

`PlanWriter` valideert eerst alle assignments. Bij fouten wordt een
`ValueError` opgegooid en wordt geen ongeldig plan geschreven.

Een geldig `plan.json` bevat per assignment:

```json
{
  "responder_id": "R1",
  "incident_id": "I1",
  "path": ["N1", "H1", "N4"],
  "time": 0.0
}
```

### `StatisticsWriter`

`StatisticsWriter` schrijft:

- aantal behandelde incidenten;
- aantal gebruikte responders;
- gemiddelde responstijd;
- percentage deadlines gehaald.

De gemiddelde responstijd is de gemiddelde aankomsttijd minus het
incidenttijdstip en bevat alleen behandelde incidenten. Onbehandelde incidenten
worden niet meegenomen in dat gemiddelde, maar tellen wel als gemiste deadline.
Alle tijdseenheden zijn simulatieseconden.

## Vergelijkingsmethoden

De opdracht vraagt om relevante alternatieven te vergelijken. Daarom bevat de
code ook:

| Hoofdonderdeel | Hoofdmethode | Vergelijkingsmethode |
|---|---|---|
| Wegtoestand | Verwachte Bayesiaanse kost | MAP-wegtoestand via `use_map_status` |
| Verkeer | Forward filtering en voorspelling | Viterbi |
| Routezoeken | A* | Uniform Cost Search |
| Toewijzing | CSP | Greedy |

De vergelijkingsmethoden zijn bedoeld voor tests, analyse en het verslag. De
standaard simulator gebruikt de verwachte Bayesiaanse kosten, HMM-
voorspelling, A* en CSP. De HMM-beliefs blijven beschikbaar voor analyse, maar
worden niet nogmaals als extra reistijdvermenigvuldiger toegepast; zo blijft de
statusfactor binnen de grens van de opgave.
