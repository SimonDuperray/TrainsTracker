import datetime, requests, json, os, matplotlib.pyplot as plt, time
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
      
   def plot_points(self, x, xlabel, y, ylabel, color, label, type, filepath, title, yScaleLog):
      print(f"=== {title} ===")
      for i in range(len(y)):
         print(f"{i}: item: {y[i]} -- color: {color[i]}")
         plt.plot(x, y[i], color=color[i], label=label[i])
      plt.title(title)
      plt.xlabel(xlabel)
      plt.ylabel(ylabel)
      plt.xticks(range(0, len(x), 10), rotation=45)
      plt.grid()
      plt.legend(loc="upper left")
      if yScaleLog:
         plt.yscale('log')
      plt.savefig(f'{filepath}/{title}.png')
      plt.savefig(f'/var/www/html/figures/{title}.png')
      plt.clf()

   def get_from_influx(self):
      with open('/var/www/html/jsons/trains-data.json', 'r') as json_file:
         trains = json.load(json_file)

      # TRANSFORM TIME OBJECT TO STRING
      dates = trains['time']
      dates_formatted = []
      for date in dates:
         dates_formatted.append(date[11:16])

      # NUMBER OF STEPS
      avg_steps = trains['avgSteps']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=[avg_steps],
         ylabel="Number of steps per journey",
         color=["#d93b3b"],
         label=['nb_steps'],
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="avg_steps",
         yScaleLog=False
      )

      # SPEEDS PER CATEGORY
      speed_intercites = trains['speedIntercites']
      speed_transilien = trains['speedTransilien']
      speed_ter = trains['speedTer']
      speed_inoui = trains['speedInoui']
      speed_tgv = trains['speedTgv']
      speed_lyria = trains['speedLyria']
      speed_ouigo = trains['speedOuigo']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=[speed_intercites, speed_transilien, speed_ter, speed_inoui, speed_tgv, speed_lyria, speed_ouigo],
         ylabel="Velocity (km/h)",
         color=["#a56774", "#027333", "#6e3e27", "#d99923", "#d93b3b", "#1E90FF", "purple"],
         label=['intercites', 'transilien', 'ter', 'inoui', 'tgv', 'lyria', 'ouigo'],
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="speeds_per_categories",
         yScaleLog=True
      )

      # SPEEDS
      avg_speeds = trains['avgSpeed']
      min_speed = trains['minSpeed']
      max_speed = trains['maxSpeed']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=[avg_speeds, min_speed, max_speed],
         ylabel="Velocity (km/h)",
         color=["#a56774", "#027333", "#6e3e27"],
         label=['average', 'min', 'max'],
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="extremal_speeds",
         yScaleLog=False
      )

      # DELAYED AND DELETED
      total = trains['total']
      delayed = trains['ret']
      deleted = trains['sup']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=[total, delayed, deleted],
         ylabel="Number of trains",
         color=["#a56774", "#027333", "#6e3e27"],
         label=['total', 'delayed', 'deleted'],
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="general",
         yScaleLog=True
      )

      # TRAINS CATEGORIES REPARTITION
      tgv = trains['tgv']
      intercites = trains['intercites']
      inoui = trains['inoui']
      ter = trains['ter']
      ouigo = trains['ouigo']
      transilien = trains['transilien']
      lyria = trains['lyria']
      self.plot_points(
         x=dates_formatted,
         xlabel="hour",
         y=[tgv, intercites, inoui, ter, ouigo, transilien, lyria],
         ylabel="Velocity (km/h)",
         color=["#a56774", "#027333", "#6e3e27", "#d99923", "#d93b3b", "#1E90FF", "purple"],
         label=['tgv', 'intercites', 'inoui', 'ter', 'ouigo', 'transilien', 'lyria'],
         type=None,
         filepath="/home/pi/Documents/TrainsTracker/figures",
         title="trains_categories_repartition",
         yScaleLog=True
      )

      # save pdf file and clean json file
      now = datetime.datetime.now()
      date__ = now.strftime("%d/%m/%Y %H:%M:%S")
      document_body = f'''
         <!DOCTYPE html>
         <html lang="en">
         <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TrainsReport</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
         </head>
         <body style="background-color: #102A43!important; color: #fff!important;">
            <nav style="background-color: #627D98!important;" class="navbar navbar-dark bg-primary">
               <a style="padding-left: 10px!important" class="navbar-brand" href="#">TrainsTracker</a>
               <span style="padding-right: 10px!important" class="navbar-text">
                  { date__ }
               </span>
            </nav>
            <div class="container">

               <h2 style="padding: 15px 0;" class="display-5">Evolution of number of steps per journey</h2>
               <div style="margin: 15px 0;" class="row">
                  <div class="col-md-6">
                     <img src="../figures/avg_steps.png" alt="avg_steps">
                  </div>
                  <div class="col-md-6">
                     <table class="table table-light">
                        <thead>
                        <tr>
                           <th style="color:#102A43!important;" scope="col">Minimum</th>
                           <th style="color:#102A43!important;" scope="col">Average</th>
                           <th style="color:#102A43!important;" scope="col">Maximum</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                           <td style="color:#102A43!important;">{ min(avg_steps) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(avg_steps) }</td>
                           <td style="color:#102A43!important;">{ max(avg_steps) }</td>
                        </tr>
                        </tbody>
                     </table>
                  </div>
               </div>

               <hr>
               <h2 style="padding: 15px 0;" class="display-5">Extremal speeds</h2>
               <div style="margin: 15px 0;" class="row">
                  <div class="col-md-6">
                     <img src="../figures/extremal_speeds.png" alt="extremal_speeds">
                  </div>
                  <div class="col-md-6">
                     <table class="table table-light">
                        <thead>
                        <tr>
                           <th style="color:#102A43!important;" scope="col">Label</th>
                           <th style="color:#102A43!important;" scope="col">Minimum</th>
                           <th style="color:#102A43!important;" scope="col">Average</th>
                           <th style="color:#102A43!important;" scope="col">Maximum</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Min</th>
                           <td style="color:#102A43!important;">{ min(min_speed) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(min_speed) }</td>
                           <td style="color:#102A43!important;">{ max(min_speed)}</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Avg.</th>
                           <td style="color:#102A43!important;">{ min(avg_speeds) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(avg_speeds) }</td>
                           <td style="color:#102A43!important;">{ max(avg_speeds)}</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Max</th>
                           <td style="color:#102A43!important;">{ min(max_speed) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(max_speed) }</td>
                           <td style="color:#102A43!important;">{ max(max_speed)}</td>
                        </tr>
                        </tbody>
                     </table>
                  </div>
               </div>

               <hr>
               <h2 style="padding: 15px 0;" class="display-5">General informations</h2>
               <div style="margin: 15px 0;" class="row">
                  <div class="col-md-6">
                     <img src="../figures/general.png" alt="general">
                  </div>
                  <div class="col-md-6">
                     <table class="table table-light">
                        <thead>
                        <tr>
                           <th style="color:#102A43!important;" scope="col">Label</th>
                           <th style="color:#102A43!important;" scope="col">Total</th>
                           <th style="color:#102A43!important;" scope="col">Delayed</th>
                           <th style="color:#102A43!important;" scope="col">Deleted</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Min</th>
                           <td style="color:#102A43!important;">{ min(total) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(total) }</td>
                           <td style="color:#102A43!important;">{ max(total) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Avg.</th>
                           <td style="color:#102A43!important;">{ min(delayed) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(delayed) }</td>
                           <td style="color:#102A43!important;">{ max(delayed) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Max</th>
                           <td style="color:#102A43!important;">{ min(deleted) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(deleted) }</td>
                           <td style="color:#102A43!important;">{ max(deleted) }</td>
                        </tr>
                        </tbody>
                     </table>
                  </div>
               </div>

               <hr>
               <h2 style="padding: 15px 0;" class="display-5">Speeds per category</h2>
               <div style="margin: 15px 0;" class="row">
                  <div class="col-md-6">
                     <img src="../figures/speeds_per_categories.png" alt="speeds_per_categories">
                  </div>
                  <div class="col-md-6">
                     <table class="table table-light">
                        <thead>
                        <tr>
                           <th style="color:#102A43!important;" scope="col">Label</th>
                           <th style="color:#102A43!important;" scope="col">Minimum</th>
                           <th style="color:#102A43!important;" scope="col">Average</th>
                           <th style="color:#102A43!important;" scope="col">Maximum</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Intercite</th>
                           <td style="color:#102A43!important;">{ min(speed_intercites) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_intercites) }</td>
                           <td style="color:#102A43!important;">{ max(speed_intercites) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Transilien</th>
                           <td style="color:#102A43!important;">{ min(speed_transilien) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_transilien) }</td>
                           <td style="color:#102A43!important;">{ max(speed_transilien) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Ter</th>
                           <td style="color:#102A43!important;">{ min(speed_ter) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_ter) }</td>
                           <td style="color:#102A43!important;">{ max(speed_ter) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Inoui</th>
                           <td style="color:#102A43!important;">{ min(speed_inoui) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_inoui) }</td>
                           <td style="color:#102A43!important;">{ max(speed_inoui) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Tgv</th>
                           <td style="color:#102A43!important;">{ min(speed_tgv) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_tgv) }</td>
                           <td style="color:#102A43!important;">{ max(speed_tgv) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Lyria</th>
                           <td style="color:#102A43!important;">{ min(speed_lyria) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_lyria) }</td>
                           <td style="color:#102A43!important;">{ max(speed_lyria) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Ouigo</th>
                           <td style="color:#102A43!important;">{ min(speed_ouigo) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(speed_ouigo) }</td>
                           <td style="color:#102A43!important;">{ max(speed_ouigo) }</td>
                        </tr>
                        </tbody>
                     </table>
                  </div>
               </div>

               <hr>
               <h2 style="padding: 15px 0;" class="display-5">Trains categories repartition</h2>
               <div style="margin: 15px 0;" class="row">
                  <div class="col-md-6">
                     <img src="../figures/trains_categories_repartition.png" alt="trains_categories_repartition">
                  </div>
                  <div class="col-md-6">
                     <table class="table table-light">
                        <thead>
                        <tr>
                           <th style="color:#102A43!important;" scope="col">Label</th>
                           <th style="color:#102A43!important;" scope="col">Minimum</th>
                           <th style="color:#102A43!important;" scope="col">Average</th>
                           <th style="color:#102A43!important;" scope="col">Maximum</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Intercite</th>
                           <td style="color:#102A43!important;">{ min(intercites) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(intercites) }</td>
                           <td style="color:#102A43!important;">{ max(intercites) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Transilien</th>
                           <td style="color:#102A43!important;">{ min(transilien) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(transilien) }</td>
                           <td style="color:#102A43!important;">{ max(transilien) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Ter</th>
                           <td style="color:#102A43!important;">{ min(ter) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(ter) }</td>
                           <td style="color:#102A43!important;">{ max(ter) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Inoui</th>
                           <td style="color:#102A43!important;">{ min(inoui) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(inoui) }</td>
                           <td style="color:#102A43!important;">{ max(inoui) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Tgv</th>
                           <td style="color:#102A43!important;">{ min(tgv) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(tgv) }</td>
                           <td style="color:#102A43!important;">{ max(tgv) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Lyria</th>
                           <td style="color:#102A43!important;">{ min(lyria) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(lyria) }</td>
                           <td style="color:#102A43!important;">{ max(lyria) }</td>
                        </tr>
                        <tr>
                           <th style="color:#102A43!important;" scope="row">Ouigo</th>
                           <td style="color:#102A43!important;">{ min(ouigo) }</td>
                           <td style="color:#102A43!important;">{ self.get_average(ouigo) }</td>
                           <td style="color:#102A43!important;">{ max(ouigo) }</td>
                        </tr>
                        </tbody>
                     </table>
                  </div>
               </div>

            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
         </body>
         </html>
'''

      timestamp = time.time()
      document_title = "/var/www/html/trains/"+str(timestamp)+".html"
      pdf = open(document_title, 'w')
      pdf.write(document_body)
      pdf.close()

      # clear data
      self.init_json()
