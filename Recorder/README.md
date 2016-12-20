# MOM-Trainer/Recorder

Dieses Tool nimmt Daten von #MOM/Glove über Blueooth (USB-Modul) entgegen und schreibt diese in eine Datenbank.

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- starten des Programs über die Konsole
  - **_OPTIONAL-0:**
    - startet man das Programm ohne die Angabe von Argumenten oder werden die Argumente nicht
    korrekt angegeben, so gibt das Programm die Aufforderung "Bitte geben Sie: EXPERIMENT.id (neu), OBSERVER.id (neu), SUBJECT.id (neu), PARKOUR.id (vorhanden) als Argumente '--e, --o, --s, --p' an."
  - **_OPTIONAL-1:**
    - das Programm sendet ein Signal (Vibra = Char: '0'-'9', Beep = Char: '*''), um via
    Vibration bzw. aktustischem Signal die "(Bluetooth-)Verbindung" zwischen Handschuh und
    Computer/Programm zu bestätigen.
- folgende Parameter werden als Argumente mit dem Aufruf des Programms mitgegeben
  - EXPERIMENT.id (neu)
  - PARKOUR.id
  - OBSERVER.id
  - SUBJECT.id
- sind alle Eingaben (korrekt) gemacht worden, so wird ein TRAINSET (mit Datum und Uhrzeit) in der Datenbank erzeugt
  - wurde PARKOUR.id nicht in der Datenbank gefunden, so wird der Fehler "[PARKOUR.id] no found." ausgegeben.
- die zum PARKOUR.id gehörenden EXERCISEs werden geladen und eine sortierte Liste (Sortierung anhand von EXERCISE.step) angezeigt.
  - jedes Item der Liste wird als [name = EXERCISE.instruction.signal.text + "-" + EXERCISE.step + "/" + PARKOUR.exercises.all()] angezeigt.
  - Außerdem wird die Aufforderung "Zum Starten 'Leertaste' drücken..." angezeigt
- drückt der Nutzer nun die Leertaste so werden DATA der beiden COLLECTORen (Glove-links und Glove-rechts) (abwechselnd) in die Datenbank geschrieben
  - das TRAINSET wird (abwechselnd) mit DATA aus einem der beiden COLLECTORen erweitert.
    - **Synchronisation:**
      - DATA stammt von je einem Channel vom Bluetooth-Modul des benutzen Computers
      - DATA wird (aktuell) mit 50Hz vom Bluetooth-Modul eines COLLECTORs gesendet. Dieser Wert ist abhängig von der Firmaware des COLLECTORs und kann auf bis zu 100Hz erhöht werden.
      - DATA der beiden Handschuhe liegen auf eigenständigen Zeitachsen
        - CH1: |--x--x--x--x--x--> (Zeitachse-1 mit Raster)
        - CH2: |--x--x--x--x--x--> (Zeitachse-2 mit Raster)
      - pro Zeitachse, soll jede DATA (=x) zu einem virtuellen Raster nur +/-10[ms] abweichen
      - die Zeitachsen müssen, mindestens über den START-Zeitpunkt (=|), synchronisierbar sein
      - DATA der überlagerten Zeitachsen sollen zueinander nur +/-?ms abweichen
  - diese DATA werden mit der zugehörigen EXERCISE.id und des zugehörigen COLLECTOR.id versehen.
    - die COLLECTOR.id entspricht der MAC-Adresse des Bluetooth-Moduls des jeweiligen Handschuhs
  - am Bildschirm erscheint nur noch der [name] der aktuellen EXERCISE.
    - OPTIONAL-1: Die eintreffenden DATA je COLLECTOR werden in je einer Zeile "stehend" angezeigt (siehe ser2file.py). Beispiel:
      - COLLECTOR.id + ": " + DATA.collection.data.rfid + " | " + DATA.collection.data.muscle + ...
  - **_OPTIONAL-2**:
    - Das Programm sendet einen Befehl an den Handschuh, der vor Beginn jeder Aufnahme ein Signal ausgibt (Vibra oder Summer). Dieses Signal kann auch (zufällig) zeitversetzt erfolgen, damit es nicht zu einer Standardisierung im Bewegungsablauf kommt. <-- siehe EXERCISE.instruction.signal
- drückt man die erneut Leertaste, so werden alle neuen eintreffenden DATA mit der nächsten EXERCISE.id versehen und wieder [name] der aktuellen EXERCISE am Bildschirm angezeigt.
  - ist der Nutzer am Ende der EXERCISE Liste angekommen, so stoppt die Aufnahme und die Meldung
  "Parkour durchlaufen. Daten unter TRAINSET [TRAINSET.id] abgespeichert. Drücken Sie 'X' um das TRAINSET als fehlerhaft zu markieren. Drücken Sie 'Leertaste' um das Programm zu beenden."
    - Taste "X" schreibt die zeitliche Differenz zwischen TRAINSET.created und dem Zeitpunkt des Tastendrucks in TRAINSET.status.faulty
- drückt man die Taste "X", so stoppt die Aufnahme und die Meldung
"Parkour abgebrochen. Daten unter TRAINSET [TRAINSET.id] abgespeichert und als fehlerhaft (TRAINSET.status.faulty) markiert. Drücken Sie 'Leertaste' um das Programm zu beenden."
