# MOM-Trainer/Recorder

Dieses Tool nimmt Daten von #MOM/Glove über Blueooth (USB-Modul) entgegen und schreibt diese in eine Datenbank.

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- [Nutzer öffnet Console]>
  - [Nutzer startet Programm]>
    - Argumente:
        + --l %TRAINSET.subject.hands.left.id%
        + --lMac %TRAINSET.subject.hands.left.macAdress%
        + --r %TRAINSET.subject.hands.right.id%
        + --rMac %TRAINSET.subject.hands.right.macAdress%
        + --e EXPERIMENT.id
        + --o OBSERVER.id
        + --s SUBJECT.id
      - [ohne oder falsche Argumente]>
        - COLLECTOR-LEFT = TRAINSET.subject.hands.left
        - COLLECTOR-RIGHT = TRAINSET.subject.hands.right
        + ["--l" leer] > Meldung("Bitte geben Sie die COLLECTOR.id für den linken Handschuh an")
        + ["--lMac" leer] > Meldung("Bitte geben Sie die COLLECTOR.macAdress für den linken Handschuh an")
        + ["--r" leer] > Meldung("Bitte geben Sie die COLLECTOR.id für den rechten Handschuh an")
        + ["--rMac" leer] > Meldung("Bitte geben Sie die COLLECTOR.macAdress für den rechten Handschuh an")
        + ["--e" leer] > Meldung("Bitte geben Sie eine EXPERIMENT.id an.")
        + ["--o" leer] > Meldung("Bitte geben Sie Ihre OBSERVER.id an.")
        + ["--s" leer] > Meldung("Bitte geben Sie die SUBJECT.id an.")
    - Programm überprüft ob eine Bluetooth-Verbindung hergestellt werden kann und ob Daten ankommen
      - [Verbindung zu mind. einem Handschuh nicht möglich]>
        - Meldung("Verbindung zu (mind.) einem COLLECTOR konnte nicht hergestellt werden.")
        - Meldung ("Bitte prüfen Sie die Bluetooth-Verbindung und starten Sie das Programm erneut.")
        - Meldung ("Programm mit 'STRG+C' beenden.")
          - [Nutzer drückt 'STRG+C']> (PROGRAMMENDE)
      - [Verbindung zu einem Handschuh hergestellt]> (BEEP)
        <-- Steuersignal "*" wird an (verbundenen) Handschuh gesendet. Dies löst ein Piepsen am Handschuh aus
    - (JUMP001)[Verbindung zu beiden Handschuhen hergestellt]>
      - Meldung("Valide PARKOUR.id angeben um Aufzeichnung zu starten.")
      - [PARKOUR.id nicht in Datenbank]>
        - Meldung("PARKOUR.id '%PARKOUR.id%' existiert nicht. Zum Aufzeichnen bitte valide PARKOUR.id angeben.")
      - [PARKOUR.id in der Datenbank gefunden]>
        - Meldung("PARKOUR gefunden. EXERCISEs werden geladen, TRAINSET wird erstellt...")
        - TRAINSET wird in der Datenbank erzeugt
          - TRAINSET.created.date = TODAY()
          - TRAINSET.created.time = NOW()
          - TRAINSET.experiment.id = EXPERIMENT.id
          - TRAINSET.parkour.id = PARKOUR.id
          - TRAINSET.parkour.observer.id = OBSERVER.id
          - TRAINSET.parkour.subject.id = SUBJECT.id
          - TRAINSET.parkour.subject.hands.left.id = COLLECTOR-LEFT.id
          - TRAINSET.parkour.subject.hands.left.macAdress = COLLECTOR-LEFT.macAdress
          - TRAINSET.parkour.subject.hands.left.uuid = uuid()
          - TRAINSET.parkour.subject.hands.right.id = COLLECTOR-RIGHT.id
          - TRAINSET.parkour.subject.hands.right.macAdress = COLLECTOR-RIGHT.macAdress
          - TRAINSET.parkour.subject.hands.right.uuid = uuid()
        - die zur PARKOUR.id gehörenden EXERCISEs werden geladen und eine sortierte Liste angezeigt.
          <-- (Sortierung anhand von Reihenfolge in PARKOUR.exercises[])
          - jedes Item der Liste wird als %name% angezeigt.
            + MUTATION = MUTATION[EXERCISE.mutation.id]
            + index = %posInArray(PARKOUR.exercises[])%/%all(PARKOUR.exercises)%
            + name = %index%: %MUTATION.id%
          - [Am Ende der Liste]>
            - Meldung("----------------------")
            - Meldung("%PARKOUR.comment%")
            - Meldung("Startposition: %PARKOUR.pose.start%")
            - Meldung("----------------------")
            - Meldung("Zum Starten des PARKOURs 'Leertaste' drücken...")
      - (JUMP002)[Nutzer drückt Leertaste]>
        - Meldung("Jetzt EXERCISE-%index% ausführen")
        - [IF(MUTATION.hasAttribute("instruction")]> Meldung("%MUTATION.instruction%")
        - [IF(MUTATION.hasAttribute("hands.left.instruction")]> Meldung("%MUTATION.hands.left.instruction%")
        - [IF(MUTATION.hasAttribute("hands.right.instruction")]> Meldung("%MUTATION.hands.right.instruction%")
        - Meldung("-------------------------------")
        - [IF(EXERCISE.signal.beep == true)]> (BEEP) wird an "aktiven Handschuh" gesendet. Handschuh piept kurz
          + aktiver Handschuh = IF(MUTATION[EXERCISE.mutation.id].hands.hasAttribute("left")) UND/ODER IF(MUTATION[EXERCISE.mutation.id].hands.hasAttribute("right"))
        - DATA (= collection[i]) der beiden COLLECTORen (Glove-links und Glove-rechts) (abwechselnd) in die Datenbank (TRAINSET.collection[].add()) geschrieben
        - das TRAINSET wird (abwechselnd) mit DATA aus je einem der beiden COLLECTORen erweitert.
          - **Synchronisation:**
            - DATA stammt von je einem Channel vom Bluetooth-Modul des benutzen Computers
            - DATA wird (aktuell) mit 50Hz vom Bluetooth-Modul eines COLLECTORs gesendet. Dieser Wert ist abhängig von der Firmaware des COLLECTORs und kann auf bis zu 100Hz erhöht werden.
            - DATA der beiden Handschuhe liegen auf eigenständigen Zeitachsen
              - CH1: |--x--x--x--x--x--> (Zeitachse-1 mit Raster)
              - CH2: |--x--x--x--x--x--> (Zeitachse-2 mit Raster)
            - pro Zeitachse, soll jede DATA (=x) zu einem virtuellen Raster nur +/-10[ms] abweichen
            - die Zeitachsen müssen, mindestens über den START-Zeitpunkt (=|), synchronisierbar sein
            - DATA der überlagerten Zeitachsen sollen zueinander nur +/-?ms abweichen
        - diese DATA werden mit folgenden Attributen ergänzt:
          - DATA.collector.uuid = TRAINSET.parkour.subject.hands.right.uuid ODER TRAINSET.parkour.subject.hands.left.uuid
          - DATA.mutation.uuid = MUTATION[EXERCISE.mutation.id]
          - DATA.step =  posInArray(PARKOUR.exercises[]) <-- Position der aktuellen EXERCISE im geladenen PARKOUR
        - [Nutzer drückt Taste "X"]>
          - Meldung("Parkour abgebrochen und Daten als fehlerhaft (TRAINSET.status.faulty) markiert.")
            - zeitliche Differenz zwischen TRAINSET.created und dem Zeitpunkt des Tastendrucks wird in TRAINSET.status.faulty
          - goto (JUMP004)
      - [Nutzer drückt (erneut) Leertaste]> Verhalten gleich wie bei (JUMP002)
      - [Ende der EXERCISE Liste]>
        - Meldung("Aufnahme beendet! PARKOUR %PARKOUR.id% erfolgreich durchlaufen.")
        - [JUMP004]>
          - "Aufnahme" stoppt. Es wird keine weitere DATA in das aktuelle TRAINSET geschrieben, die Datenverbindung zu den beiden Handschuhen bleibt aber Aufrecht.
          - (BEEP)(BEEP) <-- Steuersignal(e) "*,*" werden an den "aktiven" Handschuh gesendet
          - Meldung("aufgenommene DATA wurde unter TRAINSET %TRAINSET.uuid% abgespeichert.")
          - Meldung("Drücken Sie 'Leertaste' um einen neuen PARKOUR zu laden. Programm-Argumente bleiben erhalten!")
          - Meldung("Drücken Sie 'STRG+C' um das Programm zu beenden. Alle Programm-Argumente werden 'vergessen'!")
        - [Nutzer drückt Taste "Leertaste"]> Programm springt zurück zu (JUMP001). Alle Parameter (z.B.: EXPERIMENT.id,...) bleiben für weitere PARKOURe erhalten.
      - [Nutzer drückt Taste "STRG+C"]> (PROGRAMMENDE)
