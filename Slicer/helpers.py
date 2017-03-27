import sys
from pymongo import MongoClient, errors

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
