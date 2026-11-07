# Artificial Intelligence Practicum

## Het systeem uitvoeren

Het project gebruikt Python en `pytest` voor de tests. Installeer de afhankelijkheid
met `python -m pip install -r requirements.txt`. Voer vanuit de
hoofdmap een van de beschikbare scenario's uit:

```text
python run.py Scenario1
python run.py Scenario2
python run.py Scenario3
```

Zonder argument wordt `Scenario3` uitgevoerd:

```text
python run.py
```

Elke uitvoering schrijft `plan.json` en `statistics.txt` naar de gekozen map
onder `Scenarios/`. Het plan wordt tijdens de simulatie gemaakt: incidenten
worden pas beschikbaar zodra hun tijdstip bereikt is. Extra scenariomappen kunnen op naam
worden uitgevoerd.

Een andere uitvoermap kan expliciet worden gekozen:

```text
python run.py Scenario1 --output-dir results/Scenario1
```

Tests draaien met `python -m pytest -q`.

## Aannames

- Voor wegen zonder melding wordt het meest voorkomende gemelde weer gebruikt;
  `weather_prior` wordt als brondata bewaard maar niet opnieuw gemengd.
- De verwachte statusfactor is conditioneel op doorgang: Open is 1.0 en
  Congested 1.5. Wegen met `P(Blocked) > 0.5` zijn voor routing onbruikbaar.
- Verkeersobservaties worden HMM-filtered, maar vermenigvuldigen de reistijd
  niet extra; de opgave begrenst de statusfactor op maximaal 1.5.
- Toewijzingen worden vastgelegd op het beslismoment (`decided_at`) en daarna
  niet herpland.
- De CSP-skipkost is `gewicht × 10.000`; dat blijft hoger dan de onderzochte
  maximale responstijd van 6.000 seconden.

## Mappenstructuur

```text
run.py                    # officieel startpunt
Scenarios/
  Scenario1/              # invoerbestanden en gegenereerde uitvoer
  Scenario2/
  Scenario3/
input_data/               # domeinklassen en scenariolader
algorithms/               # Bayes, HMM, zoeken, CSP, validatie en uitvoer
```

Nieuwe scenario's horen in `Scenarios/<scenario-naam>/` en moeten dezelfde
bestandsnamen bevatten als de meegeleverde scenario's. Een aparte `main.py` is
niet nodig.

## Implementatie

Het systeem combineert exacte Bayesiaanse inferentie van wegtoestanden, HMM-
filtering van verkeer, A*-routing, CSP-toewijzing en een onafhankelijke
planningsvalidator. Uniform Cost Search, Viterbi, de meest waarschijnlijke
wegtoestand en greedy-toewijzing zijn als vergelijkings- of basismethoden
geïmplementeerd. Zie `input_data/README.md` en `AI.txt` voor de aannames,
algoritmekeuzes en bekende beperkingen.

De validator controleert gerichte routes, routebegin- en eindpunten,
vaardigheden, beschikbaarheid, incidenttijdstippen, deadlines, dubbele
toewijzingen en overlappende opdrachten. Onbehandelde incidenten worden niet
meegenomen in de gemiddelde responstijd en tellen als gemiste deadlines.