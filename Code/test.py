import pandas as pd
import logging
import json
import chardet
import time
import requests
import random

def get_random_aircraft_icao24(flights):
    selected_flight = random.choice(flights)
    return selected_flight["aircraft"]["icao24"]

if __name__ == '__main__':
    api_key = ''
    url = f"https://aviation-edge.com/v2/public/flights?key={api_key}"


    aircraft_icao24 = '4080C2'
    # params = {'aircraftIcao24': aircraft_icao24}
    params = {'status': 'en-route'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        flights = response.json()
        

    # Use the function to get a random aircraft's icao24
    random_aircraft_icao24 = get_random_aircraft_icao24(flights)
                         
    with open('weather.csv', 'rb') as file:
        raw_data = file.read(50000)
        result = chardet.detect(raw_data)
        print(f"Detected encoding: {result['encoding']} with confidence {result['confidence']}")
    with open('flight_data.csv', 'rb') as file:
        raw_data = file.read(50000)
        result = chardet.detect(raw_data)
        print(f"Detected encoding: {result['encoding']} with confidence {result['confidence']}")

    latest_instance_timestamp="20240404-144416"
    weather_df = pd.read_csv('weather.csv')
    flight_data_df = pd.read_csv('flight_data.csv')
    weather_filtered = weather_df[weather_df['instance_timestamp'] == latest_instance_timestamp]
    flight_data_filtered = flight_data_df[flight_data_df['instance_timestamp'] == latest_instance_timestamp]
    weather_old = weather_filtered.iloc[0].to_dict()
    flight_old = flight_data_filtered.iloc[0].to_dict()
    while True:
        data = json.dumps({
            "flight_data": flight_old,
            "weather_data": weather_old,
            "instance_timestamp":latest_instance_timestamp
        })
        # yield f"data: {data}\n\n"
        logging.info("sse -- old data event dumps")
        logging.info(data)
        time.sleep(10)
