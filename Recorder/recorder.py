#!/usr/bin/env python

import argparse
import datetime
from time import sleep
import uuid
import os, sys, tty, termios
from subprocess import call

from pymongo import MongoClient
from glove import Glove


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)         
    try:             
        tty.setraw(sys.stdin.fileno())             
        ch = sys.stdin.read(1)         
    finally:             
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def beep():
    call(['ogg123', '-q', '/usr/share/sounds/ubuntu/stereo/dialog-information.ogg'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='recorder.')
    parser.add_argument('-l', '--lId', type=str, required=True, help='COLLECTOR.id fuer den linken Handschuh')
    parser.add_argument('-L', '--lMAC', type=str, required=True, help='COLLECTOR.macAddress fuer den linken Handschuh')
    parser.add_argument('-r', '--rId', type=str, required=True, help='COLLECTOR.id fuer den rechten Handschuh')
    parser.add_argument('-R', '--rMAC', type=str, required=True, help='COLLECTOR.macAddress fuer den rechten Handschuh')

    parser.add_argument('-e', '--experiment', type=str, required=True, help='EXPERIMENT.id (neu)')
    parser.add_argument('-o', '--observer', type=str, required=True, help='OBSERVER.id (neu)')
    parser.add_argument('-s', '--subject', type=str, required=True, help='SUBJECT.id (neu)')

    args = parser.parse_args()

    db_client = MongoClient()
    db = db_client['makeomatic']

    recording = [False];
    def isRecording():
        return recording[0]

    lUUID = str(uuid.uuid4())
    rUUID = str(uuid.uuid4())
    gloves = Glove(args.lMAC, args.rMAC, isRecording, lUUID, rUUID)
    gloves.connect()
    for i in [1, 2]:
        if not gloves.connected(i):	
            print("Verbindung zu (mind.) einem COLLECTOR konnte nicht hergestellt werden.")
            print("Bitte pruefen Sie die Bluetooth-Verbindung und starten Sie das Programm erneut.")
            print("Programm mit zwei mal 'STRG+C' beenden.")
            while True:
                sleep(1);
        beep()


    while True:
        args.parcours = raw_input("Valide PARCOURS.id angeben um Aufzeichnung zu starten: ")
        while (True):
            parcours = db.parcours.find_one({"id": args.parcours})
            if (bool(parcours)):
                break
            args.parcours = raw_input("PARCOURS.id '" + args.parcours + "' existiert nicht. Zum Aufzeichnen bitte valide PARKOUR.id angeben: ")

        now = datetime.datetime.utcnow()
        trainsetId = "_TRAINSET" + now.strftime('%d%m%Y%H%M%S')
        print("PARCOURS gefunden. EXERCISEs werden geladen, " + trainsetId + " wird erstellt...\n")
        gloves.setTrainset(trainsetId)
        trainset = db[trainsetId]
        trainset.insert_one(
        {   "_id" : trainsetId,
            "created" : now,
            "experiment" : { "id" : args.experiment },
            "parkour" : { "id" : args.parcours,
                          "observer" : { "id" : args.observer },
                          "subject" : { "id" : args.subject,
                                        "hands" : { "left" : { "uuid" : lUUID,
                                                               "id" : args.lId,
                                                               "macAdress" : args.lMAC },
                                                    "right" : { "uuid" : rUUID,
                                                               "id" : args.rId,
                                                                "macAdress" : args.rMAC } } } } });

        i = 1
        for exercise in parcours["exercises"]:
            mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
            if (bool(mutation) and 'slug' in mutation):
                slug = mutation['slug']
            print(str(i) + "/" + str(len(parcours['exercises'])) + " (" + exercise['mutation']['id'] + ") " + slug)
            i = i + 1

        print("----------------------")
        
        if 'comment' in parcours:
            print "- COMMENT: " + parcours['comment']
        print "- STARTPOSE: " + parcours['pose']['start']
        print "----------------------"
        print "Zum Starten des PARCOURS 'Leertaste' druecken..."
        getch()
        print "----------------------"        
        


        i = 1
        for exercise in parcours['exercises']:
            print "Jetzt EXERCISE " + str(i) + "/" + str(len(parcours['exercises'])) + " (" + exercise['mutation']['id'] + ") ausfuehren"
            mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
            if (bool(mutation) and 'instruction' in mutation):
                print "- INSTRUCTION: " + mutation['instruction']


            if bool(mutation) and 'hands' in mutation:
                hands = mutation['hands']
                text = ""
                if 'left' in hands:
                    if 'host' in hands['left']:
                        text += "-- HOST: " + hands['left']['host']['id'] 
                        if 'spot' in hands['left']['host'] and 'id' in hands['left']['host']['spot']:
                            text += " > " + hands['left']['host']['spot']['id']

                    if 'gesture' in hands['left']:
                        gesture = db.gestures.find_one({'id' : hands['left']['gesture']['id']})
                        text += "\n-- GESTURE: " + gesture['name']

                    print "- linke Hand\n" + text;
                    if 'instruction' in hands['left']:
                        print "-- INSTRUCTION: " + hands['left']['instruction']

                text = ""
                if 'right' in hands:
                    if 'host' in hands['right']:
                        text += "-- HOST: " + hands['right']['host']['id'] 
                        if 'spot' in hands['right']['host'] and 'id' in hands['right']['host']['spot']:
                            text += " > " + hands['right']['host']['spot']['id']

                    if 'gesture' in hands['right']:
                        gesture = db.gestures.find_one({'id' : hands['right']['gesture']['id']})
                        text += "\n-- GESTURE: " + gesture['name']

                    print "- rechte Hand\n" + text
                    if 'instruction' in hands['right']:
                        print "-- INSTRUCTION: " + hands['right']['instruction']

            print "----------------------"
            if exercise['signal']['beep']:
                beep()
            gloves.m_mutation = exercise['mutation']['id']
            gloves.m_mutationIndex = str(mutation['_id'])
            gloves.m_step = i
            i = i + 1
            recording[0] = True

            cmd = ""
            while True:
                cmd = getch()
                if cmd == " ":
                    break
                if cmd == "x":
                    time = gloves.faulty();#args.experiment)
                    trainset2.update_one({ "experiment" : { "id" : args.experiment } },
                                        { "$set" : { "status" : { "faulty" : time } } })
                    break

            recording[0] = False

            if cmd == "x":
                print "PARCOURS abgebrochen. Daten unter TRAINSET " + trainsetId + " abgespeichert und als fehlerhaft (TRAINSET.status.faulty) markiert."
                break

        if cmd != "x":
            print "Aufnahme beendet! PARCOURS " + args.parcours + " erfolgreich durchlaufen."

        trainset.update_one({ "experiment" : { "id" : args.experiment } },
                             { "$set" : { "ended" : datetime.datetime.utcnow() } })

        beep()
        beep()
        print "aufgenommene DATA wurde unter TRAINSET " + trainsetId + " abgespeichert."
        print "Druecken Sie 'Leertaste' um einen neuen PARCOURS zu laden. Programm-Argumente bleiben erhalten!"
        print "Druecken Sie zwei mal 'STRG+C' um das Programm zu beenden. Alle Programm-Argumente werden 'vergessen'!\n"            
        while True:
            cmd = getch()
            if cmd == " ":
                break;
            if ord(cmd) == 3:
               print "Beende..."
               sys.stdout.flush()
               quit(0)
            sleep(1);
	



