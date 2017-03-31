import sys
from pymongo import MongoClient, errors, ASCENDING, DESCENDING


def add_db_arguments(parser):
    parser.add_argument('--hostname', required=True, help='HOSTNAME')
    parser.add_argument('--port', required=True, help='PORT')
    parser.add_argument('--db', required=True, help='DATABASE')
    parser.add_argument('--username', required=True, help='USER')
    parser.add_argument('--password', required=True, help='PASSWORT')


def make_db(args):
    try:
        db_client = MongoClient('mongodb://' + args.username + ':' + args.password + 
                                '@' + args.hostname + ':' + args.port + '/' + args.db)
        db_client.admin.command('ismaster')
        db = db_client[args.db]
        return db
    except (errors.ConnectionFailure, errors.InvalidURI, errors.OperationFailure):
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
        sys.exit()


def get_trainset_infos(db):
    collections = db.collection_names()
    trainset_infos = {}
    for collection in collections:
        if not 'TRAINSET' in collection:
            continue
        trainset_info = db[collection].find_one({ '_id' : collection })
        if trainset_info:
            if 'parkour' in trainset_info:
                trainset_info['parcours'] = trainset_info['parkour']
            trainset_infos[collection] = trainset_info

    return trainset_infos


def get_exercises(db, parcours_id):
    parcours = db.parcours.find_one({'id': parcours_id})
    return parcours["exercises"]


def get_mutation(db, exercise):
    mutation = db.mutations.find_one({'id' : exercise['mutation']['id']})
    return mutation


def get_info(db, hands, side):
    host, spot, gesture, instruction = '', '', '', ''
    if side in hands:
        hand = hands[side]
        if 'host' in hand:
            host = hand['host']['id']
            if 'spot' in hand['host'] and 'id' in hand['host']['spot']:
                spot = hand['host']['spot']['id']

        if 'gesture' in hand:
            gesture = db.gestures.find_one({'id' : hand['gesture']['id']})
            gesture = gesture['name']

        if 'instruction' in hand:
            instruction = hand['instruction']

    return host, spot, gesture, instruction


def get_endpoint(trainset, filter, ascending):
    if ascending:
        order = ASCENDING
    else:
        order = DESCENDING
    endpoint = trainset.find_one(filter, sort=[('data.stamp.microSeconds', order)])
    if bool(endpoint):
        return endpoint['data']['stamp']['microSeconds']
    else:
        return None
