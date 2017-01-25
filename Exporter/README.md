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
