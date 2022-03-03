import datetime, psutil, requests, json, os
from influxdb import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

USER=os.getenv('USER')
PASSWORD=os.getenv('PASSWORD')
DB=os.getenv('DATABASE')
HOST=os.getenv('HOST')
PORT=os.getenv('PORT')

MEASUREMENT_NAME="trains_properties"

time = datetime.datetime.utcnow()

trains_data = requests.get('https://graou.info/trains.geojson').json()

trains_properties = trains_data['properties']
del trains_properties['timestamp']
print(json.dumps(trains_properties, indent=2))

# STORE DATA IN DATABASE
body = [
    {
        "measurement": MEASUREMENT_NAME,
        "time": time,
        "fields": trains_properties
    }
]

ifclient = InfluxDBClient(HOST, PORT, USER, PASSWORD, DB)
ifclient.write_points(body)

print("> process finished")
