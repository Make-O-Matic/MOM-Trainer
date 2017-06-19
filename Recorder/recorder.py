#!/usr/bin/env python

import argparse
import datetime
import threading
from time import sleep
import uuid
import os
import sys
import tty
import termios
from subprocess import call
import signal

from pymongo import MongoClient
from momconnectivity.glove import Glove
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import helpers

def main():
    parser = argparse.ArgumentParser(description='recorder.')
    helpers.add_db_arguments(parser, False)
    helpers.add_db_arguments(parser, True)
    helpers.add_MAC_arguments(parser)
    parser.add_argument('-l', '--lId', required=True,
                        help='COLLECTOR.id fuer den linken Handschuh')
    parser.add_argument('-r', '--rId', required=True,
                        help='COLLECTOR.id fuer den rechten Handschuh')
    parser.add_argument('-e', '--experiment', required=True,
                        help='EXPERIMENT.id (neu)')
    parser.add_argument('-o', '--observer', required=True,
                        help='OBSERVER.id (neu)')
    parser.add_argument('-s', '--subject', required=True,
                        help='SUBJECT.id (neu)')

    args = parser.parse_args()

    db_generic = helpers.db(args.dbgen)
    db_ts = helpers.db(args.dbts)

    gloves, lUUID, rUUID = helpers.connected_gloves(args, 3, None)

    while True:
        args.parcours = input('Valide PARCOURS.id angeben um Aufzeichnung zu starten: ')

        while True:
            parcours = db_generic.parcours.find_one({'id': args.parcours})
            if bool(parcours):
                break
            args.parcours = input(
                'PARCOURS.id "' + args.parcours
                + '" existiert nicht. Zum Aufzeichnen bitte valide PARKOUR.id angeben: ')

        now = datetime.datetime.utcnow()
        trainset_name = 'TRAINSET' + now.strftime('%d%m%Y%H%M%S')
        print('PARCOURS gefunden. EXERCISEs werden geladen, '
              + trainset_name + ' wird erstellt...\n')
        gloves.setTrainsetExercise(trainset_name, 0, '', '')
        trainset = db_ts[trainset_name]
        trainset.insert_one({
            '_id': trainset_name,
            'created': now,
            'experiment': {'id': args.experiment},
            'parcours': {
                'id': args.parcours,
                'observer': {'id': args.observer},
                'subject': {
                    'id': args.subject,
                    'hands': {
                        'left': {
                            'uuid': lUUID,
                            'id': args.lId,
                            'macAddress': args.lMAC
                        },
                        'right': {
                            'uuid': rUUID,
                            'id': args.rId,
                            'macAddress': args.rMAC
                        }
                    }
                }
            }
        })

        mutations = {}
        for exercise in parcours['exercises']:
            mutations[exercise['mutation']['id']] = db_generic.mutations.find_one(
                {'id': exercise['mutation']['id']})

        step = 1
        for exercise in parcours['exercises']:
            mutation = mutations[exercise['mutation']['id']]
            if 'slug' in mutation:
                slug = mutation['slug']
            print(str(step) + '/' + str(len(parcours['exercises']))
                  + ' (' + exercise['mutation']['id'] + ') "' + slug + '"')
            step += 1

        print("----------------------")
        
        if 'comment' in parcours:
            print('- COMMENT: "' + parcours['comment'] + '"')
        print('- STARTPOSE: "' + parcours['pose']['start'] + '"')
        print('----------------------')
        print('Zum Starten des PARCOURS \'Leertaste\' druecken...')
        
        cmd = ''
        while True:
            cmd = helpers.getch()
            if cmd == ' ':
                break;
                
        print('----------------------')

        step = 1
        for exercise in parcours['exercises']:
            mutation = mutations[exercise['mutation']['id']]
            gloves.setTrainsetExercise('', step, exercise['mutation']['id'], 
                str(mutation['_id']))
            gloves.recording = True
            if ('slug' in mutation):
                slug = mutation['slug']
            print('Jetzt EXERCISE ' + str(step) + '/' + str(len(parcours['exercises'])) + 
                  ' (' + exercise['mutation']['id'] + ') "' + slug + '" ausfuehren')

            if 'instruction' in mutation:
                print('- INSTRUCTION: "' + mutation['instruction'] + '"')
            if 'hands' in mutation:
                hands = mutation['hands']
                print_info(db_generic, hands, 'left', 'linke')
                print_info(db_generic, hands, 'right', 'rechte')

            print('----------------------')
            if exercise['signal']['beep']:
                beep()

            cmd = ''
            while True:
                cmd = helpers.getch()
                if cmd == ' ':
                    step += 1
                    break
                if cmd == 'x':
                    time = gloves.now();
                    trainset.update_one({ 'experiment' : { 'id' : args.experiment } },
                                        { '$set' : { 'status' : { 'faulty' : time } } })
                    print('PARCOURS abgebrochen. Daten unter TRAINSET ' + trainset_name 
                        + ' abgespeichert und als fehlerhaft (TRAINSET.status.faulty) markiert.')
                    break

            gloves.recording = False

            if cmd == 'x':
                break

        trainset.update_one({ 'experiment' : { 'id' : args.experiment } },
                             { '$set' : { 'ended' : datetime.datetime.utcnow() } })
        if cmd != 'x':
            print('Aufnahme beendet! PARCOURS ' + args.parcours + ' erfolgreich durchlaufen.')
        beep()
        beep()
        print('aufgenommene DATA wurde unter TRAINSET ' + trainset_name + ' abgespeichert.')
        print('Druecken Sie \'Leertaste\' um einen neuen PARCOURS zu laden. Programm-Argumente bleiben erhalten!')
        print('Druecken Sie \'STRG+C\' um das Programm zu beenden. Alle Programm-Argumente werden \'vergessen\'!\n')
        while True:
            cmd = helpers.getch()
            if cmd == ' ':
                break;


def beep():
    call(['ogg123', '-q', '/usr/share/sounds/ubuntu/stereo/dialog-information.ogg'])


def print_info(db, hands, side, description):
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

        print('- ' + description + ' Hand\n' + text);
        if 'instruction' in hand:
            print('-- INSTRUCTION: "' + hand['instruction'] + '"')


if __name__ == "__main__":
    main()
