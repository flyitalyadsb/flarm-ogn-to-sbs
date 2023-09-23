import datetime
import pytz
import socket
import logging

from ogn.client import AprsClient
from ogn.parser import parse, ParseError


# output
HOST = "readsb"
PORT = 3022
solo_messaggi_con_icao = False

logger = logging.getLogger("logger")
logger.warning("Flarm-ogn in partenza!")

def process_beacon(raw_message):
    try:
        beacon = parse(raw_message, calculate_relations=True)
        if beacon['aprs_type'].startswith('position'):
            logger.debug(f"beacon: {beacon}")
            keys = beacon.keys()
            sbs = "MSG,3,1,1,"
            if "name" in keys:
                if solo_messaggi_con_icao:
                    if not beacon["name"][:3] == "ICA":
                        return
            else:
                return

            if "address" in keys:
                sbs += beacon["address"] + ","
            else:
                return

            sbs += "1,"
            now = datetime.datetime.now(pytz.timezone('Europe/Rome'))
            time = beacon["timestamp"]
            date = time.strftime("%Y/%m/%d")
            micr = time.strftime("%f")[:3]
            hour = time.strftime("%X.") + micr
            sbs += date + ","
            sbs += hour + ","
            date = now.strftime("%Y/%m/%d")
            micr = now.strftime("%f")[:3]
            hour = now.strftime("%X.") + micr
            sbs += date + ","  ####
            sbs += hour + ","  ####

            sbs += ","

            if "altitude" in keys:
                if beacon["altitude"]:
                    sbs += str(int(beacon["altitude"])) + ","
                #sbs += ","
            else:
                sbs += ","
            if "ground_speed" in keys:
                sbs += str(beacon["ground_speed"]) + ","
            else:
                sbs += ","
            if "track" in keys:
                sbs += str(beacon["track"]) + ","
            else:
                sbs += ","
            if "latitude" in keys:
                sbs += str(beacon["latitude"]) + ","
            else:
                return
            if "longitude" in keys:
                sbs += str(beacon["longitude"]) + ","
            else:
                return
            # if "climb_rate" in keys:
            #    sbs += str(beacon["climb_rate"]) + ","
            # else:
            #    sbs += ","
            sbs += ",,,,,"
            code1 = chr(13)  # Device Control 3 (oft. XOFF)
            code2 = chr(10)  # Data Line Escape
            sbs += code1 + code2
            logger.debug(f"Messaggio SBS: {sbs}")
            #with open("D:\\sbs.txt", "wb") as f:
            #    f.write(sbs.encode())


            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(sbs.encode())

    except ParseError as e:
        print('Error, {}'.format(e.message))
    except NotImplementedError as e:
        print('{}: {}'.format(e, raw_message))
    except AttributeError as e:
        print(e)


client = AprsClient(aprs_user='N0CALL')
client.connect()

try:
    client.run(callback=process_beacon, autoreconnect=True)
except KeyboardInterrupt:
    print('\nStop ogn gateway')
    client.disconnect()
