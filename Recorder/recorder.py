#!/usr/bin/env python

import argparse
import datetime
import threading
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
    
    
def handText(db, hands, side, description):
    text = ''
    if side in hands:
        hand = hands[side]
        if 'host' in hand:
            text += '-- HOST: ' + hand['host']['id'] 
            if 'spot' in hand['host'] and 'id' in hand['host']['spot']:
                text += ' > ' + hand['host']['spot']['id']

        if 'gesture' in hand:
            gesture = db.gestures.find_one({'id' : hand['gesture']['id']})
            text += '\n-- GESTURE: "' + gesture['name'] + '"'

        print '- ' + description + ' Hand\n' + text;
        if 'instruction' in hand:
            print '-- INSTRUCTION: "' + hand['instruction'] + '"'
            

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

    db_client = MongoClient("mongodb://TestDBAccessForGil:Ikemigoku754@ds145639.mlab.com:45639/mom-trainer_cloud")
    db_client2 = MongoClient()
    db2 = db_client2['makeomatic']
    db = db_client['mom-trainer_cloud']
    
    gloves = []
    
    def setConnected(state):
		if state > gloves[0].state:
			beep()
		gloves[0].state = state	
		if state == 3:
			gloves[0].bothConnected.set()		

    def isRecording():
        return gloves[0].recording

    lUUID = str(uuid.uuid4())
    rUUID = str(uuid.uuid4())
    
    try:
        gloves = [Glove(args.lMAC, args.rMAC, setConnected, isRecording, lUUID, rUUID)]
        gloves[0].state = 0
        gloves[0].recording = False
        gloves[0].bothConnected = threading.Event()
        gloves[0].connect()
        gloves[0].bothConnected.wait()
    except RuntimeError:
            print('Verbindung zu (mind.) einem COLLECTOR konnte nicht hergestellt werden.')
            print('Bitte pruefen Sie die Bluetooth-Verbindung und starten Sie das Programm erneut.')
            print('Programm mit \'STRG+C\' beenden.')
            while True:
                try:
                    sleep(1)
                except KeyboardInterrupt:
					sys.exit()



    while True:
        args.parcours = raw_input('Valide PARCOURS.id angeben um Aufzeichnung zu starten: ')
        
        while True:
            parcours = db.parcours.find_one({'id': args.parcours})
            if bool(parcours):
                break
            args.parcours = raw_input('PARCOURS.id "' + args.parcours + '" existiert nicht. Zum Aufzeichnen bitte valide PARKOUR.id angeben: ')

        now = datetime.datetime.utcnow()
        trainsetName = '_TRAINSET' + now.strftime('%d%m%Y%H%M%S')
        print('PARCOURS gefunden. EXERCISEs werden geladen, ' + trainsetName + ' wird erstellt...\n')
        gloves[0].setTrainsetExercise(trainsetName, 0, '', '')
        trainset2 = db2[trainsetName]
        trainset2.insert_one(
        {   "_id" : trainsetName,
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

        step = 1
        cmd = ''
        for exercise in parcours["exercises"]:
            mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
            if (bool(mutation) and 'slug' in mutation):
                slug = mutation['slug']
            print(str(step) + '/' + str(len(parcours['exercises'])) + ' (' + exercise['mutation']['id'] + ') "' + slug + '"')
            step += 1

        print("----------------------")
        
        if 'comment' in parcours:
            print '- COMMENT: "' + parcours['comment'] + '"'
        print '- STARTPOSE: "' + parcours['pose']['start'] + '"'
        print '----------------------'
        print 'Zum Starten des PARCOURS \'Leertaste\' druecken...'
        
        while True:
            cmd = getch()
            if cmd == ' ':
                break;
                
        print '----------------------'        
        


        step = 1
        for exercise in parcours['exercises']:
			mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
            gloves[0].setTrainsetExercise('', step, exercise['mutation']['id'], str(mutation['_id']))
            gloves[0].recording = True
            print 'Jetzt EXERCISE ' + str(step) + '/' + str(len(parcours['exercises'])) + ' (' + exercise['mutation']['id'] + ') ausfuehren'
            if (bool(mutation) and 'instruction' in mutation):
                print '- INSTRUCTION: "' + mutation['instruction'] + '"'


            if bool(mutation) and 'hands' in mutation:
                hands = mutation['hands']
                handText(db, hands, 'left', 'linke')
                handText(db, hands, 'right', 'rechte')

            print '----------------------'
            if exercise['signal']['beep']:
                beep()

            cmd = ''
            while True:
                cmd = getch()
                if cmd == ' ':
					step += 1
                    break
                if cmd == 'x':
                    time = gloves[0].now();
                    trainset2.update_one({ 'experiment' : { 'id' : args.experiment } },
                                        { '$set' : { 'status' : { 'faulty' : time } } })
                    print 'PARCOURS abgebrochen. Daten unter TRAINSET ' + trainsetName + ' abgespeichert und als fehlerhaft (TRAINSET.status.faulty) markiert.'
                    break

            gloves[0].recording = False

            if cmd == 'x':
                break

        trainset2.update_one({ 'experiment' : { 'id' : args.experiment } },
                             { '$set' : { 'ended' : datetime.datetime.utcnow() } })
        if cmd != 'x':
            print 'Aufnahme beendet! PARCOURS ' + args.parcours + ' erfolgreich durchlaufen.'
        beep()
        beep()
        print 'aufgenommene DATA wurde unter TRAINSET ' + trainsetName + ' abgespeichert.'
        print 'Druecken Sie \'Leertaste\' um einen neuen PARCOURS zu laden. Programm-Argumente bleiben erhalten!'
        print 'Druecken Sie \'STRG+C\' um das Programm zu beenden. Alle Programm-Argumente werden \'vergessen\'!\n'           
        while True:
            cmd = getch()
            if cmd == ' ':
                break;
            if ord(cmd) == 3:
               print 'Beende...'
               sys.exit()
            sleep(1);
	



