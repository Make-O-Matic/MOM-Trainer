TODO:
- was ist das beste Datenformat um es der TU Wien zu übergeben?
  - Ordnung nach trainset, gesture, collector?


# MOM-Trainer/Exporter (Python)

Lädt, von MOM-Recorder erstellte Daten aus der Datenbank und wandelt diese in ein .CSV-File um.

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- Nutzer startet das Programm über die Konsole mit diesen Argumenten:
  - TRAINSET.uuid
  - MAPPING.id <-- gibt an in welchem Format die vorhandenen Daten ausgegeben werden sollen. Gibt es da schon Libraries?
- ist ein entsprechendes TRAINSET vorhanden, so wird eine .CSV Datei im vorgegebenen Format erstellt
  - Format der .CSV Datei
- ist kein passendes TRAINSET vorhanden, so wird eine Fehlermeldung ausgegeben
- **_OPTIONAL-x:** - .json Datei wird ausgegeben
