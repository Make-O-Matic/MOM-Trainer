#!/usr/bin/env python

import argparse

from pymongo import MongoClient
from guh import guh
from guh import devices
from guh import parameters
from guh import actions
from guh import selector

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='recorder.')
    parser.add_argument('-e', '--experiment', type=int, required=True, help='EXPERIMENT.id (neu)')
    parser.add_argument('-o', '--observer', type=int, required=True, help='OBSERVER.id (neu)')
    parser.add_argument('-s', '--subject', type=int, required=True, help='SUBJECT.id (neu)')
    parser.add_argument('-p', '--parkour', type=int, required=True, help='PARKOUR.id (vorhanden)')
    parser.add_argument('--host', type=str, default='localhost', help='the location of the guh daemon (default 127.0.0.1)')
    parser.add_argument('--port', type=int, default=2222, help='the port of the the guh daemon (default 2222)')

    args = parser.parse_args()

    db_client = MongoClient()
    db = db_client.makeomatic
    parkours = db.parkour
    parkour = parkours.find_one({"_id": args.parkour})
    print parkour
    if not guh.init_connection(args.host, args.port):
        exit()

    deviceClassId = '{330e3a6f-a6e0-408d-acb0-26329ea7f5e6}'
    deviceClass = devices.get_deviceClass(deviceClassId)
    params = {}
    params['deviceClassId'] = deviceClassId
    params['name'] = 'glove'
    deviceParams = parameters.read_params(deviceClass['paramTypes'])
    if deviceParams:
        params['deviceParams'] = deviceParams
    response = guh.send_command("Devices.AddConfiguredDevice", params)
    guh.print_device_error_code(response['params']['deviceError'])
    deviceId = response['params']['deviceId']

    actionCmdParams = {}
    actionCmdParams['deviceId'] = deviceId
    stateCmdParams = {};
    stateCmdParams['deviceId'] = deviceId
    stateCmdParams['stateTypeId'] = deviceClass['stateTypes'][2]['id']
    recordingActionTypeId = '65daba61-29bb-498a-b699-737873fdff28';
    mutationActionTypeId = '3b2ca689-c3d2-48c0-95a4-e415804b7c38';
    recordingActionType = actions.get_actionType(recordingActionTypeId)
    mutationActionType = actions.get_actionType(mutationActionTypeId)

    for mutation in ['mut1','mut2','mut3']:
        if not selector.getYesNoSelection("Continue?"):
            break

        actionParams = parameters.read_params(recordingActionType['paramTypes'])
        actionCmdParams['actionTypeId'] = recordingActionTypeId
        actionCmdParams['params'] = actionParams
        response = guh.send_command("Actions.ExecuteAction", actionCmdParams)
        if response:
            guh.print_device_error_code(response['params']['deviceError'])

        param = {}
        param['paramTypeId'] = mutationActionType['paramTypes'][0]['id']
        param['value'] = mutation
        actionCmdParams['actionTypeId'] = mutationActionTypeId
        actionCmdParams['params'] = [ param ]
        response = guh.send_command("Actions.ExecuteAction", actionCmdParams)
        if response:
            guh.print_device_error_code(response['params']['deviceError'])

        response = guh.send_command("Devices.GetStateValue", stateCmdParams)
        print "%35s: %s" % (deviceClass['stateTypes'][2]['name'], mutation)
        raw_input("\nPress \"enter\" to return to the menu...\n")
#response['params']['value']



