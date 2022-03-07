import datetime, psutil, requests, json, os, seaborn as sns, pandas as pd, matplotlib.pyplot as plt
from influxdb import InfluxDBClient
from dotenv import load_dotenv

class TrainsScraper:
   def __init__(self, url):
      load_dotenv()
      self.user=os.getenv('USER')
      self.password=os.getenv('PASSWORD')
      self.db=os.getenv('DATABASE')
      self.host=os.getenv('HOST')
      self.port=os.getenv('PORT')
      self.measurement_name="trains_properties"
      self.json_filename="/var/www/html/jsons/trains-data.json"
      
      self.url = url

   def scrap(self):
      return requests.get(self.url).json()

   def get_average(self, li):
      return int(sum(li)/len(li))

   def connect(self):
      return InfluxDBClient(
         self.host,
         self.port,
         self.user,
         self.password,
         self.db
      )

   def init_json(self):
      obj = {
          'time': [],
         'tgv': [],
         'total': [],
         'intercites': [],
         'inoui': [],
         'ter': [],
         'ouigo': [],
         'transilien': [],
         'lyria': [],
         'ret': [],
         'sup': [],
         'avgSteps': [],
         'avgSpeed': [],
         'minSpeed': [],
         'maxSpeed': [],
         'speedIntercites': [],
         'speedTransilien': [],
         'speedTer': [],
         'speedInoui': [],
         'speedTgv': [],
         'speedLyria': [],
         'speedOuigo': []
      }

      with open(self.json_filename, 'w') as file:
         json.dump(obj, file)

   def store_in_influx(self, body):
      client = self.connect()
      client.write_points(body)

   def parse(self):
      time = datetime.datetime.utcnow()
      # get data from website
      response = self.scrap()

      # split response
      properties = response['properties']
      del properties['timestamp']
      trains = response['features']

      # variables declaration
      speedsPerCat = {}
      nb_steps, speeds = [], []
      min_speed, max_speed, average_speed, avg_steps = 0, 0, 0, 0

      # fetch json
      for train in trains:
         nb_steps.append(len(train['properties']['etapes']))
         speed = train['properties']['vitesse']
         cat = train['properties']['origine']
         if speed<350 and speed>20:
            speeds.append(speed)
         if cat not in list(speedsPerCat.keys()):
            speedsPerCat[cat] = []
         speedsPerCat[cat].append(speed)

      average_speed = int(sum(speeds)/len(speeds))
      min_speed = min(speeds)
      max_speed = max(speeds)
      avg_steps = self.get_average(nb_steps)

      # CREATE AN OBJECT
      to_store = properties
      to_store['avgSteps']=avg_steps
      to_store['avgSpeed']=average_speed
      to_store['minSpeed']=min_speed
      to_store['maxSpeed']=max_speed
      to_store['speedIntercites']=self.get_average(speedsPerCat['intercites'])
      to_store['speedTransilien']=self.get_average(speedsPerCat['transilien'])
      to_store['speedTer']=self.get_average(speedsPerCat['ter'])
      to_store['speedInoui']=self.get_average(speedsPerCat['inoui'])
      to_store['speedTgv']=self.get_average(speedsPerCat['tgv'])
      to_store['speedLyria']=self.get_average(speedsPerCat['lyria'])
      to_store['speedOuigo']=self.get_average(speedsPerCat['ouigo'])

      # LOG
      print(json.dumps(to_store, indent=2))

      # OBJECT TO STORE
      body = [
         {
            "measurement": self.measurement_name,
            "time": time,
            "fields": to_store
         }
      ]

      # store in influxdb
      self.store_in_influx(body=body)

      # store in jsons files on apache server
      # get online json file
      with open(self.json_filename, 'r') as file:
         data = json.load(file)

      # update it
      data['time'].append(str(time)),
      data['tgv'].append(to_store['tgv'])
      data['total'].append(to_store['total'])
      data['intercites'].append(to_store['intercites'])
      data['inoui'].append(to_store['inoui'])
      data['ter'].append(to_store['ter'])
      data['ouigo'].append(to_store['ouigo'])
      data['transilien'].append(to_store['transilien'])
      data['lyria'].append(to_store['lyria'])
      data['ret'].append(to_store['ret'])
      data['sup'].append(to_store['sup'])
      data['avgSteps'].append(to_store['avgSteps'])
      data['avgSpeed'].append(to_store['avgSpeed'])
      data['minSpeed'].append(to_store['minSpeed'])
      data['maxSpeed'].append(to_store['maxSpeed'])
      data['speedIntercites'].append(to_store['speedIntercites'])
      data['speedTransilien'].append(to_store['speedTransilien'])
      data['speedTer'].append(to_store['speedTer'])
      data['speedInoui'].append(to_store['speedInoui'])
      data['speedTgv'].append(to_store['speedTgv'])
      data['speedLyria'].append(to_store['speedLyria'])
      data['speedOuigo'].append(to_store['speedOuigo'])

      # save it 
      with open(self.json_filename, 'w') as file:
         json.dump(data, file, indent=2)

      print("> Process is finished!")
      
   def plot_points(self, x, xlabel, y, ylabel, color, type, filepath, title):
      plt.plot(x, y, color=color)
      plt.title(title)
      plt.xlabel(xlabel)
      plt.ylabel(ylabel)
      plt.savefig(f'{filepath}/{title}.png')

   def get_from_influx(self):
      with open('/var/www/html/jsons/trains-data.json', 'r') as json_file:
         trains = json.load(json_file)

      # TRANSFORM TIME OBJECT TO STRING
      dates = trains['time']
      dates_formatted = []
      for date in dates:
         dates_formatted.append(date[11:19])

      # NUMBER OF STEPS
      avg_steps = trains['avgSteps']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=avg_steps,
         ylabel="Number of steps per journey",
         color="blue",
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="avg_steps"
      )

      # SPEEDS PER CATEGORY
      speed_intercites = trains['speedIntercites']
      speed_transilien = trains['speedTransilien']
      speed_ter = trains['speedTer']
      speed_inoui = trains['speedInoui']
      speed_tgv = trains['speedTgv']
      speed_lyria = trains['speedLyria']
      speed_ouigo = trains['speedOuigo']


      # SPEEDS
      avg_speeds = trains['avgSpeed']
      min_speed = trains['minSpeed']
      max_speed = trains['maxSpeed']

      # DELAYED AND DELETED
      total = trains['total']
      delayed = trains['ret']
      deleted = trains['sup']

      # TRAINS CATEGORIES REPARTITION
      tgv = trains['tgv']
      intercites = trains['intercites']
      inoui = trains['inoui']
      ter = trains['ter']
      ouigo = trains['ouigo']
      transilien = trains['transilien']
      lyria = trains['lyria']

      # save pdf file and clean json file
      # self.init_json()