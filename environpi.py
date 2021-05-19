# EnvironPi
# Adam Zeloof
# 5/14/2021

import qwiic_bme280
import qwiic_ccs811
from datetime import datetime
import time
import sys
from PiPocketGeiger import RadiationWatch
from sps30 import SPS30
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import secret

def enterData(client, write_api, name, location, measurements):
    data = []
    cTime = datetime.utcnow()
    for point in measurements:
        data.append(
            {
                'measurement': point,
                'tags': {
                    'location': location
                },
                'time': cTime,
                'fields': {'value': measurements[point]}
            }
        )
    write_api.write(secret.bucket, secret.org, data)

def run():
    # Sensor Setup
    bme280 = qwiic_bme280.QwiicBme280() # Temperatire, Pressure, Altidude, Humidity
    ccs811 = qwiic_ccs811.QwiicCcs811() # CO2, tVOC
    rad = RadiationWatch(24, 23).setup()
    sps30 = SPS30(1)

    # Database Initialization
    client = InfluxDBClient(url=secret.url, token=secret.token)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Config
    interval = 10

    # Sensor Initialization
    if bme280.is_connected():
        bme280.begin()

    if ccs811.is_connected():
        ccs811.begin()

    try:
        sps30Serial = sps30.read_device_serial()
        sps30.start_measurement()
        spsConnected = True
    except:
        spsConnected = False
    
    # Main Loop
    while True:
        measurements = {}
        if bme280.is_connected():
            measurements['Temp_F'] = bme280.get_temperature_fahrenheit()
            measurements['Temp_C'] = bme280.get_temperature_celsius()
            measurements['Pressure_Pa'] = bme280.read_pressure()
            measurements['Alt_Feet'] = bme280.get_altitude_feet()
            measurements['Alt_Meters'] = bme280.get_altitude_meters()
            measurements['Relative_Humidity_Percent'] = bme280.read_humidity()
        if ccs811.is_connected():
            ccs811.read_algorithm_results()
            measurements['CO2_PPM'] = ccs811.get_co2()
            measurements['tVOC_PPB'] = ccs811.get_tvoc()
        radStatus = rad.status()
        measurements['Radiation_Duration_Sec'] = radStatus['duration']
        measurements['Radiation_uSvh'] = radStatus['uSvh']
        measurements['Radiation_uSvh_Error'] = radStatus['uSvhError']
        measurements['Radiation_CPM'] = radStatus['cpm']
        #if spsConnected:
            #sps30.read_measured_values()
            #measurements.update(sps30.dict_values)
        print(measurements)
        enterData(client, write_api, "Environpi", "53 Farragut", measurements)
        time.sleep(interval)
            
    
if __name__=="__main__":
    try:
        run()
    except (KeyboardInterrupt, SystemExit):
        print("\nbye")
        sys.exit(0)
