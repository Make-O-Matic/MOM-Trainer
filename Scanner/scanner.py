#!/usr/bin/env python

import argparse
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import functools
import threading
import asyncio
import helpers

def main():
    parser = argparse.ArgumentParser(description='tagreader.')
    helpers.add_MAC_arguments(parser)
    helpers.add_db_arguments(parser)
    
    args = parser.parse_args()
    
    db = helpers.db(args)
    hosts = db['hosts']
    print('Datenbankverbindung hergestellt.')

    user_acted = threading.Event()
    gloves = None
    def set_rfid(rfid, left):
        if user_acted.is_set():
            return
        gloves.rfid = rfid
        gloves.rfid_side = 'R'
        if left:
            gloves.rfid_side = 'L'
        user_acted.set()

    gloves = helpers.connected_gloves(args, 1, set_rfid)
    hand = 'L'
    if gloves.state == 2:
        hand = 'R'
    print('Verbindung zu mind. einem Handschuh hergestellt.')
    print('SCANNER bereit.')

    got_rfid = False
    while True:
        if not got_rfid:
            user_acted.clear()
            print('Bewegen sie einen GLOVE ueber einen TAG um diesen auszulesen oder neu anzulegen')
            user_acted.wait()
        print(gloves.rfid_side + ': TAG "' + gloves.rfid + '" erkannt!')
        host = hosts.find_one({'spots.rfid': gloves.rfid})
        if bool(host):

            spot = hosts.find_one({'spots.rfid': gloves.rfid}, {'spots.$': 1})['spots'][0]
            helpers.print_line()
            print(host['name'] + ' > ' + spot['name'] + ' (' + gloves.rfid_side + ')')
            print(host['id'] + ' > ' + spot['id'])
            helpers.print_line()
            got_rfid = raw_input_or_rfid(
                'Neuen TAG scannen oder [D] druecken um TAG von HOST zu loeschen',
                'Dd', user_acted, gloves)
            if not got_rfid:
                hosts.update_one({'_id': host['_id']}, 
                                 {'$pull': {'spots': {'rfid': gloves.rfid}}})
                print('TAG wurde von ' + host['id'] + ' geloescht')

        else:

            print('TAG nicht vorhanden.')
            got_rfid = raw_input_or_rfid(
                'Druecken sie [N] um zum Anzulegen ODER beruehren Sie einen anderen Tag.',
                'Nn', user_acted, gloves)
            if not got_rfid:
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


def raw_input_or_rfid(prompt, keys, user_acted, gloves):
    got_rfid = helpers.raw_wrap(sys.stdin, 
        functools.partial(input_or_rfid, prompt, keys, user_acted, gloves))
    print('')
    return got_rfid


def input_or_rfid(prompt, keys, user_acted, gloves):
    user_acted.clear()
    old_rfid = gloves.rfid
    gloves.rfid = None
    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin, user_acted.set)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    got_rfid = None
    
    async def wait():
        await loop.run_in_executor(None, user_acted.wait)
    
    while True:
        loop.run_until_complete(wait())
        if gloves.rfid:
            if gloves.rfid != old_rfid:
                got_rfid = True
                break
            gloves.rfid = None
        else:
            key = sys.stdin.read(1)
            if key in keys:
                got_rfid = False
                break
        user_acted.clear()

    loop.remove_reader(sys.stdin)
    if not got_rfid:
        gloves.rfid = old_rfid
    return got_rfid


def wait_for(keys):
    while True:
        key = helpers.getch()
        if key in keys:
            return key


if __name__ == "__main__":
    main()
