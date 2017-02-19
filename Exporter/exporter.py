#!/usr/bin/env python

import argparse

from pymongo import MongoClient


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='exporter.', add_help=False)
    parser.add_argument('-H', '--hostnameport', type=str, required=True, help='HOSTNAME:PORT')
    parser.add_argument('-D', '--db', type=str, required=True, help='DATABASE')
    parser.add_argument('-U', '--username', type=str, required=True, help='USER')
    parser.add_argument('-P', '--password', type=str, required=True, help='PASSWORT')
    parser.add_argument('-t', '--trainset', type=str, nargs='+', help='TRAINSET.id')
    parser.add_argument('-e', '--experiment', type=str, nargs='+', help='EXPERIMENT.id')
    parser.add_argument('-s', '--subject', type=str, nargs='+', help='SUBJECT.id')
    parser.add_argument('-o', '--observer', type=str, nargs='+', help='OBSERVER.id')
    parser.add_argument('-p', '--parcours', type=str, nargs='+', help='PARCOURS.id')
    parser.add_argument('-c', '--collector', type=str, nargs='+', help='COLLECTOR.id')
    parser.add_argument('-m', '--mutation', type=str, nargs='+', help='MUTATION.id')
    parser.add_argument('-g', '--gesture', type=str, nargs='+', help='GESTURE.id')
    parser.add_argument('-h', '--host', type=str, nargs='+', help='HOST.id')

    args = parser.parse_args()

