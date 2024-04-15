from gevent import monkey; monkey.patch_all()
import random
import bottle
import os 
import csv
from bottle import Bottle, route, run, request, response, HTTPResponse
import requests
import json
import threading
import time
from datetime import datetime
import logging
import chardet
import pandas as pd

instance_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
log_filename = f'app_{instance_timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

with open('instance_numbers.txt', 'a') as file:
        file.write(str(instance_timestamp) + '\n')

app = Bottle()

api_key = ''
app.debug = True
aircraft_icao24 = '3C64ED'
flight_num = aircraft_icao24
lat_g='48.26260775254051'
lon_g='11.668052070687509'
flight_status_g=None
flight_status_unchanged = True
startRecord = True
flight_already_active = False
flight_data=None
flight_not_landed=True
weather_data = None
previous_flight_status = None

WEATHER_API_KEY = ''
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'

# def get_random_aircraft_icao24(flights):
#     selected_flight = random.choice(flights)
#     return selected_flight["aircraft"]["icao24"]

def get_flight_info(api_key, aircraft_icao24):
    global flight_num, lat_g, lon_g, flight_status_g, flight_status_unchanged, flight_already_active, flight_data, flight_not_landed, previous_flight_status, startRecord
    previous_flight_status = previous_flight_status
    time.sleep(120)
    
    while True:
        try:
            request_time = datetime.now()
            url = f"https://aviation-edge.com/v2/public/flights?key={api_key}"
            params = {'aircraftIcao24': aircraft_icao24}
            # logging.info(f"Requesting URL: {url} with params: {params}")
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                try:
                    flights = response.json()
                    if len(flights) > 0:
                        flight = flights[0]
                        
                        updated_time = datetime.fromtimestamp(flight['system']['updated']).strftime('%d-%b-%Y %I:%M:%S %p')
                        
                        flight_num = flight['flight']['iataNumber']
                        lat_g = flight['geography']['latitude']
                        lon_g = flight['geography']['longitude']
                        flight_status_g = flight['status']
                        flight_already_active = (flight_status_g == "en-route")
                        flight_not_landed = (flight_status_g != "landed")
                        flight_data = flight
                        
                        if flight_status_g == previous_flight_status:
                            flight_status_unchanged = True
                        else:
                            flight_status_unchanged = False
                            previous_flight_status = flight_status_g
                        
                        if flight_status_g == "landed" or flight_status_g == "unknown":
                            startRecord = False
                            flight_not_landed = False
                        
                        logging.info(f"flight_num:{flight_num}, Lat:{lat_g}, Lon:{lon_g}, Status:{flight_status_g}, Last Location Updated:{updated_time}, Request Time:{request_time.strftime('%d-%b-%Y %I:%M:%S %p')}")
                    else:
                        logging.info("No data received")
                    logging.info("Request made to Flight API")
                except json.JSONDecodeError:
                    logging.error("Failed to decode JSON from the response")
            else:
                logging.error(f"Failed to retrieve data: {response.status_code}, Response body: {response.text}")
        except Exception as e:
            logging.error("error occurred in get_flight_info", exc_info=True)

flight_data_thread = threading.Thread(target=get_flight_info, args=(api_key, aircraft_icao24))
flight_data_thread.daemon = True
flight_data_thread.start()

def get_weather():
    global lat_g,lon_g, WEATHER_API_KEY, weather_data, startRecord, flight_status_g
    if flight_status_g == "landed":
        startRecord = False
    while True:
        try:
            params = {'lat': lat_g, 'lon': lon_g, 'appid': WEATHER_API_KEY, 'units': 'metric'}
            weather_response = requests.get(WEATHER_API_URL, params=params) 
            weather_data = weather_response.json()
            logging.info("Request made to Weather API")
            logging.info(weather_data)

        except Exception as e:
            logging.error("Error occurred in get_weather: %s", e, exc_info=True)
        time.sleep(100) 

weather_thread = threading.Thread(target=get_weather)
weather_thread.daemon = True
weather_thread.start()

@app.route('/flightnumber',method='GET')
def flightnum():
    global flight_num, aircraft_icao24
    # logging.info('flight_num')
    # logging.info(flight_num)
    # logging.info('aircraft_icao24')
    # logging.info(aircraft_icao24)
    
    # url = f"https://aviation-edge.com/v2/public/flights?key={api_key}"
    # params = {'status': 'en-route'}
    # response = requests.get(url, params=params)
    # if response.status_code == 200:
    #     if aircraft_icao24 == '':
    #         selected_flight = random.choice(response.json())
    #         aircraft_icao24 = selected_flight["aircraft"]["icao24"]
    
    # flight_num = aircraft_icao24
    # logging.info('flight_num')
    # logging.info(flight_num)
    # logging.info('aircraft_icao24')
    # logging.info(aircraft_icao24)
    # logging.info("FlightNumber check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps({'FlightName': flight_num}))

