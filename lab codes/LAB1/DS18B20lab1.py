#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import time
import csv
from datetime import datetime

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c, temp_f

def main():
    # --- Settings you can change ---
    sampling_period_s = 1.0          # must be >= 1.0 for DS18B20
    duration_s = 70                  # > 60 seconds (1 minute)
    csv_filename = "ds18b20_data.csv"
    # -------------------------------

    start_time = time.time()
    end_time = start_time + duration_s

    with open(csv_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Temperature(\u00B0C)", "Temperature(\u00B0F)"])

        print(f"Logging to {csv_filename} for {duration_s} seconds...")

        while time.time() < end_time:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            temp_c, temp_f = read_temp()

            if temp_c is not None:
                writer.writerow([timestamp, f"{temp_c:.2f}", f"{temp_f:.2f}"])
                print(f"{timestamp} | {temp_c:.2f}\u00B0C | {temp_f:.2f} \u00B0F")
            else:
                print(f"{timestamp} | Read failed")

            # Keep period >= 1 second
            time.sleep(sampling_period_s)

    print("\nDone! CSV saved.")

if __name__ == "__main__":
    main()
