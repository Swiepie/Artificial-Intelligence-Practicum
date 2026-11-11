# Algoritmes

Deze map bevat de algoritmes die het noodhulpsysteem gebruikt om wegen,
verkeer, routes en de inzet van responders te beoordelen. Samen bepalen ze
welke responder naar welk incident wordt gestuurd en leveren ze de resultaten
voor de simulatie.

## Overzicht

De algoritmes werken in de volgende volgorde:

1. De toestand van wegen en het verkeersniveau worden geschat.
2. Op basis daarvan worden geschikte routes en reistijden bepaald.
3. Responders worden aan incidenten toegewezen.
4. Het gemaakte plan wordt gecontroleerd.
5. Het plan en de statistieken worden als uitvoer opgeslagen.

De simulatie herhaalt dit proces wanneer nieuwe incidenten bekend worden.
Incidenten die nog niet zijn gemeld, worden niet meegenomen in een eerdere
beslissing.

## Wegtoestand en verkeer

- `bayesian_road.py` schat per gerichte weg hoe waarschijnlijk de toestanden
  `Open`, `Congested` en `Blocked` zijn. Hiervoor worden het weer en meldingen
  van burgers, politie en sensoren gebruikt.
- `hmm_traffic.py` schat per gerichte weg het verkeersniveau `Low`, `Medium` of
  `High` op basis van historische verkeerswaarnemingen. De schatting wordt ook
  gebruikt om het verwachte verkeer tijdens een route te voorspellen.

## Routes

- `routing.py` bepaalt routes door de gerichte stadsgraaf.
- Bij de routekeuze wordt rekening gehouden met de normale reistijd, de
  geschatte wegtoestand, het verwachte verkeer en de kans op een geblokkeerde
  weg.
- Het algoritme kan aangeven of een bestemming bereikbaar is en hoe lang de
  verwachte route duurt.

## Toewijzing van responders

- `allocation.py` koppelt beschikbare responders aan incidenten.
- Daarbij wordt rekening gehouden met prioriteit, benodigde capabilities,
  bereikbaarheid, beschikbaarheid en deadlines.
- De hoofdtoewijzing zoekt naar een combinatie die incidenten zo goed mogelijk
  en met zo kort mogelijke responstijden behandelt.
- Er is ook een eenvoudigere greedy-methode aanwezig als
  vergelijkingsmethode.

## Simulatie

- `simulation.py` voert de volledige planning door.
- De simulator verwerkt incidenten chronologisch, houdt de locatie en
  beschikbaarheid van responders bij en bewaart behandelde en onbehandelde
  incidenten.
- De resultaten van de simulatie worden gebruikt om een plan en statistieken
  te maken.

## Controle en uitvoer

- `validator.py` controleert of een plan uitvoerbaar en geldig is. Hierbij
  worden onder andere responders, capabilities, routes, deadlines,
  beschikbaarheid en overlappende opdrachten gecontroleerd.
- `output.py` schrijft geldige plannen en de bijbehorende statistieken weg.
  De statistieken bevatten onder andere het aantal behandelde incidenten, het
  aantal ingezette responders, de gemiddelde responstijd en het percentage
  behaalde deadlines.
- `independent_validator.py` bevat een afzonderlijke controle van de
  belangrijkste plangegevens en resultaten.

## Overige bestanden

- `constants.py` bevat gedeelde instellingen voor de algoritmes.
- `__init__.py` maakt van deze map een Python-module.