@app.route('/weather',method='GET')
def get_weather_request():
    global startRecord, weather_data
    # logging.info("Weather check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps({'startRecord': startRecord,'weather':weather_data}))

@app.route('/scheduled',method='GET')
def flightScheduled():
    global flight_num, flight_status_g, startRecord, flight_status_unchanged, flight_already_active, flight_data
    response_data = {'flight_status': flight_status_g,'flight_status_unchanged': flight_status_unchanged, 'startRecord':startRecord,'flight_already_active':flight_already_active,'flight_data':flight_data}
    # logging.info("scheduled check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps(response_data))
        

@app.route('/statuscheck',method='GET')
def getFlightStatus():
    global flight_status_g, flight_status_unchanged, startRecord, flight_already_active, flight_not_landed, flight_data
    response_data = {'flight_status': flight_status_g,'flight_status_unchanged': flight_status_unchanged, 'startRecord':startRecord,'flight_data':flight_data,'flight_already_active':flight_already_active,'flight_not_landed':flight_not_landed}
    # logging.info("statuscheck check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps(response_data))

@app.route('/flightactive',method='GET')
def flightactive():
    global flight_status_g, flight_status_unchanged, startRecord,flight_data
    response_data = {'flight_status': flight_status_g,'flight_status_unchanged': flight_status_unchanged, 'startRecord':startRecord,'flight_data':flight_data}
    # logging.info("flightactive check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps(response_data))

@app.route('/flightlanded',method='GET')
def flightlanded():
    global flight_status_g, flight_data, flight_not_landed,flight_status_unchanged
    response_data = {'flight_status': flight_status_g,'flight_data':flight_data,'flight_not_landed':flight_not_landed}
    # logging.info("flightlanded check here")
    return bottle.HTTPResponse(status=200,headers={'content-type':'application/json'},body=json.dumps(response_data))


