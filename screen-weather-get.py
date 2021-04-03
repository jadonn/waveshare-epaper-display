#!/usr/bin/python

import datetime
import sys
import os
import json
import logging
from weather_providers import climacell, openweathermap
from utility import is_stale, update_svg, configure_logging

configure_logging()

def get_cached_weather(filename, ttl):
    if is_stale(filename, ttl):
        logging.info("Weather cache is stale.")
        return None

    logging.info("Found in cache")
    with open(filename, 'r') as file:
        return json.loads(file.read())
    

def cache_weather_data(filename, weather_data):
    if weather_data:
        with open(filename, 'w') as text_file:
            json.dump(weather_data, text_file)


def main():

    # gather relevant environment configs
    climacell_apikey=os.getenv("CLIMACELL_APIKEY")
    openweathermap_apikey=os.getenv("OPENWEATHERMAP_APIKEY","9f3eab3dcf9a0d02e31adfc36ba307b7")
    
    if not climacell_apikey:
        logging.error("CLIMACELL_APIKEY is missing")
        sys.exit(1)

    weather_format=os.getenv("WEATHER_FORMAT", "CELSIUS")
    if (weather_format == "CELSIUS"):
        units = "metric"
    else:
        units = "imperial"

    location_lat = os.getenv("WEATHER_LATITUDE","51.3656")
    location_long = os.getenv("WEATHER_LONGITUDE","-0.1963")

    # TTL for refetching of JSON
    ttl = float(os.getenv("WEATHER_TTL", 1 * 60 * 60))
    cache_weather_file = "weather-cache.json"

    if openweathermap_apikey:
        logging.info("Gathering weather from OpenWeatherMap")
        weather = openweathermap.get_weather(openweathermap_apikey, location_lat, location_long, units)
        logging.debug(weather)
    elif climacell_apikey:
        logging.info("Gathering weather from Climacell")

        weather = get_cached_weather(cache_weather_file, ttl)
        if not weather:
            weather = climacell.get_weather(climacell_apikey, location_lat, location_long, units)
            cache_weather_data(cache_weather_file, weather)
        logging.info("weather - {}".format(weather))

    if not weather:
        logging.error("Unable to fetch weather payload. SVG will not be updated.")
        return

    degrees = "°C" if units == "metric" else "°F"

    output_dict = {
        'LOW_ONE': "{}{}".format(str(round(weather['temperatureMin'])), degrees),
        'HIGH_ONE': "{}{}".format(str(round(weather['temperatureMax'])), degrees),
        'ICON_ONE': weather["icon"],
        'WEATHER_DESC': weather["description"],
        'TIME_NOW': datetime.datetime.now().strftime("%-I:%M %p"),
        'DAY_ONE': datetime.datetime.now().strftime("%b %-d, %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE': "" # unused
    }

    logging.debug("main() - {}".format(output_dict))

    logging.info("Updating SVG")
    template_svg_filename = 'screen-template.svg'
    output_svg_filename = 'screen-output-weather.svg'
    update_svg(template_svg_filename, output_svg_filename, output_dict)

if __name__ == "__main__":
    main()
