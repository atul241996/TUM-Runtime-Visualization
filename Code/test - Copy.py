import requests
import json
import threading
import time
from datetime import datetime
import logging
import pandas as pd
import chardet

def stream_old_data():
    latest_instance_timestamp="20240404-144416"
    with open('weather.csv', 'rb') as file:
        raw_data = file.read(10000) 
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    weather_df = pd.read_csv('weather.csv',encoding=encoding)
    flight_data_df = pd.read_csv('flight_data.csv',encoding=encoding)
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
        print(data)
        logging.info("sse -- old data event dumps")
        logging.info(data)
        time.sleep(10) 


if __name__ == '__main__':
    stream_old_data()