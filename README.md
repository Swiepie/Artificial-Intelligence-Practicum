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

Zonder argument worden alle drie de scenario's uitgevoerd:

```text
python run.py
```

Dit voert achtereenvolgens `Scenario1`, `Scenario2` en `Scenario3` uit. Elke
uitvoering schrijft `plan.json` en `statistics.txt` naar de bijbehorende map
onder `Scenarios/`. Het plan wordt tijdens de simulatie gemaakt: incidenten
worden pas beschikbaar zodra hun tijdstip bereikt is. Extra scenariomappen kunnen op naam
worden uitgevoerd.

Een andere uitvoermap kan expliciet worden gekozen:

```text
python run.py Scenario1 --output-dir results/Scenario1
```

Tests draaien met `python -m pytest -q`.

## Gevoeligheidsanalyse

Met `sensitivity.py` kan worden onderzocht hoe de planner reageert op
verschillende modelinstellingen. Het script voert voor elke combinatie een
volledige simulatie uit en schrijft de resultaten standaard naar
`results/sensitivity.md`:

```text
python sensitivity.py
```

Standaard worden `Scenario1`, `Scenario2` en `Scenario3` getest met
blokkeerstraf `0`, `50`, `200`, `1000` en `10000`. Voor iedere straf worden
zowel HMM-verkeer aan en uit als beide statusmodellen (`verwacht` en `MAP`)
uitgevoerd. De voortgang wordt ook in de terminal weergegeven.

Je kunt de scenario's, straffen en het uitvoerbestand aanpassen:

```text
python sensitivity.py --scenarios Scenario1 Scenario3
python sensitivity.py --penalties 0 200 10000
python sensitivity.py --output results/mijn-sensitivity.md
```

In de gegenereerde tabel is elke rij één volledige simulatie. De kolommen
betekenen:

- `scenario`: het gebruikte scenario.
- `HMM-verkeer`: of de HMM-verkeersvoorspelling als extra route-evidence is
  gebruikt.
- `blokkeerstraf`: de straf voor wegen die volgens het model geblokkeerd zijn.
- `status`: `verwacht` gebruikt de verwachte wegstatus; `MAP` gebruikt alleen
  de meest waarschijnlijke status.
- `behandeld`: aantal toegewezen incidenten ten opzichte van het totale aantal
  incidenten.
- `responders`: het aantal verschillende hulpverleners dat is ingezet.
- `gem. responstijd (s)`: de gemiddelde responstijd in seconden, alleen over
  behandelde incidenten.
- `deadlines (%)`: het percentage van alle incidenten dat binnen de deadline
  is bereikt; een onbehandeld incident telt hierbij als niet gehaald.
- `onbehandeld`: de identificatiecodes van incidenten waarvoor geen toewijzing
  is gevonden.

De standaardconfiguratie van het systeem komt overeen met `HMM-verkeer = aan`,
`blokkeerstraf = 10000` en `status = verwacht`.

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

