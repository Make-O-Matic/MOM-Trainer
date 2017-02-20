#!/usr/bin/env python

import sys
from subprocess import call
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
    parser.add_argument('-m', '--mutation', nargs='+', default= [], help='MUTATION.id')
    parser.add_argument('-g', '--gesture', nargs='+', default= [], help='GESTURE.id')
    parser.add_argument('-h', '--host', nargs='+', default= [], help='HOST.id')

    args = parser.parse_args()
    try:
        db_client = MongoClient('mongodb://' + args.username + ':' + args.password + '@' + args.hostnameport + '/' + args.db)
        db = db_client[args.db]
    except errors.ConnectionFailure:
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
        sys.exit()
    
    parcours_ids = Set(args.parcours)
    aggregated_parcours = db.parcours.aggregate([
        {
            '$unwind' : '$exercises'
        },
        {
            '$lookup' : {
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
        
   #print
 
    collections = db.collection_names()
    trainset_infos = {}
    for collection in collections:
        trainset_info = db[collection].find_one({ '_id' : collection })
        if (trainset_info
            and ((trainset_info._id in args.trainsets)
                or (trainset_info.experiment.id in args.experiments)
                or (trainset_info.parcours.subject.id in args.subject)
                or (trainset_info.parcours.observer.id in args.observer)
                or (trainset_info.parcours.id in parcours_ids)
                or (trainset_info.parcours.subject.hands.left.id in args.collector)
                or (trainset_info.parcours.subject.hands.right.id in args.collector))):
            if not trainset_info.status.faulty:
                trainset_infos[collection] = trainset_info
    
    if not trainset_infos:
        print('keine Daten zum Export verfuegbar.')
        sys.exit()

    fields = '''
trainset
experiment
subject
observer
info.side
info.collector
data.stamp.microSeconds
data.rfid
data.grasp.sensorA
data.grasp.sensorB
data.grasp.sensorC
data.acceleration.x
data.acceleration.y
data.acceleration.z
data.rotation.x
data.rotation.y
data.rotation.z
data.interface.userInputButton
data.interface.handIsInGlove
parcours
data.step
data.mutation.id
info.active.hand
info.active.host
info.active.spot
info.active.gesture
'''

    for trainset in sorted(trainsets, key=trainsets.get.created):
        info = trainset_infos[trainset]   
        matchHand = {}
        if args.hand and args.hand != 'both':
            match = { '$eq' : [ 
                '$collector.id', 
                info.parcours.subject.hands[args.hand].uuid
            ] }
        db[trainset].aggregate([
        {
            '$match' : matchHand
        },
        {
            '$lookup' :
                {
                    'from' : 'mutations',
                    'localField' : 'mutation.id',
                    'foreignField' : 'id',
                    'as' : 'mutation_info'
                }
        },        
        {
            '$addFields' : {
                'trainset' : info._id,
                'experiment' : info.experiment.id,
                'subject' : info.parcours.subject.id,
                'observer' : info.parcours.observer.id,
                'info' : {
                    '$cond' : { 
                        'if' : { '$eq' : [ '$collector.id', info.parcours.subject.hands.left.uuid ] }, 
                        'then' : { 
                            'side' : 'left', 
                            'collector' : info.parcours.subject.hands.left.id,
                            'active' : {'$cond' : { 
                                'if' : { '$gt' : [ 'mutation_info.hands.left', null ] },
                                'then' : { 
                                    'hand' : True,
                                    'host' : 'mutation_info.hands.left.host.id',
                                    'spot' : 'mutation_info.hands.left.host.spot.id',
                                    'gesture' : 'mutation_info.hands.left.gesture.id'
                                },
                                'else' : {
                                    'hand' : False,
                                    'host' : 'mutation_info.hands.right.host.id',
                                    'spot' : 'mutation_info.hands.right.host.spot.id',
                                    'gesture' : 'mutation_info.hands.right.gesture.id'
                                }
                            }}
                        },
                        'else' : { 
                            'side' : 'right', 
                            'collector' : info.parcours.subject.hands.right.id,
                            'active' : {'$cond' : { 
                                'if' : { '$gt' : [ 'mutation_info.hands.right', null ] },
                                'then' : { 
                                    'hand' : True,
                                    'host' : 'mutation_info.hands.right.host.id',
                                    'spot' : 'mutation_info.hands.right.host.spot.id',
                                    'gesture' : 'mutation_info.hands.right.gesture.id'
                                },
                                'else' : {
                                    'hand' : False,
                                    'host' : 'mutation_info.hands.left.host.id',
                                    'spot' : 'mutation_info.hands.left.host.spot.id',
                                    'gesture' : 'mutation_info.hands.left.gesture.id'
                                }  
                            }}
                        }
                    }
                },
                'parcours' : info.parcours.id
            }
        },
        {
            '$out' : 'exporter'
        }
        ])
        
        call(['mongoexport']) 
    