weather_final = {}
flight_final = {}
process_events = {}
@app.route('/',method='POST')
def record():
    global instance_timestamp, process_events
    body = bottle.request.body.read()
    # logging.info('body')
    # logging.info(body)
    data = body.decode('utf-8') if isinstance(body, bytes) else body
    parts = [part for part in data.split('--Time_is_an_illusion._Lunchtime_doubly_so.0xriddldata') if part.strip()][3]
    # logging.info('parts from part for part in data.split("--Time_is_an_illusion._Lunchtime_doubly_so.0xriddldata") if part.strip()][3]')
    # logging.info(parts)
    parts = [part for part in parts.split('\r\n\r\n') if part.strip()][1]
    # logging.info('parts from part for part in parts.split if part.strip()][1]')
    # logging.info(parts)
    contents = json.loads(parts)['content']
    # logging.info('contents')
    # logging.info(contents)
    filtered_data = {key: value for key, value in contents.items() if 'value' in key}
    # logging.info('filtered_data')
    # logging.info(filtered_data)
    if filtered_data:
        final = filtered_data['values']
        weather = {key: value for key, value in final.items() if 'weather' in key}
        flight = {key: value for key, value in final.items() if 'flight_data' in key}
        # logging.info("weather")
        # logging.info(weather)
        # logging.info("flight")
        # logging.info(flight)
        if weather:
            logging.info("weather from the log")
            logging.info(weather)
            final = weather['weather']
            global weather_final
            weather_final = final
            file_exists = os.path.isfile(f'weather.csv')
            # {'coord': {'lon':, 'lat':}, 'weather': [{'id':, 'main':, 'description':, 'icon':}], 'base':, 'main': {'temp':, 'feels_like':, 'temp_min':, 'temp_max':, 'pressure':, 'humidity':}, 'visibility':, 'wind': {'speed':, 'deg':}, 'clouds': {'all':}, 'dt':, 'sys': {'type':, 'id':, 'country':, 'sunrise':, 'sunset':}, 'timezone':, 'id':, 'name':, 'cod':}
            with open(f'weather.csv', 'a', newline='',encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['instance','lon', 'lat','base','visibility', 'weather_main', 'weather_description', 'temp', 'feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity', 'speed', 'deg', 'all_clouds', 'dt', 'country', 'sunrise', 'sunset', 'timezone', 'city_id', 'city_name', 'cod'])
                
                instance = instance_timestamp
                lon = final['coord']['lon']
                lat = final['coord']['lat']
                weather = final['weather'][0]
                main = final['main']
                speed = final['wind']['speed']
                deg = final['wind']['deg']
                all_clouds = final['clouds']['all']
                dt = final['dt']
                base = final['base']
                visibility = final['visibility']
                country = final['sys']['country']
                sunrise = final['sys']['sunrise']
                sunset = final['sys']['sunset']
                timezone = final['timezone']
                city_id = final['id']
                city_name = final['name']
                cod = final['cod']
                writer.writerow([instance,lon, lat,base,visibility, weather['main'], weather['description'], main['temp'], main['feels_like'], main['temp_min'], main['temp_max'], main['pressure'], main['humidity'], speed, deg, all_clouds, dt, country, sunrise, sunset, timezone, city_id, city_name, cod])
        if flight:
            logging.info("flight info from the log")
            logging.info(flight)
            fflight = flight['flight_data']
            global flight_final
            flight_final = flight
            file_exists = os.path.isfile(f'flight_data.csv') 
            # {'flight_data': {'aircraft': {'iataCode': '', 'icao24': '', 'icaoCode': '', 'regNumber': ''}, 'airline': {'iataCode': '', 'icaoCode': ''}, 'arrival': {'iataCode': '', 'icaoCode': ''}, 'departure': {'iataCode': '', 'icaoCode': ''}, 'flight': {'iataNumber': '', 'icaoNumber': '', 'number': ''}, 'geography': {'altitude':, 'direction': , 'latitude':, 'longitude': }, 'speed': {'horizontal': , 'isGround':, 'vspeed':}, 'status': '', 'system': {'squawk': , 'updated':}}}
            with open(f'flight_data.csv', 'a', newline='',encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['instance','status','aircraftiataCode', 'aircrafticao24','airlineiataCode','flightnumber','flighticaoNumber','flightiataNumber','departureicaoCode','departureiataCode','arrivalicaoCode','arrivaliataCode','airlineicaoCode','aircraftregNumber', 'aircrafticaoCode', 'altitude', 'direction', 'latitude', 'longitude', 'horizontal_speed', 'vspeed', 'isGround','squawk', 'Last_updated'])
                
                instance = instance_timestamp
                aircraftiataCode = fflight['aircraft']['iataCode']
                aircrafticao24 = fflight['aircraft']['icao24']
                aircrafticaoCode = fflight['aircraft']['icaoCode']
                aircraftregNumber = fflight['aircraft']['regNumber']
                airlineiataCode = fflight['airline']['iataCode']
                airlineicaoCode = fflight['airline']['icaoCode']
                arrivaliataCode = fflight['arrival']['iataCode']
                arrivalicaoCode = fflight['arrival']['icaoCode']
                departureiataCode = fflight['departure']['iataCode']
                departureicaoCode = fflight['departure']['icaoCode']
                flightiataNumber = fflight['flight']['iataNumber']
                flighticaoNumber = fflight['flight']['icaoNumber']
                flightnumber = fflight['flight']['number']
                altitude = fflight['geography']['altitude']
                direction = fflight['geography']['direction']
                latitude = fflight['geography']['latitude']
                longitude = fflight['geography']['longitude']
                horizontal_speed = fflight['speed']['horizontal']
                vspeed = fflight['speed']['vspeed']
                isGround = fflight['speed']['isGround']
                status = fflight['status']
                squawk = fflight['system']['squawk']
                Last_updated = datetime.fromtimestamp(fflight['system']['updated']).strftime('%d-%b-%Y %I:%M:%S %p')  
                writer.writerow([instance,status,aircraftiataCode, aircrafticao24,airlineiataCode,flightnumber,flighticaoNumber,flightiataNumber,departureicaoCode,departureiataCode,arrivalicaoCode,arrivaliataCode,airlineicaoCode,aircraftregNumber, aircrafticaoCode, altitude, direction, latitude, longitude, horizontal_speed, vspeed, isGround,squawk, Last_updated])

def stream_data():
    global instance_timestamp, flight_final, weather_final, process_events
    while True:
        data = json.dumps({
            "flight_data": flight_final,
            "weather_data": weather_final,
            "instance_timestamp":instance_timestamp,
            "process_events":process_events
        })
        yield f"data: {data}\n\n"
        # logging.info("sse event dumps")
        # logging.info(data)
        time.sleep(10)  

@app.route('/sse', method='GET')
def sse_request():
    global weather_final, flight_final, instance_timestamp, process_events
    response.content_type = 'text/event-stream'
    response.cache_control = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return stream_data()

