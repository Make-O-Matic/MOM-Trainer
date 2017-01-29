#!/usr/bin/env python

import argparse

from pymongo import MongoClient
from guh import guh
from guh import devices

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
    db = db_client.mom
    parkours = db.parkour
    parkour = parkours.find_one({"id": args.parkour})

    if not guh.init_connection(args.host, args.port):
        exit()

    devices.add_configured_device("330e3a6f-a6e0-408d-acb0-26329ea7f5e6")

    #actions
