import sys
import tty
import termios
import argparse
import threading
from time import sleep
from subprocess import call
import uuid

from pymongo import MongoClient, errors, ASCENDING, DESCENDING
from momconnectivity.glove import Glove


def add_db_arguments(parser):
    parser.add_argument('--hostname', required=True, help='HOSTNAME')
    parser.add_argument('--port', required=True, help='PORT')
    parser.add_argument('--db', required=True, help='DATABASE')
    parser.add_argument('--username', required=True, help='USER')
    parser.add_argument('--password', required=True, help='PASSWORT')


def add_MAC_arguments(parser):
    parser.add_argument('-L', '--lMAC', required=True,
        help='COLLECTOR.macAddress fuer den linken Handschuh')
    parser.add_argument('-R', '--rMAC', required=True,
        help='COLLECTOR.macAddress fuer den rechten Handschuh')


def db(args):
    try:
        db_client = MongoClient('mongodb://' + args.username + ':' + args.password + 
                                '@' + args.hostname + ':' + args.port + '/' + args.db)
        db_client.admin.command('ismaster')
        db = db_client[args.db]
        return db
    except (errors.ConnectionFailure, errors.InvalidURI, errors.OperationFailure):
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
        sys.exit()


def trainset_infos(db):
    collections = db.collection_names()
    trainset_infos = {}
    for collection in collections:
        if not 'TRAINSET' in collection:
            continue
        trainset_info = db[collection].find_one({ '_id' : collection })
        if (trainset_info and
            not ('status' in trainset_info and 'faulty' in trainset_info['status'])):
            if 'parkour' in trainset_info:
                trainset_info['parcours'] = trainset_info['parkour']
            trainset_infos[collection] = trainset_info

    return trainset_infos


def exercises(db, parcours_id):
    parcours = db.parcours.find_one({'id': parcours_id})
    return parcours["exercises"]


def mutation(db, exercise):
    mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
    return mutation


def info(db, hands, side, gesture_text):
    info, instruction = None, None
    if side in hands:
        info = ''
        hand = hands[side]
        if 'host' in hand:
            info += hand['host']['id']
            if 'spot' in hand['host'] and 'id' in hand['host']['spot']:
                info += '>' + hand['host']['spot']['id']

        if 'gesture' in hand:
            gesture = db.gestures.find_one({'id' : hand['gesture']['id']})
            info += gesture_text + gesture['name']

        if 'instruction' in hand:
            instruction = hand['instruction']

    return info, instruction


def endpoint(trainset, filter, ascending):
    if ascending:
        order = ASCENDING
    else:
        order = DESCENDING
    endpoint = trainset.find_one(filter, sort=[('data.stamp.microSeconds', order)])
    if bool(endpoint):
        return endpoint['data']['stamp']['microSeconds']
    else:
        return None


def connected_gloves(args, minimum, rfid):
    minimum_state = 3
    if minimum == 1:
        minimum_state = 1
    gloves = []

    def set_connected(state):
        if state > gloves[0].state:
            beep()
        gloves[0].state = state
        if state >= minimum_state:
            gloves[0].connected.set()

    def is_recording():
        return gloves[0].recording

    def set_rfid(rfid):
        if gloves[0].rfid_received.is_set():
            return;
        gloves[0].rfid = rfid
        gloves[0].rfid_received.set()

    lUUID = str(uuid.uuid4())
    rUUID = str(uuid.uuid4())
    try:
        gloves = [Glove(args.lMAC, args.rMAC, set_connected, is_recording, lUUID, rUUID)]
        if rfid:
            gloves[0].processRFID = set_rfid
        gloves[0].state = 0
        gloves[0].connected = threading.Event()
        gloves[0].recording = False
        gloves[0].rfid_received = threading.Event()
        gloves[0].connect()
        gloves[0].connected.wait()
        return gloves[0]
    except RuntimeError:
            print('Verbindung zu (mind.) einem COLLECTOR konnte nicht hergestellt werden.')
            print('Bitte pruefen Sie die Bluetooth-Verbindung und starten Sie das Programm erneut.')
            print('Programm mit \'STRG+C\' beenden.')
            while True:
                try:
                    sleep(1)
                except KeyboardInterrupt:
                    gloves[0].disconnect()
                    sys.exit()


def beep():
    call(['ogg123', '-q', '/usr/share/sounds/ubuntu/stereo/dialog-information.ogg'])


def print_line():
    print('----------------------')


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