def stream_old_data():
    # with open('instance_numbers.txt', 'r') as file:
    #     lines = file.readlines()
    #     if lines:
    #         latest_instance_timestamp = lines[-1].strip()
    #     else:
    #         return HTTPResponse(status=404, body='No instance numbers found.')
    latest_instance_timestamp="20240404-144416"
    with open('weather.csv', 'rb') as file:
        raw_data = file.read(10000) 
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    weather_df = pd.read_csv('weather.csv',encoding=encoding)
    flight_data_df = pd.read_csv('flight_data.csv',encoding=encoding)
    weather_filtered = weather_df[weather_df['instance_timestamp'] == latest_instance_timestamp]
    flight_data_filtered = flight_data_df[flight_data_df['instance_timestamp'] == latest_instance_timestamp]

    if not weather_filtered.empty and not flight_data_filtered.empty:
        weather_old = weather_filtered.iloc[0].to_dict()
        flight_old = flight_data_filtered.iloc[0].to_dict()
        
        logging.info("weather_old")
        logging.info(weather_old)

        logging.info("flight_old")
        logging.info(flight_old)

        formatted_data = {
            'flight_data':{
            'flight_data': {
                'aircraft': {
                    'iataCode': flight_old.get('iataCode'),
                    'icao24': flight_old.get('icao24'),
                    'icaoCode': flight_old.get('icaoCode'),
                    'regNumber': flight_old.get('regNumber')
                },
                'airline': {
                    'iataCode': flight_old.get('airlineIataCode'),
                    'icaoCode': flight_old.get('airlineIcaoCode')
                },
                'arrival': {
                    'iataCode': flight_old.get('arrivalIata'),
                    'icaoCode': flight_old.get('arrivalIcao')
                },
                'departure': {
                    'iataCode': flight_old.get('departureIata'),
                    'icaoCode': flight_old.get('departureIcao')
                },
                'flight': {
                    'iataNumber': flight_old.get('iataNumber'),
                    'icaoNumber': flight_old.get('icaoNumber'),
                    'number': flight_old.get('flightNumber')
                },
                'geography': {
                    'altitude': flight_old.get('altitude'),
                    'direction': flight_old.get('direction'),
                    'latitude': flight_old.get('latitude'),
                    'longitude': flight_old.get('longitude')
                },
                'speed': {
                    'horizontal': flight_old.get('horizontal_speed'),
                    'isGround': flight_old.get('isGround'),
                    'vspeed': flight_old.get('vspeed')
                },
                'status': flight_old.get('status'),
                'system': {
                    'squawk': flight_old.get('squawk'),
                    'updated': flight_old.get('Last_updated')
                }
            }},
            'weather_data':{
                'coord': {
                    'lon':  weather_old.get('lon'),
                    'lat':  weather_old.get('lat')
                },
                'weather': [{
                    'id':  weather_old.get('weatherId'),
                    'main':  weather_old.get('main'),
                    'description':  weather_old.get('description'),
                    'icon':  weather_old.get('icon')
                }],
                'base': 'stations',
                'main': {
                    'temp':  weather_old.get('temp'),
                    'feels_like':  weather_old.get('feels_like'),
                    'temp_min':  weather_old.get('temp_min'),
                    'temp_max':  weather_old.get('temp_max'),
                    'pressure':  weather_old.get('pressure'),
                    'humidity':  weather_old.get('humidity')
                },
                'visibility':  weather_old.get('visibility'),
                'wind': {
                    'speed':  weather_old.get('speed'),
                    'deg':  weather_old.get('deg')
                },
                'clouds': {
                    'all':  weather_old.get('all')
                },
                'dt':  weather_old.get('dt'),
                'sys': {
                'type':  weather_old.get('sysType'),
                'id':  weather_old.get('sysId'),
                'country':  weather_old.get('country'),
                'sunrise':  weather_old.get('sunrise'),
                'sunset':  weather_old.get('sunset')
                },
                'timezone':  weather_old.get('timezone'),
                'id':  weather_old.get('id'),
                'name':  weather_old.get('name'),
                'cod':  weather_old.get('cod')
            },
            'instance_timestamp': latest_instance_timestamp,
            'process_events':process_events
        }

        while True:
            data = json.dumps(formatted_data)
            yield f"data: {formatted_data}\n\n"
            logging.info("sse -- old data event dumps")
            logging.info(formatted_data)
            time.sleep(10)
    else:
        logging.error("No data available for the provided timestamp.")  

@app.route('/sseold', method='GET')
def sse_request():
    response.content_type = 'text/event-stream'
    response.cache_control = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return stream_old_data()


if __name__ == '__main__':
    bottle.run(app, host='::', port=9000, server='gevent')
