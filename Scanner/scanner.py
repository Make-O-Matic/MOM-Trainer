#!/usr/bin/env python

import argparse
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import helpers

def main():
    parser = argparse.ArgumentParser(description='tagreader.')
    helpers.add_MAC_arguments(parser)
    helpers.add_db_arguments(parser)
    
    args = parser.parse_args()
    
    db = helpers.db(args)
    hosts = db['hosts']
    print('Datenbankverbindung hergestellt.')

    gloves = helpers.connected_gloves(args, 1, True)
    hand = 'L'
    if gloves.state == 2:
        hand = 'R'
    print('Verbindung zu mind. einem Handschuh hergestellt.')
    print('SCANNER bereit.')
    
    while True:
        gloves.rfid_received.clear()
        print('Bewegen sie einen GLOVE ueber einen TAG um diesen auszulesen oder neu anzulegen')
        gloves.rfid_received.wait()
        print(hand + ': TAG "' + gloves.rfid + '" erkannt!')
        host = hosts.find_one({'spots.rfid': gloves.rfid})
        if bool(host):

            spot = hosts.find_one({'spots.rfid': gloves.rfid}, {'spots.$': 1})['spots'][0]
            helpers.print_line()
            print(host['name'] + ' (' + hand + ')')
            print(host['id'] + ' > ' + spot['id'])
            helpers.print_line()
            print('[X] druecken und neuen TAG scannen oder [D] druecken um TAG von HOST zu loeschen')
            restart = choose('DX')
            if not restart:
                hosts.update_one({'_id': host['_id']}, 
                                 {'$pull': {'spots': {'rfid': gloves.rfid}}})
                print('TAG wurde von ' + host['id'] + ' geloescht')

        else:

            print('TAG nicht vorhanden.')
            print('Druecken sie [N] um zum Anzulegen ODER [X] und beruehren Sie einen anderen Tag.')
            restart = choose('NX')
            if not restart:
                while True:
                    host_id = input('Bitte geben sie die ID des HOSTs an, auf dem sich der TAG befindet: ')
                    host = hosts.find_one({'id': host_id})
                    if bool(host):
                        add_spot(hosts, host_id, gloves.rfid)
                        break
                    else:
                        print(host_id + ' wurde nicht gefunden.')
                        print('[ENTER] um neuen HOST anzulegen.')
                        print('[ESC] um neue HOST.ID anzugeben')
                        key = wait_for('\n\r' + chr(27))
                        if key != chr(27):
                            host_name = input('Geben Sie HOST.name ein: ')
                            print('[ENTER] um neuen HOST anzulegen.')
                            print('[ESC] um neuen TAG zu scannen.')
                            key = wait_for('\n\r' + chr(27))
                            if key != chr(27):
                                hosts.insert_one({'id': host_id, 'name': host_name})
                                print('Neuer HOST: ' + host_id + ', ' + host_name + ' wurde in Datenbank angelegt.')
                                add_spot(hosts, host_id, gloves.rfid)
                            break


def add_spot(hosts, host_id, rfid):
    print('Geben Sie eine SPOT.ID an und bestaetigen Sie mit [ENTER]:')
    spot_id = input('ACHTUNG: Wenn SPOT.ID bereits vorhanden ist, dann wird dieser einfach ueberschrieben!\n')
    spot_name = input('Geben Sie einen SPOT.name an und bestaetigen Sie mit [ENTER]: ')
    print('[ENTER] um den neuen SPOT anzulegen.')
    print('[ESC] um anderen TAG zu scannen.')
    key = wait_for('\n\r' + chr(27))
    if key == chr(27):
        return False
    hosts.update_one({'id': host_id}, 
                     {'$push': {'spots': {'id' : spot_id, 'name': spot_name, 'rfid': rfid}}})
    print('SPOT ' + spot_id + ', ' + spot_name + ' wurde angelegt')
    print('SPOT ' + spot_id + ' wurde HOST ' + host_id + ' zugewiesen')
    print('TAG ' + rfid + ' wurde angelegt.')
    print('TAG ' + rfid + ' wurde ' + host_id + ' > ' + spot_id + ' zugewiesen')
    return True


def choose(keys):
    key = wait_for(keys)
    return (key == keys[1])


def wait_for(keys):
    while True:
        key = helpers.getch()
        if key in keys:
            return key


if __name__ == "__main__":
    main()
