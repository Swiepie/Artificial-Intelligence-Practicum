# Invoerdata en domeinmodel

Elke scenariomap bevat een volledige invoerdataset.

## Eenheden

- Coördinaten en `distance` van wegen: meter.
- `speed` van wegen: meter per seconde (30 op hoofdwegen en 15 op secundaire
  wegen).
- Alle simulatietijden en tijdsduurwaarden zijn seconden. Dit geldt voor
  incidenttijdstippen, aankomstdeadlines, afhandeltijden, beschikbaarheid van
  responders en starttijden van opdrachten. Kommagetallen zijn toegestaan.

## Interpretatie

- Wegmeldingen zijn beschikbaar op tijdstip 0. Het weer geldt lokaal voor de
  gemelde weg.
- Verkeerswaarnemingen zijn historische gegevens die vóór tijdstip 0 beschikbaar
  zijn. `observation_nr` ordent een aparte reeks voor elke gerichte weg; het is
  geen tijdstip in de simulatie.
- Verkeersniveaus (`Low`, `Medium`, `High`) verschillen van wegtoestanden
  (`Open`, `Congested`, `Blocked`). Beschrijf en verantwoord hoe verkeer de
  planning beïnvloedt; er zijn geen vaste verkeersvermenigvuldigers opgelegd.


## Codestructuur

Deze map bevat de klassen en de lader die nodig zijn om de scenario-
invoerbestanden te lezen. Verwante klassen zijn gegroepeerd in thematische
modules:

- `city_graph.py` en `road.py` modelleren de gerichte stadsgraaf en wegen.
- `responder.py` bevat responders, respondertypes en beschikbaarheid.
- `incident.py` bevat incidenten en incidentprioriteiten.
- `road.py` bevat wegen, wegmeldingen, wegtoestanden, weer en weg-CPT's.
- `traffic.py` bevat verkeersniveaus, waarnemingen en verkeers-CPT's.
- `scenario_data.py` bevat het volledige scenario in het geheugen.
- `scenario_loader.py` leest alle CSV- en JSON-bestanden en controleert
  verwijzingen naar knopen en wegen.

