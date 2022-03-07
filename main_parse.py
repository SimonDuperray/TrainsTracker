from TrainsScraper import TrainsScraper

url = "https://graou.info/trains.geojson"

trains = TrainsScraper(url=url)

trains.parse()