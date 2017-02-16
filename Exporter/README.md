# MOM-Trainer/Exporter (Python)

Lädt, von MOM-Recorder erstellte Daten aus der Datenbank und wandelt diese in ein beliebiges Ausgabeformat, abhängig vom MAPPING um.

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- Nutzer startet das Programm über die Konsole mit diesen Argumenten:
  - TRAINSET.uuid [MongoDB:uuid]
  - MAPPING.id: [alphanumericKey | "trainset.tmpl.csv"]
- ist ein entsprechendes TRAINSET in der Datenbank vorhanden, so wird eine Datei im vorgegebenen Format [.csv] erstellt und der Dateiname der Datei ausgegeben. Das Programm wird mit STRG+C oder durch schließen der Konsole beendet
- ist kein entsprechendes TRAINSET vorhanden, so wird eine Fehlermeldung ausgegeben und
der Benutzer wird solange aufgefordert erneut eine TRAINSET.uuid einzugeben bis ein entsprechendes TRAINSET vorhanden ist



Export
- alle TRAINSETS von EXPERIMENT.id
- TRAINSETs von dieser GESTURE
- alle TRAINSETS zu einem PARKOUR.id
- alle TRAINSETS zu einem HOST (kommt mind. einmal vor)

expoter.py -e E001 -s S001 -t TRAINSET000111


- Start: Summe aller verfügbaren TRAINSETs
- Filter: (durchsucht alle TRAINSETs nach den Filterkriterien und gibt ein TRAINSET aus, sofern die Summe aller Kriterien mind. einmal erfüllt wurden)
  - g > GESTURE.id [, GESTURE.id]
  - h > HOST.id [, HOST.id]
  - s > SPOT.id <-- macht ohne -h kaum Sinn
  - o > OBSERVER.id
  - e > EXPERIMENT.id
  - s > SUBJECT.id
  - m > MUTATION.id
  - c > COLLECTOR.id
  - p > PARCOURS.id
  - t > TRAINSET.id [, TRAINSET.id]
- hands > left|right|both
- faulty wird grundsätzlich ausgeschlossen!

Achtung!
Aktuell ist der stamp.microSeconds die vergangene Zeit seit Programmstart und nicht seit Beginn: PARCOURS
die Ordnung sollte eher sein stamp.microSeconds[i] = stamp.microSeconds[i] - tamp.microSeconds[0]

Werden mehrere TRAINSETs gefunden, die die angegeben Kriterien erfüllen, so werden diese chronologisch aneinander gereiht und als ein .CSV File ausgegeben.

TRAINSET.id | EXPERIMENT.id | SUBJECT.id | OBSERVER.id | COLLECTOR.id | hand [right/left] | TIMESTAMP(seit Programmstart!) | DATA | PARCOURS.id | STEP | MUTATION.id | isActive | HOST.id | SPOT.id | GESTURE.id
