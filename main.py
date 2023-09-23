import datetime
import pytz
import socket
import logging
from ogn.client import AprsClient
from ogn.parser import parse, ParseError

import argparse

# Parsing Arguments
parser = argparse.ArgumentParser(description="Execute the Flarm-ogn script with custom configurations.")
parser.add_argument('--readsb-host', default="localhost", help="Host for READSB.")
parser.add_argument('--port', type=int, default=3022, help="Port number.")
parser.add_argument('--only-messages-with-icao', action="store_true", help="Forward to readsb only messages with ICAO.")
parser.add_argument('--timezone', default="Europe/Rome", help="Timezone.")
args = parser.parse_args()

# Configuration
READSB_HOST = args.readsb_host
PORT = args.port
ONLY_MESSAGES_WITH_ICAO = args.only_messages_with_icao
TIMEZONE = args.timezone

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MAIN")
logger.warning("Starting Flarm ogn to sbs!")


def process_beacon(raw_message):
    try:
        beacon = parse(raw_message, calculate_relations=True)

        if not beacon.get('aprs_type', '').startswith('position'):
            return

        # Check for mandatory fields
        if not all(key in beacon for key in ["name", "address", "latitude", "longitude"]):
            return

        # Check if message should contain ICAO
        if ONLY_MESSAGES_WITH_ICAO and not beacon["name"].startswith("ICA"):
            return

        sbs = build_sbs_message(beacon)
        send_to_server(sbs)

    except (ParseError, NotImplementedError, AttributeError) as e:
        logger.debug(f"Error processing beacon: {e}")


def build_sbs_message(beacon):
    """Constructs the SBS message."""
    now = datetime.datetime.now(pytz.timezone(TIMEZONE))

    # Create base SBS string with required fields
    sbs_parts = [
        "MSG,3,1,1",
        beacon["address"],
        "1",
        beacon["timestamp"].strftime("%Y/%m/%d,%X.%f")[:23],
        now.strftime("%Y/%m/%d,%X.%f")[:23],
        "",
        str(int(beacon.get("altitude"))) if beacon.get("altitude") and beacon["altitude"] else "",
        str(beacon.get("ground_speed", "")) or "",
        str(beacon.get("track", "")) or "",
        str(beacon["latitude"]),
        str(beacon["longitude"]),
        ",,,,",
        chr(13) + chr(10)
    ]

    return ','.join(sbs_parts)


def send_to_server(message):
    """Sends the SBS message to the server."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(message)

            s.connect((READSB_HOST, PORT))
            s.sendall(message.encode())
            logger.debug(f"SBS message sent: {message}")
    except socket.error as e:
        logger.error(f"Failed to send message to server: {e}")
        # TODO reconnect


# Main execution
client = AprsClient(aprs_user='N0CALL')

try:
    client.connect()
    client.run(callback=process_beacon, autoreconnect=True)
except KeyboardInterrupt:
    logger.info('Stopping ogn gateway due to keyboard interruption')

finally:
    client.disconnect()