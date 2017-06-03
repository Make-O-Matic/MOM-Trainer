#!/usr/bin/env python

import sys
from subprocess import call
import argparse
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
        db_client.admin.command('ismaster')
        db = db_client[args.db]
    except (errors.ConnectionFailure, errors.InvalidURI, errors.OperationFailure):
        print('Es konnte keine Verbindung zur Datenbank hergestellt werden.')
        sys.exit()
    match_mutation = []
    if args.mutation:
        match_mutation.add({ 'mutation.id' : { '$in' : args.mutation } })
    if args.gesture:
        match_mutation.add(
        { '$or' : [
            { 'mutation.hands.left.gesture.id' : { '$in' : args.gesture } },
            { 'mutation.hands.right.gesture.id' : { '$in' : args.gesture } }
        ]})
    if args.host:
        match_mutation.add(
        { '$or' : [
            { 'mutation.hands.left.host.id' : { '$in' : args.host } },
            { 'mutation.hands.right.host.id' : { '$in' : args.host } }
        ]})
    parcours_ids = set()
    if not match_mutation:
        parcours_ids = set(args.parcours)
    else:
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
            '$match' : { '$and' : match_mutation }
        }
        ])
        for parcours in selected_parcours:
            parcours_ids.add(parcours['id'])
        if args.parcours:
            parcours_ids &= args.parcours
        if not parcours_ids:
            print('keine Daten zum Export verfuegbar.')
            sys.exit()

 
    collections = db.collection_names()
    trainset_infos = {}
    for collection in collections:
        if not 'TRAINSET' in collection:
            continue
        trainset_info = db[collection].find_one({'experiment': {'$exists': True}})
        parcours = 'parcours'
        if 'parkour' in trainset_info:
            parcours = 'parkour'
        if (trainset_info
            and (not args.trainset or trainset_info['_id'] in args.trainset)
            and (not args.experiment or trainset_info['experiment']['id'] in args.experiment)
            and (not args.subject or trainset_info[parcours]['subject']['id'] in args.subject)
            and (not args.observer or trainset_info[parcours]['observer']['id'] in args.observer)
            and (not parcours_ids or trainset_info[parcours]['id'] in parcours_ids)
            and (not args.collector or trainset_info[parcours]['subject']['hands']['left']['id'] in args.collector)
            and (not args.collector or trainset_info[parcours]['subject']['hands']['right']['id'] in args.collector)):
            if not ('status' in trainset_info and 'faulty' in trainset_info['status']):
                trainset_infos[collection] = trainset_info
    
    if not trainset_infos:
        print('keine Daten zum Export verfuegbar.')
        sys.exit()

    fields = {
        'trainset': ['trainset ID', ''],
        'experiment' : ['experiment ID', ''],
        'subject': ['subject ID', ''],
        'observer': ['observer ID', ''],
        'info.side': ['collected by hand', 'left/right', 'boolean'],
        'info.collector': ['collector ID', ''],
        'data.stamp.microSeconds': ['timestamp', 'microseconds', 'time'],
        'data.rfid': ['RFID', ''],
        'data.grasp.sensorA': ['GRASP-A', '0,1023', 'integer'],
        'data.grasp.sensorB': ['GRASP-B', '0,1023', 'integer'],
        'data.grasp.sensorC': ['GRASP-C', '0,1023', 'integer'],
        'data.acceleration.x': ['AX', '-7,+7', 'float'],
        'data.acceleration.y': ['AY', '-7,+7', 'float'],
        'data.acceleration.z': ['AZ', '-7,+7', 'float'],
        'data.rotation.x': ['EX', '-90,+90', 'float'],
        'data.rotation.y': ['EY', '-90,+90', 'float'],
        'data.rotation.z': ['EZ', '-90,+90', 'float'],
        'data.interface.userInputButton': ['user input', 'true/false', 'boolean'],
        'data.interface.handIsInGlove': ['hand in glove', 'true/false', 'boolean'],
        'parcours': ['parcours ID', ''],
        'step': ['parcours step', '', 'integer'],
        'mutation.id': ['mutation ID', ''],
        'info.active.hand': ['mutation/hand is active', 'true/false', 'boolean'],
        'info.active.host': ['host ID', ''],
        'info.active.spot': ['host/spot ID', ''],
        'info.active.gesture': ['gesture ID', '']
    }

    tmpCollection = 'tmpexportercollection'

    fieldFile = tempfile.NamedTemporaryFile(mode='w+')
    fieldFile.write('\n'.join(list(fields)) + '\n')
    fieldFile.flush()
    
    outputID = 'EXPORT_' + datetime.datetime.now().strftime('%d%m%Y%H%M%S') 
    outputFile = outputID
    for filters in [args.trainset, args.experiment, args.gesture, args.host,
                    args.subject, args.observer, args.mutation, args.collector, args.parcours]:
        if filters:
	        outputFile += '_' + '-'.join(filters)
    outputFile += '.csv'
    output = open(outputFile, 'a+')
    output.write('#id: ' + outputID + '\n#filename: ' + outputFile + '\n')
    output.write('#created: ' + datetime.datetime.now().strftime('%d.%m.%Y') + '\n')
    output.write('#creator: Make-O-Matic\n##\n')
    db_args = '#arguments:'
    filter_args = '#filters:'
    for arg, values in vars(args).items():
        if isinstance(values, str):
            text = ' --' + arg + ': ' + values + ','
            if arg == 'hand':
                filter_args += text
            else:
                db_args += text
        else:
            if values:
                filter_args += ' --' + arg + ':'
            for value in values:
                filter_args += ' ' + value + ','
    output.write(db_args + '\n' + filter_args + '\n')
    output.write('#data from: ' + ', '.join(list(trainset_infos)) + '\n##\n')
    typerow = []
    rangerow = []
    namerow = []
    for field, info in fields.items():
        namerow.append(info[0])
        rangerow.append(info[1])
        info.append('string')
        typerow.append(info[2])
    output.write(','.join(typerow) + '\n' + ','.join(rangerow) + '\n'
        + ','.join(namerow) + '\n')
    output.flush()

    for trainset in sorted(trainset_infos, key=lambda trainset: trainset_infos[trainset]['created']):
        info = trainset_infos[trainset]  
        parcours = 'parcours'
        if 'parkour' in info:
            parcours = 'parkour'
        match = { '_id' : { '$ne' : info['_id'] } }
        if args.hand and args.hand != 'both':
            match.update({ 'collector.id': info[parcours]['subject']['hands'][args.hand]['uuid'] })
        db[trainset].aggregate([{
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
        }])
        
        start = db[tmpCollection].find_one({}, sort=[('data.stamp.microSeconds', ASCENDING)])
        if start:
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

    
    


