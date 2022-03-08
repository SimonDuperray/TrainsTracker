# TrainsTracker

The main goal of this project is to scrap data from <code>https://carto.graou.info/47.98779/2.09807/7.04929/0/0</code> and to do two different things. These two steps will be described in the two next sections.

## Architecture

This project proposes one Python class named <code>TrainsTracker.py</code> and two main scripts, <code>main_parse.py</code> and <code>main_writer.py</code>.

The class provides all usable methods to scrap, store, fetch data and make reports. This only class is called in the two main scripts. In the <code>main_parse.py</code> file, I scrap data from Carto Graou and the <code>main_writer.py</code> makes reports based on data fetched from JSON file.

## Grafana and InfluxDB

The first step required some configuration on my personal Raspberry Pi. I had to setup InfluxDB and Grafana services thanks to the following tutorial <code>https://simonhearne.com/2020/pi-influx-grafana/</code>.

Grafana is hosted on 192.168.X.X/300X and is reachable from a browser. InfluxDB is hosted on the default port of the RPi.

I've writed algorithm that scraps data from Carto Graou and to make simple graphs to display real data like:
- Number of steps for each journey
- Min/Max/Avg speeds (accross all categories)
- Speeds for each category of trains
- Number of delayed/deleted trains
- Number of trains for each category

All the graphs provided by Grafana are visible on the following image.

[![gafana.png](https://i.postimg.cc/sgMfFq7z/gafana.png)](https://postimg.cc/nXtfBd3S)

To fit Grafana graphs, I've scheduled cron tasks like:

```bash
*/10 * * * * /usr/bin/python /home/pi/Documents/TrainsTracker/main_parse.py > /home/pi/Documents/TrainsTracker/logs/main-parse-log.log 2>&1
```

So, the main_parse script will be ran every 10 minutes all living days to fit graphs. 

## Reports

All the data are also stored in json files hosted on the RPi's Apache server and, every day at 3:00am, main_writer script is ran with cronjob with the following command:

```bash
0 3 * * * /usr/bin/python /home/pi/Documents/TrainsTracker/main_writer.py > /home/pi/Documents/TrainsTracker/logs/main-writer-log.log 2>&1
```

This script will generate html files with a timestamp to make it unique. On this report, I plot graphs using data from JSON file and the Matplotlib library. I've made this script to give me the possibility to track possible special events. These HTML files are also available on my RPi Apache server.

[![reports.png](https://i.postimg.cc/RVD9Td8D/reports.png)](https://postimg.cc/xcMWfv9v)
