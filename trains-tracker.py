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

response = requests.get('https://graou.info/trains.geojson').json()

properties = response['properties']
del properties['timestamp']

trains = response['features']

# AVERAGE NUMBER OF STEPS and SPEEDS
nbSteps, speeds = [], []
minSpeed, maxSpeed, avgSpeed, avgSteps = 0, 0, 0, 0

for train in trains:
    nbSteps.append(len(train['properties']['etapes']))
    speed = train['properties']['vitesse']
    if speed<350 and speed>20:
        speeds.append(speed)

avgSpeed = int(sum(speeds)/len(speeds))
minSpeed = min(speeds)
maxSpeed = max(speeds)
avgSteps = int(round(sum(nbSteps)/len(nbSteps), 0))

# CREATE TO STORE OBJECT
toStore = properties
toStore['avgSteps']=avgSteps
toStore['avgSpeed']=avgSpeed
toStore['minSpeed']=minSpeed
toStore['maxSpeed']=maxSpeed

print(json.dumps(toStore, indent=2))

# STORE DATA IN DATABASE
body = [
    {
        "measurement": MEASUREMENT_NAME,
        "time": time,
        "fields": toStore
    }
]

ifclient = InfluxDBClient(HOST, PORT, USER, PASSWORD, DB)
ifclient.write_points(body)

print("> process finished")
