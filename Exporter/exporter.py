#!/usr/bin/env python

import argparse
from sets import Set
from pymongo import MongoClient, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='exporter.', add_help=False)
    parser.add_argument('-H', '--hostnameport', required=True, help='HOSTNAME:PORT')
    parser.add_argument('-D', '--db', required=True, help='DATABASE')
    parser.add_argument('-U', '--username', required=True, help='USER')
    parser.add_argument('-P', '--password', required=True, help='PASSWORT')
    parser.add_argument('--hand', choices=['left', 'right', 'both'], default='both', help='HAND')
    parser.add_argument('-t', '--trainset', nargs='+', help='TRAINSET.id')
    parser.add_argument('-e', '--experiment', nargs='+', help='EXPERIMENT.id')
    parser.add_argument('-s', '--subject', nargs='+', help='SUBJECT.id')
    parser.add_argument('-o', '--observer', nargs='+', help='OBSERVER.id')
    parser.add_argument('-p', '--parcours', nargs='+', help='PARCOURS.id')
    parser.add_argument('-c', '--collector', nargs='+', help='COLLECTOR.id')
    parser.add_argument('-m', '--mutation', nargs='+', help='MUTATION.id')
    parser.add_argument('-g', '--gesture', nargs='+', help='GESTURE.id')
    parser.add_argument('-h', '--host', nargs='+', help='HOST.id')

    args = parser.parse_args()
    try:
        db_client = MongoClient('mongodb://' + args.username + ':' + args.password + '@' + args.hostnameport + '/' + args.db)
        db = db_client[args.db]
    except errors.ConnectionFailure:
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
  
    
    parcours_ids = Set(args.parcours)
    aggregated_parcours = db.parcours.aggregate([
        {
            '$unwind' : '$exercises'
        },
        {
            '$lookup' :
                {
                    'from' : 'mutations',
                    'localField' : 'exercises.mutation.id',
                    'foreignField' : 'id',
                    'as' : 'mutation'
                }
        },
        {
            '$match' : { '$or' : [
                { 'mutation.id' : { '$in' : args.mutation } },
                { 'mutation.hands.left.gesture.id' : { '$in' : args.gesture } },
                { 'mutation.hands.right.gesture.id' : { '$in' : args.gesture } },
                { 'mutation.hands.left.host.id' : { '$in' : args.host } },
                { 'mutation.hands.right.host.id' : { '$in' : args.host } }
            ]}
        },
            #'$group' :
    ])
    for parcours in aggregated_parcours:
        parcours_ids.add(parcours.id)
        

 
    collections = db.collection_names()
    for collection in collections:
        collection_info = db[collection].find_one({ '_id' : collection })
        if (collection_info
            and ((collection_info._id in args.trainsets)
                or (collection_info.experiment.id in args.experiments)
                or (collection_info.parcours.subject.id in args.subject)
                or (collection_info.parcours.observer.id in args.observer)
                or (collection_info.parcours.id in parcours_ids)
                or (collection_info.parcours.subject.hands.left.id in args.collector)
                or (collection_info.parcours.subject.hands.right.id in args.collector))):
            if not collection_info.status.faulty:
                trainsets[collection] = collection_info.created
 
