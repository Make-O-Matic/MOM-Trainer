#!/usr/bin/env python

import sys
from subprocess import call
import argparse
from sets import Set
import datetime
import tempfile
from pymongo import MongoClient, errors, ASCENDING


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='exporter.', add_help=False)
    parser.add_argument('--hostname', required=True, help='HOSTNAME')
    parser.add_argument('--port', required=True, help='PORT')
    parser.add_argument('--db', required=True, help='DATABASE')
    parser.add_argument('--username', required=True, help='USER')
    parser.add_argument('--password', required=True, help='PASSWORT')
    parser.add_argument('--hand', choices=['left', 'right', 'both'], default='both', help='HAND')
    parser.add_argument('-t', '--trainset', nargs='+', default= [], help='TRAINSET.id')
    parser.add_argument('-e', '--experiment', nargs='+', default= [], help='EXPERIMENT.id')
    parser.add_argument('-s', '--subject', nargs='+', default= [], help='SUBJECT.id')
    parser.add_argument('-o', '--observer', nargs='+', default= [], help='OBSERVER.id')
    parser.add_argument('-p', '--parcours', nargs='+', default= [], help='PARCOURS.id')
    parser.add_argument('-c', '--collector', nargs='+', default= [], help='COLLECTOR.id')
    parser.add_argument('-m', '--mutation', nargs='+', default= [], help='MUTATION.id')
    parser.add_argument('-g', '--gesture', nargs='+', default= [], help='GESTURE.id')
    parser.add_argument('-h', '--host', nargs='+', default= [], help='HOST.id')

    args = parser.parse_args()
    try:
        db_client = MongoClient('mongodb://' + args.username + ':' + args.password + 
                                '@' + args.hostname + ':' + args.port + '/' + args.db)
        db = db_client[args.db]
    except (errors.ConnectionFailure, errors.InvalidURI):
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
        sys.exit()
    
    parcours_ids = Set(args.parcours)
    selected_parcours = db.parcours.aggregate([
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
            '$unwind' : '$mutation'
        },       
        {
            '$match' : { '$or' : [
                { 'mutation.id' : { '$in' : args.mutation } },
                { 'mutation.hands.left.gesture.id' : { '$in' : args.gesture } },
                { 'mutation.hands.right.gesture.id' : { '$in' : args.gesture } },
                { 'mutation.hands.left.host.id' : { '$in' : args.host } },
                { 'mutation.hands.right.host.id' : { '$in' : args.host } }
            ]}
        }
    ])
    for parcours in selected_parcours:
        parcours_ids.add(parcours['id'])
 
    collections = db.collection_names()
    trainset_infos = {}
    for collection in collections:
        if not 'TRAINSET' in collection:
            continue
        trainset_info = db[collection].find_one({ '_id' : collection })
        parcours = 'parcours'
        if 'parkour' in trainset_info:
            parcours = 'parkour'
        if (trainset_info
            and ((trainset_info['_id'] in args.trainset)
                or (trainset_info['experiment']['id'] in args.experiment)
                or (trainset_info[parcours]['subject']['id'] in args.subject)
                or (trainset_info[parcours]['observer']['id'] in args.observer)
                or (trainset_info[parcours]['id'] in parcours_ids)
                or (trainset_info[parcours]['subject']['hands']['left']['id'] in args.collector)
                or (trainset_info[parcours]['subject']['hands']['right']['id'] in args.collector))):
            if not ('status' in trainset_info and 'faulty' in trainset_info['status']):
                trainset_infos[collection] = trainset_info
    
    if not trainset_infos:
        print('keine Daten zum Export verfuegbar.')
        sys.exit()

    fields = '''trainset
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
step
mutation.id
info.active.hand
info.active.host
info.active.spot
info.active.gesture
'''

    tmpCollection = 'tmpexportercollection'

    fieldFile = tempfile.NamedTemporaryFile()
    fieldFile.write(fields)
    fieldFile.flush()
    
    outputFile = 'EXPORT_' + datetime.datetime.now().strftime('%d%m%Y%H%M%S') 
    for filter in (args.trainset + args.experiment + args.subject + args.observer +
                   args.parcours + args.collector + args.mutation + args.gesture + args.host):
        outputFile += '_' + filter
    outputFile += '.csv'
    output = open(outputFile, 'a+')

    for trainset in sorted(trainset_infos, key=lambda trainset: trainset_infos[trainset]['created']):
        info = trainset_infos[trainset]   
        parcours = 'parcours'
        if 'parkour' in trainset_info:
            parcours = 'parkour'
        match = { '_id' : { '$ne' : info['_id'] } }
        if args.hand and args.hand != 'both':
            match.update({ 'collector.id': info[parcours]['subject']['hands'][args.hand]['uuid'] })
        db[trainset].aggregate([
        {
            '$match' : match
        },
        {
            '$lookup' :
                {
                    'from' : 'mutations',
                    'localField' : 'mutation.id',
                    'foreignField' : 'id',
                    'as' : 'mutationInfo'
                }
        },    
        {
            '$unwind' : '$mutationInfo'
        },    
        {
            '$addFields' : {
                'trainset' : info['_id'],
                'experiment' : info['experiment']['id'],
                'subject' : info[parcours]['subject']['id'],
                'observer' : info[parcours]['observer']['id'],
                'parcours' : info[parcours]['id'],
                'info' : {
                    '$cond' : { 
                        'if' : { '$eq' : [ '$collector.id', info[parcours]['subject']['hands']['left']['uuid'] ] }, 
                        'then' : { 
                            'side' : 'left', 
                            'collector' : info[parcours]['subject']['hands']['left']['id'],
                            'active' : {'$cond' : { 
                                'if' : { '$gt' : [ '$mutationInfo.hands.left', None ] },
                                'then' : { 
                                    'hand' : True,
                                    'host' : '$mutationInfo.hands.left.host.id',
                                    'spot' : '$mutationInfo.hands.left.host.spot.id',
                                    'gesture' : '$mutationInfo.hands.left.gesture.id'
                                },
                                'else' : {
                                    'hand' : False
                                }
                            } }
                        },
                        'else' : { 
                            'side' : 'right', 
                            'collector' : info[parcours]['subject']['hands']['right']['id'],
                            'active' : {'$cond' : { 
                                'if' : { '$gt' : [ '$mutationInfo.hands.right', None ] },
                                'then' : { 
                                    'hand' : True,
                                    'host' : '$mutationInfo.hands.right.host.id',
                                    'spot' : '$mutationInfo.hands.right.host.spot.id',
                                    'gesture' : '$mutationInfo.hands.right.gesture.id'
                                },
                                'else' : {
                                    'hand' : False
                                }  
                            } }
                        }
                    }
                }
            }
        },
        {
            '$out' : tmpCollection
        }
        ])
        
        start = db[tmpCollection].find_one({}, sort=[('data.stamp.microSeconds', ASCENDING)])
        db[tmpCollection].update_many({}, { '$inc' : { 'data.stamp.microSeconds' : -start['data']['stamp']['microSeconds'] } })
                
        call(['mongoexport', '--quiet',
            '--host', args.hostname,
            '--port', args.port,
            '--username', args.username,
            '--password', args.password,
            '--db', args.db,
            '--collection', tmpCollection,           
            '--fieldFile', fieldFile.name,
            '--type', 'csv',
            '--sort', '"{ \'data.stamp.microSeconds\' : 1 }"'
            ], stdout=output) 
      
    
    output.close()        
    call(['sed', '-i', '/data\.stamp\.microSeconds/d', outputFile])
    


