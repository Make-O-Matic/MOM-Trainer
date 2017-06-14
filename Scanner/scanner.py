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
    helpers.add_db_arguments(parser, False)

    args = parser.parse_args()

    db = helpers.db(args.dbgen)
    hosts = db['hosts']
    print('+) Datenbankverbindung hergestellt.')

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

    gloves = helpers.connected_gloves(args, 1, set_rfid)[0]
    gloves.rfid = None
    gloves.rfid_side = None
    print('+) Verbindung zu mind. einem Handschuh hergestellt.')
    print('SCANNER bereit.\n')

    got_rfid = False
    while True:
        if not got_rfid:
            print('\nzum Scannen GLOVE ueber TAG bewegen')
            helpers.print_line()
            print('oder Programm mit [ESC] beenden')
            got_rfid = raw_input_or_rfid(chr(27), user_acted, gloves)
            print('')
            if not got_rfid:
                end(gloves)
        helpers.beep()
        print(gloves.rfid_side + ':\nTAG "' + gloves.rfid + '" erkannt!\n')
        host = hosts.find_one({'spots.rfid': gloves.rfid})
        if bool(host):

            spot = hosts.find_one({'spots.rfid': gloves.rfid}, {'spots.$': 1})['spots'][0]
            print('')
            helpers.print_line()
            print('|')
            print('|' + host['name'] + ' > ' + spot['name'] + ' (' + gloves.rfid_side + ')')
            print('|' + host['id'] + ' > ' + spot['id'])
            print('|')
            helpers.print_line()
            print('\nNeuen TAG scannen oder [D] druecken um TAG von HOST zu loeschen')
            got_rfid = raw_input_or_rfid('Dd', user_acted, gloves)
            if not got_rfid:
                hosts.update_one({'_id': host['_id']}, 
                                 {'$pull': {'spots': {'rfid': gloves.rfid}}})
                print('TAG wurde von HOST"' + host['id'] + '" geloescht')

        else:

            print('TAG nicht vorhanden.')
            print('Druecken sie [N] zum Anzulegen '
                  'ODER beruehren Sie einen anderen TAG.')
            got_rfid = raw_input_or_rfid('Nn', user_acted, gloves)
            print('')
            if not got_rfid:
                while True:
                    host_id = input('Bitte geben sie die ID des HOST(.id) an, '
                        'auf dem sich der TAG befindet '
                        'und bestaetigen Sie mit [ENTER]: ')
                    host = hosts.find_one({'id': host_id})
                    if bool(host):
                        add_spot(hosts, host_id, gloves.rfid)
                        break
                    else:
                        print('\nHOST "' + host_id + '" wurde nicht gefunden.')
                        print('Bitte um Eingabe:')
                        print('+) [ENTER] um neuen HOST anzulegen')
                        print('+) [ESC] um neue HOST.ID anzugeben\n')
                        key = wait_for('\n\r' + chr(27))
                        if key != chr(27):
                            host_name = input('Geben Sie den Namen des HOST(.name) an '
                                'und bestaetigen Sie mit [ENTER]: ')
                            print('- [ENTER] um neuen HOST anzulegen')
                            print('- [ESC] um neuen TAG zu scannen\n')
                            key = wait_for('\n\r' + chr(27))
                            if key != chr(27):
                                hosts.insert_one({'id': host_id, 'name': host_name})
                                print('+) HOST "' + host_name + '" ("' + 
                                    host_id + '") wurde angelegt.')
                                add_spot(hosts, host_id, gloves.rfid)
                            break


def add_spot(hosts, host_id, rfid):
    spot_id = input('\nGeben Sie die ID des SPOT(.id) an '
        'und bestaetigen Sie mit [ENTER]:')
    spot_name = input('Geben Sie den Namen des SPOT(.name) an '
        'und bestaetigen Sie mit [ENTER]: ')
    print('\nEingaben wurden verarbeitet. Bitte um Eingabe:\n')
    print('- [ENTER] um den neuen SPOT anzulegen')
    print('- [ESC] um anderen TAG zu scannen\n')
    key = wait_for('\n\r' + chr(27))
    if key == chr(27):
        return False
    hosts.update_one({'id': host_id}, 
                     {'$push': {'spots': {'id' : spot_id, 'name': spot_name, 'rfid': rfid}}})
    print('+) SPOT "' + spot_name + '" ("' + spot_id + '") wurde angelegt')
    print('+) SPOT "' + spot_id + '" wurde HOST "' + host_id + '" zugewiesen.')
    print('+) TAG "' + rfid + '" wurde angelegt.')
    print('+) TAG "' + rfid + '" wurde "' + host_id + '" > "' + spot_id + '" zugewiesen')
    return True


def end(gloves):
    print('SCANNER wird beendet...')
    print('-) Bluetoothverbindung wird geschlossen.')
    gloves.disconnect()
    print('-) Datenbankverbindung wird getrennt')
    sys.exit()


def raw_input_or_rfid(keys, user_acted, gloves):
    try:
        got_rfid = helpers.raw_wrap(sys.stdin,
            functools.partial(input_or_rfid, prompt, keys, user_acted, gloves))
    except Exception:
        print('Verbindung zu mind. einem Handschuh wurde unterbrochen.')
        print('Programm mit [ESC] beenden.')
        wait_for(chr(27))
        end(gloves)
    return got_rfid


def input_or_rfid(keys, user_acted, gloves):
    user_acted.clear()
    old_rfid = gloves.rfid
    old_side = gloves.rfid_side
    gloves.rfid = None
    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin, user_acted.set)
    got_rfid = None
    
    async def wait_user():
        await loop.run_in_executor(None, user_acted.wait)
        
    while True:
        loop.run_until_complete(asyncio.wait([gloves.io_done, wait_user()],
            return_when=asyncio.FIRST_COMPLETED))
        if not user_acted.is_set():
            user_acted.set()
            raise Exception
        if gloves.rfid:
            if gloves.rfid != old_rfid or gloves.rfid_side != old_side:
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
