# MOM-Trainer/Exporter (Python)

Lädt, von MOM-Recorder erstellte TRAINSETs, anhand von Filter-Kriterien, aus der Datenbank und wandelt diese in eine .CSV Datei um.  

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- **[Nutzer öffnet Console]>**
  - **[Nutzer startet Programm "exporter.py"]>**
    - Argument(e)
      + -connect > {"server": SERVER, "port": PORT, "db":DATABASE, user":USER, "password":PASSWORD}
        - SERVER z.B.: "localhost"
        - PORT z.B.: "27017"
        - DATABASE z.B.: "makeomatic"
        - USER z.B.: "exportUser" (read-only)
        - PASSWORD z.B.: "export1234"
        - **[ohne oder falsches Argument]**>
          - Meldung("Es konnte keine Verbindung zur Datenbank hergestellt werden.")
      + -hand > left | right | both (= Standard)
    - optionale Argumente (= Kriterien): <-- jedes angegebene Kriterium muss in mind. einem TRAINSET mind. einmal vorkommen
      + --g > GESTURE.id [, GESTURE.id]
      + --h > HOST.id [, HOST.id]
      + --o > OBSERVER.id [, OBSERVER.id]
      + --e > EXPERIMENT.id [, EXPERIMENT.id]
      + --s > SUBJECT.id [, SUBJECT.id]
      + --m > MUTATION.id [, MUTATION.id]
      + --c > COLLECTOR.id [, COLLECTOR.id]
      + --p > PARCOURS.id [, PARCOURS.id]
      + --t > TRAINSET.id [, TRAINSET.id]
      - **[keine Argument(e) angegeben]**>
        - goto (JUMP001)
      - **[Argument(e) angegeben]**>
        - goto (JUMP001)
  - **[JUMP001]>**
    - **[kein TRAINSETs erfüllt die Kriterien]>**
      - Meldung("keine Daten zum Export verfügbar.")
      - (PROGRAMMENDE)
    - **[mind. ein TRAINSET erfüllt die Kriterien]>**
      - Export aller TRAINSETs aus DATABASE (für Spalten siehe [trainset.tmpl.csv](/tree/Templates/trainset.tmpl.csv))
        - in chronologischer Reihenfolge: TRAINSET.created
        - Ausschlusskriterium: TRAINSET.hasAttribute("status.faulty")
      - Auswahl wird als .CSV exportiert
      - Meldung("Daten wurden in %Filename% exportiert.") <-- TIME: Zeitzone für Wien
        - Filename = "EXPORT_%DATETIME%_%[Kriterien]%.CSV"
        - Dateiname z.B.:
          - EXPORT_14022017163906_G14-G10_H001-H005-H100_Clemens_Andreas_M508-M101_C03-C04_P105-P110-P204.csv
          - EXPORT_14022017163906__TRAINSET14022017163905-_TRAINSET14022017163906.csv
          - EXPORT_14022017163906_Andreas.csv
          - Export_14022017163906_G10.csv
          - Export_14022017163906_H001.csv
      - (PROGRAMMENDE)
