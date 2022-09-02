import datetime
import pytz
import socket

from ogn.client import AprsClient
from ogn.parser import parse, ParseError

# output
HOST = "localhost"
PORT = 40000


def process_beacon(raw_message):
    try:
        beacon = parse(raw_message, calculate_relations=True)
        if beacon['aprs_type'].startswith('position'):
            keys = beacon.keys()
            sbs = "MSG,3,0,0,"
            if "name" in keys:
                if not beacon["name"][:3] == "ICA":
                    return
            else:
                return
            if "address" in keys:
                sbs += beacon["address"] + ","
            else:
                return

            sbs += "0,"
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
            sbs += ",0,,0,0"
            code1 = chr(13)  # Device Control 3 (oft. XOFF)
            code2 = chr(10)  # Data Line Escape
            sbs += code1 + code2

            with open("D:\\sbs.txt", "wb") as f:
                f.write(sbs.encode())

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

"""
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        data = s.recv(1024)

        with open("D:\\sbs2.txt", "wb") as f:
            f.write(data)
"""

"""
with open("D:\\sbs2.txt", "rb+") as f:
    a = list(f.read())

with open("D:\\sbs.txt", "rb+") as f:
    b = list(f.read())

for i in range(len(a)):
    try:
        if a[i] == b[i]:
            continue
    except:
        print(a[i:])
"""
