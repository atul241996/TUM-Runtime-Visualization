from gevent import monkey; monkey.patch_all()
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

instance_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
log_filename = f'app_{instance_timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

with open('instance_numbers.txt', 'a') as file:
        file.write(str(instance_timestamp) + '\n')

app = Bottle()

api_key = ''
app.debug = True
aircraft_icao24 = '3C64EC'
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

def get_flight_info(api_key, aircraft_icao24):
    global flight_num, lat_g, lon_g, flight_status_g, flight_status_unchanged, flight_already_active, flight_data, flight_not_landed, previous_flight_status, startRecord
    previous_flight_status = previous_flight_status
    
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
        time.sleep(120)

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
    global flight_num
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
            # logging.info("weather from the log")
            # logging.info(weather)
            final = weather['weather']
            global weather_final
            weather_final = final
            file_exists = os.path.isfile(f'weather.csv')  
            with open(f'weather.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['instance_timestamp','lon', 'lat', 'main', 'description', 'temp', 'feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity', 'speed', 'deg', 'all', 'dt', 'country', 'sunrise', 'sunset', 'timezone', 'id', 'name', 'cod', 'timestamp'])
                
                instance = instance_timestamp
                lon = final['coord']['lon']
                lat = final['coord']['lat']
                weather = final['weather'][0]
                main = final['main']
                speed = final['wind']['speed']
                deg = final['wind']['deg']
                all_clouds = final['clouds']['all']
                dt = final['dt']
                country = final['sys']['country']
                sunrise = final['sys']['sunrise']
                sunset = final['sys']['sunset']
                timezone = final['timezone']
                city_id = final['id']
                city_name = final['name']
                cod = final['cod']
                writer.writerow([instance,lon, lat, weather['main'], weather['description'], main['temp'], main['feels_like'], main['temp_min'], main['temp_max'], main['pressure'], main['humidity'], speed, deg, all_clouds, dt, country, sunrise, sunset, timezone, city_id, city_name, cod])
        if flight:
            # logging.info("flight info from the log")
            # logging.info(flight)
            fflight = flight['flight_data']
            global flight_final
            flight_final = flight
            file_exists = os.path.isfile(f'flight_data.csv') 
            with open(f'flight_data.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['instance_timestamp','iataCode', 'icao24', 'iataNumber', 'altitude', 'direction', 'latitude', 'longitude', 'horizontal_speed', 'vspeed', 'isGround', 'status', 'Last_updated'])
                
                instance = instance_timestamp
                iataCode = fflight['aircraft']['iataCode']
                icao24 = fflight['aircraft']['icao24']
                iataNumber = fflight['flight']['iataNumber']
                altitude = fflight['geography']['altitude']
                direction = fflight['geography']['direction']
                latitude = fflight['geography']['latitude']
                longitude = fflight['geography']['longitude']
                horizontal_speed = fflight['speed']['horizontal']
                vspeed = fflight['speed']['vspeed']
                isGround = fflight['speed']['isGround']
                status = fflight['status']
                Last_updated = datetime.fromtimestamp(fflight['system']['updated']).strftime('%d-%b-%Y %I:%M:%S %p')  
                writer.writerow([instance,iataCode, icao24, iataNumber, altitude, direction, latitude, longitude, horizontal_speed, vspeed, isGround, status, Last_updated])

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


if __name__ == '__main__':
    bottle.run(app, host='::', port=9000, server='gevent')
