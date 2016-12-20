# MOM-Trainer/Recorder

Spezifikationen
*

* starten des Programs über die Konsole
- eingeben von
  - experiment-id (neu)
  - parkour-id (bzw. Auswahl)
  - observer-id (bzw. Auswahl)
  - subject-id (bzw. Auswahl)
(collector-id für Glove-links und Glove-rechts ist fix)
- sind alle Eingaben (korrekt) gemacht worden, so wird ein TRAINSET (mit Datum und Uhrzeit) in der Datenbank erzeugt
- die zum PARKOUR.id gehörenden EXERCISE werden geladen und eine sortierte Liste (sortierung anhand von EXERCISE.step) angezeigt.
Die Items in der Liste entsprechen dem Text aus INSTRUCTION.signal.text
Außerdem wird die Aufforderung "Zum Starten 'Leertaste' drücken" angezeigt
- drückt man die Leertaste so werden DATA der beiden COLLECTOREN (Glove-links und Glove-rechts) in die Datenbank geschrieben
Diese Daten werden mit der "id" der zugehörigen EXERCISE und des zugehörigen COLLECTOR versehen.
Am Bildschirm erscheint nur noch INSTRUCTION.signal.text, der aktuellen EXERCISE.
- _OPTIONAL: Das Programm sendet einen Befehl an den Handschuh, der vor Beginn jeder Aufnahme ein Signal ausgibt (Vibra oder Summer)
  Dieses Signal kann auch (zufällig) zeitversetzt erfolgen, damit es nicht zu einer Standardisierung im Bewegungsablauf kommt.
  siehe EXERCISE.instruction.signal
- drückt man erneut die Leertaste, so werden alle neuen eintreffenden Daten mit der nächsten EXERCISE.id versehen und
dieser INSTRUCTION.signal.text am Bildschirm angezeigt.
- ist der Nutzer am Ende der EXERCISE Liste angekommen, so stoppt die Aufnahme der Daten und man kommt zum Hauptbilschirm zurück
- dort kann man auswählen ob man erneut mit der selben Konfiguration Daten aufnehmen möchte, oder ob man "von vorne einsteigen möchte".


Zusatz:
- mit X kann man einen Parkour beenden, während man aufnimmt. Das TRAINSET wird dann als "fehlerhaft" vermerkt
- nach der Aufnahme eines Parkours kann man mit X den Parkour als "fehlerhaft" vermerken
- nach der Aufnahme eines Parkours wird die ID des entsprechen TRAINSETS angezeigt

- Console:
-- help zeigt was man damit machen kann und was man eingeben muss
-- Bei jeder Exercise steht EXERCISE.name (X/Y)
