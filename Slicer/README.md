# MOM-Slicer
Eine Sammlung von Tools zur Aufbereitung von Videodaten, die parallel zur Aufnahme durch #MOM-Trainer/Recorder entstanden sind.

Um die Anwendung und Funktion der Tools zu verstehen, haben wir eine Liste der verwendeten [Begriffe/Vokabeln](https://workflowy.com/s/qrLIZmQBRp) (in Workflowy, read-only) zusammengestellt.

##Features:
- einlesen eines .MP4 files dessen Länge (mind.) vor der Aufnahme des ersten TRAINSET beginnt und über die
Aufnahme des letzten TRAINSET hinaus geht
  - auslesen des Beginn und Endzeitpunkts je Video
- Zugriff auf die Datenbank aller TRAINSETs, PARCOURS, MUTATIONs, GESTUREs, ...
    - Suche nach passenden TRAINSETs anhand von Start- und Endzeitpunkt je Video bzw. je TRAINSET
      - auslesen der EXPERIMENT.id, SUBJECT.id, OBSERVER.id TRAINSET.id aus dem TRAINSET
- hinzufügen eines Untertitels mit FFMPEG anhand von TRAINSET.created/TRAINSET.ended
  - Untertitel = TRAINSET.id(EXPERIMENT.id/SUBJECT.id/OBSERVER.id)>PARKOUR.id/STEP, MUTATION(GESTURE/HOST) <-- nur mal die rechte Hand!
    - Untertitel: http://stackoverflow.com/questions/8672809/use-ffmpeg-to-add-text-subtitles
    - Text in Bildbereich einfügen: https://lists.ffmpeg.org/pipermail/ffmpeg-user/2014-June/021915.html
- zerschneiden des gesamten Videos in Stücke je PARKOUR.id
  geht mit FFMPEG - http://superuser.com/questions/138331/using-ffmpeg-to-cut-up-video

 //Ideen
