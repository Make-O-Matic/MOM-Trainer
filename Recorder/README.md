# MOM-Trainer/Recorder

Dieses Tool nimmt Daten von #MOM/Glove über Blueooth (USB-Modul) entgegen und schreibt diese in eine Datenbank.

## Spezifikationen
[Vokabeln](https://workflowy.com/s/qrLIZmQBRp) in Workflowy (read-only)

Programmablauf:
- [Nutzer öffnet Console]>
  - [Nutzer startet Programm]>
    - Argumente:
      ..* --l %TRAINSET.subject.hands.left.id%
      ..* --lMac %TRAINSET.subject.hands.left.macAdress%
      ..* --r %TRAINSET.subject.hands.right.id%
      ..* --rMac %TRAINSET.subject.hands.right.macAdress%
      ..* --e EXPERIMENT.id
      ..* --o OBSERVER.id
      ..* --s SUBJECT.id
      - [ohne oder falsche Argumente]>
        - COLLECTOR-LEFT = TRAINSET.subject.hands.left
        - COLLECTOR-RIGHT = TRAINSET.subject.hands.right
        + --l > Meldung("Bitte geben Sie die %COLLECTOR-LEFT.id% für den linken Handschuh an")
        + --lMac > Meldung("Bitte geben Sie die COLLECTOR-LEFT.macAdress für den linken Handschuh an")
        + --r > Meldung("Bitte geben Sie die %COLLECTOR-RIGHT.id%für den rechten Handschuh an")
        + --rMac > Meldung("Bitte geben Sie die COLLECTOR-RIGHT.macAdress für den rechten Handschuh an")
        + --e > Meldung("Bitte geben Sie eine EXPERIMENT.id an.")
        + --o > Meldung("Bitte geben Sie Ihre OBSERVER.id an.")
        + --s > Meldung("Bitte geben Sie die SUBJECT.id an.")
    - Programm überprüft ob eine Bluetooth-Verbindung hergestellt werden kann und ob Daten ankommen
      - [Verbindung zu mind. einem Handschuh nicht möglich]>
        - Meldung("Verbindung zu (mind.) einem Handschuh konnte nicht hergestellt werden.")
        - Meldung ("Bitte prüfen Sie die Bluetooth-Verbindung und starten Sie das Programm erneut.")
        - Meldung ("Mit 'STRG+C' beenden.")
      - Nutzer drückt STRG+C > (PROGRAMMENDE)
      - [Verbindung zu einem Handschuh hergestellt]> (BEEP) = Steuersignal "*" wird an (verbundenen) Handschuh gesendet. Dies löst ein Piepsen am Handschuh aus
    - (JUMP001)[Verbindung zu beiden Handschuhen hergestellt]> Meldung("Zum Aufzeichnen bitte valide PARKOUR.id angeben.")
      - [PARKOUR.id nicht in Datenbank]> Meldung("%PARKOUR.id% existiert nicht. Zum Aufzeichnen bitte valide PARKOUR.id angeben.")
      - [PARKOUR.id in der Datenbank gefunden]>
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
        - die zum PARKOUR.id gehörenden EXERCISEs werden geladen und eine sortierte Liste (Sortierung anhand von Reihenfolge in PARKOUR.exercises[]) angezeigt.
          - jedes Item der Liste wird als %name% angezeigt.
            + index = %posInArray(PARKOUR.exercises[])%/%all(PARKOUR.exercises)%
            + name = %MUTATION[EXERCISE.mutation.id].id% - %index%
          - [nach dem letzten Item]> Meldung("Zum Starten 'Leertaste' drücken...")
      - (JUMP002)[Nutzer drückt Leertaste]>
        - Meldung(%index%: %instructionCommon%, %instructionLeft%, %instructionRight%)
          + MUTATION = MUTATION[EXERCISE.mutation.id]
          + instructionCommon = IF(MUTATION.hasAttribute("instruction")){MUTATION.instruction}ELSE{""}
          + instructionLeft = IF(MUTATION.hasAttribute("hands.left.instruction")){MUTATION.hands.left.instruction}ELSE{""}
          + instructionRight = IF(MUTATION.hasAttribute("hands.right.instruction")){MUTATION.hands.right.instruction}ELSE{""}
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
        - Meldung("Parkour erfolgreich durchlaufen.")
        - [JUMP004]>
          - "Aufnahme" stoppt. Es wird keine weitere DATA in das aktuelle TRAINSET geschrieben, die Datenverbindung zu den beiden Handschuhen bleibt aber Aufrecht.
          - (BEEP)(BEEP) <-- Steuersignal(e) "*,*" werden an den "aktiven" Handschuh gesendet
          - Meldung("gesammelte Daten wurden unter TRAINSET %TRAINSET.uuid% abgespeichert.")
          - Meldung("Drücken Sie 'Leertaste' um einen neuen PARKOUR zu laden. Alle Eingaben bleiben erhatlen!")
          - Meldung("Drücken Sie 'STRG+C' um das Programm zu beenden. Alle Eingaben werden 'vergessen'!")
        - [Nutzer drückt Taste "Leertaste"]> Programm springt zurück zu (JUMP001). Alle Parameter (z.B.: EXPERIMENT.id,...) bleiben für weitere PARKOURe erhalten.
      - [Nutzer drückt Taste "STRG+C"]> (PROGRAMMENDE)
