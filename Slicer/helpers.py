import sys
from pymongo import MongoClient

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
