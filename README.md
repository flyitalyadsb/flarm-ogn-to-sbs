# ✈️ Flarm-ogn-to-SBS

A powerful small and light utility that captures data from the **Flarm OGN (Open Glider Network)** and transforms it
into a Basestation
**SBS** stream, subsequently forwarding it to ADS-B servers such as readsb, dump1090-fa, or Virtual Radar Server.

> 📡 Running a server? Boost its data with this additional feed!

## 🌟 Features

- 🔄 Converts Flarm OGN data to the SBS format.
- 🔗 Forwards the data to prevalent ADS-B servers.
- 🔍 Option to process only gliders, paragliders, etc., broadcasting a genuine ICAO code and filter data by location coordinates

## 🛠️ Installation

1. Clone the repository:
   ```
   git clone https://github.com/flyitalyadsb/flarm-ogn-to-sbs.git
   cd flarm-ogn-to-sbs
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## ⚙️ Configuration and Execution with Docker Compose

1. Navigate to your repository's directory.

2. Use Docker Compose to run the service:
   ```
   docker-compose up -d
   ```

3. If you need to make configuration changes, modify the `docker-compose.yml` file and restart the service:

   ```
   docker-compose down && docker-compose up -d
   ```

## Script Options

Here's a breakdown of the available script options:

- `--host`: If used with `--listen-on`, specifies the address the utility binds to; otherwise, it's the address of readsb. Default is `localhost`.

- `--port`: Specifies the port number to forward the SBS data.

- `--listen-on`: Sets the utility to listen mode on the given port number. Useful if you want the utility to act as a server and wait for incoming connections.

- `--only-messages-with-icao`: If set, the utility will only forward messages to readsb that contain an ICAO address.

- `--location-filter`: "If used, the script will send only data within a radius from some coordinates (format: lat,long,radius)

- `--timezone`: Specifies the timezone for timestamping. Default is `Europe/Rome`.

- `--debug`: Enables detailed debug logging.

## 🔗 Useful Links

- [OGN](https://www.glidernet.org/)
- [readsb](https://github.com/wiedehopf/readsb)
- [dump1090-fa](https://github.com/flightaware/dump1090)
- [Virtual Radar Server](http://www.virtualradarserver.co.uk/)

## 🤝 Contributing

Want to contribute? **Your assistance would be invaluable!** Start by creating a Pull Request or opening an Issue.

---

> 🚀 Enhance your server's capabilities by integrating **Flarm-ogn-to-SBS**!

