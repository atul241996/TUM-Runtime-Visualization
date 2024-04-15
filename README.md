# Flight and Weather Visualization App

This repository contains a web application that visualizes flight and weather data in real-time. The application displays a map with the current position of a flight, its status, and weather conditions affecting the flight path.

## Features

- Real-time tracking of flight status and location on a map.
- Display of weather conditions including temperature, wind speed, and visibility.
- Weather and flight data are updated dynamically using Server-Sent Events (SSE).
- Detailed annotations on weather changes and flight altitude and flight status variations.

### Prerequisites

Before you start, ensure that you have Python and all the required packages are installed.

## Configuration
1 Obtain ICAO 24-Bit Address - 
Visit FlightRadar24 or a similar website to obtain a flight's ICAO 24-bit address, which is a unique identifier for each aircraft.

2 Update the Server Script - 
aircraft_icao24 = "your_ICAO_24_bit_address_here"
Save the file after making the changes and start the Server

3 Start Process in CPEE - 
Navigate to the CPEE interface and start the process using the provided XML file. This will manage the workflow between collecting flight data and updating the visualization.

4 Open the Web Application
Open index_with_annotations.html in a web browser to view the visualization.

5 Viewing Data
With the web application open, you should see updates reflecting the tracked flight's position and the associated weather conditions in real-time.

## Acknowledgments
Aviation Edge: This project utilizes the Aviation Edge API to gather real-time flight tracking and status information. Their robust data capabilities allow for accurate and timely updates that power the core functionalities of our app. More details about their offerings can be found at Aviation Edge (https://aviation-edge.com).

CPEE: The Cloud Process Execution Engine (CPEE) (https://cpee.org) is used to manage the backend processes that handle data fetching and updates. It provides the necessary scalability and reliability required for real-time data processing. Find out more about CPEE and their services at CPEE.
