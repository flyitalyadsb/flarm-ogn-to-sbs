import datetime
import threading
import time

import pytz
import socket
import logging
from ogn.client import AprsClient
from ogn.parser import parse, ParseError

import argparse

# Setting up logging
logger = logging.getLogger("MAIN")
logger.warning("Starting Flarm ogn to sbs!")

# Parsing Arguments
parser = argparse.ArgumentParser(description="Execute the Flarm-ogn script with custom configurations.")
parser.add_argument('--host', required=True, default="localhost", help="If used with --listen-on, the "
                                                                       "address that utility binds else the address "
                                                                       "of readsb.")
parser.add_argument('--port', type=int, default=None, help="Port number.")
parser.add_argument('--listen-on', type=int, default=None, help="Listen on port number.")

parser.add_argument('--only-messages-with-icao', action="store_true", help="Forward to readsb only messages with ICAO.")
parser.add_argument('--location-filter', default=None, action="store",
                    help="Filter data by location coordinates (format: lat,long,radius). Example: 45.5,10.2,500 filters planes within 500nm from the point with latitude 45.2 and longitude 10.2")
parser.add_argument('--timezone', default="Europe/Rome", help="Timezone.")
parser.add_argument('--debug', action="store_true", help="Enable debug logging.")
args = parser.parse_args()

# Configuration
READSB_HOST = args.host
PORT = args.port
ONLY_MESSAGES_WITH_ICAO = args.only_messages_with_icao
TIMEZONE = args.timezone
LISTEN_PORT = args.listen_on
LOCATION_FILTER: str = args.location_filter

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class SBSSender:
    def __init__(self, host=None, port=None, listen_port=None):
        self.host = host
        self.port = port
        self.listen_port = listen_port
        self.socket = None
        self.server_socket = None
        self.clients = []
        if self.port:
            self.connect()
        else:
            self.setup_server()

    def connect(self):
        """Establishes a connection as a client."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        if self.listen_port:
            self.setup_server()

    def setup_server(self):
        """Sets up a server to listen for incoming client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.listen_port))
        self.server_socket.listen(5)
        logger.info(f"Listening for incoming connections on {self.host}:{self.listen_port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        """Accepts incoming clients."""
        while True:
            client_socket, addr = self.server_socket.accept()
            self.clients.append(client_socket)
            logger.info(f"Accepted connection from {addr}")

    def send_to_clients(self, message):
        """Sends a message to all connected clients."""
        for client in self.clients:
            try:
                client.sendall(message.encode())
            except socket.error as e:
                logger.error(f"Failed to send message to client: {e}")
                self.clients.remove(client)

    def send(self, message):
        """Sends the message to the server."""
        if self.socket is None:
            self.connect()
        try:
            self.socket.sendall(message.encode())
            logger.debug(f"SBS message sent: {message}")
        except socket.error as e:
            logger.error(f"Failed to send message to server: {e}")
            logger.error("Reconnecting to the server...")
            time.sleep(1)

    def close(self):
        """Closes the connection."""
        if self.socket:
            self.socket.close()
            self.socket = None

        if self.server_socket:
            for client in self.clients:
                client.close()
            self.server_socket.close()
            self.server_socket = None


# Now, instantiate the SBSSender once
sbs_sender = SBSSender(READSB_HOST, PORT, LISTEN_PORT)


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
        if PORT:
            sbs_sender.send(sbs)
        else:
            sbs_sender.send_to_clients(sbs)

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
        ",,,,,"
    ]
    sbs = ','.join(sbs_parts) + chr(13) + chr(10)  # Device Control 3 (oft. XOFF) Data Line Escape
    return sbs


# Main execution
if LOCATION_FILTER:
    tp = tuple(LOCATION_FILTER.split(","))
    filter = f"r/{tp[0]}/{tp[1]}/{tp[2]}"
    client = AprsClient(aprs_user='N0CALL', aprs_filter=filter)
else:
    client = AprsClient(aprs_user='N0CALL')
try:
    client.connect()
    client.run(callback=process_beacon, autoreconnect=True)
except KeyboardInterrupt:
    logger.info('Stopping ogn gateway due to keyboard interruption')

finally:
    client.disconnect()
