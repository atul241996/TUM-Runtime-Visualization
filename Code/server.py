from gevent import monkey; monkey.patch_all()
import bottle
from bottle import Bottle, route, run, request, response, HTTPResponse
import requests
import json
import threading
import time

app = Bottle()

#https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}

def get_flight_info(flightnum):
    lat,lon='',''

    return {"lat":lat, "lon":lon, "flightnum": flightnum}

WEATHER_API_KEY = 'c2ae3191ce2c8cbd500456bd45cf27fa'
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'

@route('/weather', method='GET')
def get_weather():
    flightnum = request.query.flightnum
    if not flightnum:
        response.status = 400
        return "Flight number is required"

    flight_info = get_flight_info(flightnum)
    lat, lon = flight_info['lat'], flight_info['lon']
    
    params = {
        'lat': lat,
        'lon': lon,
        'appid': WEATHER_API_KEY,
        'units': 'metric'
    }
    weather_response = requests.get(WEATHER_API_URL, params=params)
    if weather_response.status_code == 200:
        return weather_response.json()
    else:
        response.status = weather_response.status_code
        return "Failed to fetch weather data"


@route('/flightnum', method='GET')
def flightnum_handler(flightnum):
    return "Flightnum endpoint for flight: {}".format(flightnum)
