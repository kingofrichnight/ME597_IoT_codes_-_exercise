# -*- coding: utf-8 -*-
import requests
import json
import datetime
import time
import csv
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------
# IO-Link Master Configuration
# -------------------------------
URL = "http://192.168.1.102/"  # Change if needed
BODY = {
    "code": "request",
    "cid": -1,
    "adr": "/iolinkmaster/port[1]/iolinkdevice/iolreadacyclic",
    "data": {"index": 40, "subindex": 0}
}

# -------------------------------
# Data Storage
# -------------------------------
time_list = []
vRms_list = []
aPeak_list = []
aRms_list = []
Temp_list = []
Crest_list = []

# -------------------------------
# Data Collection Parameters
# -------------------------------
duration = 60  # seconds
sampling_period = 1  # second

start_time = time.time()
print("Starting 1-minute IO-Link data collection...")

while (time.time() - start_time) < duration:
    elapsed_time = int(time.time() - start_time)
    
    try:
        # Send POST request
        req = requests.post(url=URL, json=BODY, timeout=2)
        data_json = req.json()
        
        # Extract raw value
        value = data_json['data']['value']

        # -------------------------------
        # Convert raw values
        # -------------------------------
        v_Rms      = round(int(value[0:4], 16) * 0.0001, 4)
        a_Peak     = round(int(value[8:12], 16) * 0.01, 2)
        a_Rms      = round(int(value[16:20], 16) * 0.01, 2)
        Temperature= round(int(value[24:28], 16) * 0.1, 1)
        Crest      = round(int(value[32:36], 16) * 0.01, 2)

        # -------------------------------
                # Store values
        # -------------------------------
        time_list.append(elapsed_time)
        vRms_list.append(v_Rms)
        aPeak_list.append(a_Peak)
        aRms_list.append(a_Rms)
        Temp_list.append(Temperature)
        Crest_list.append(Crest)

        # Print Table 5 format (Unicode-safe)
        print(f"Time:{elapsed_time}s | v_Rms:{v_Rms} m/s | a_Peak:{a_Peak} m/s\u00B2 | a_Rms:{a_Rms} m/s\u00B2 | Temp:{Temperature} \u00B0C | Crest:{Crest} -")
    
    except Exception as e:
        print(f"Error at t={elapsed_time}s: {e}")
    
    time.sleep(sampling_period)

print("Data collection completed.")

# -------------------------------
# Save to CSV (Table 5 format)
# -------------------------------
csv_file = "iolink_data_table5.csv"
with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    # Table 5 header
    writer.writerow(["Time [sec]", "v_Rms [m/s]", "a_Peak [m/s\u00B2]", "a_Rms [m/s\u00B2]", "Temperature [\u00B0C]", "Crest [-]"])
    for i in range(len(time_list)):
        writer.writerow([
            time_list[i],
            vRms_list[i],
            aPeak_list[i],
            aRms_list[i],
            Temp_list[i],
            Crest_list[i]
        ])
print(f"CSV file saved as '{csv_file}'")

# -------------------------------
# Convert lists to NumPy arrays for analysis
# -------------------------------
vRms_arr  = np.array(vRms_list)
aPeak_arr = np.array(aPeak_list)
aRms_arr  = np.array(aRms_list)
Temp_arr  = np.array(Temp_list)
Crest_arr = np.array(Crest_list)

# -------------------------------
# Time-Domain Features
# -------------------------------
print("\n----- Time-Domain Features -----")
def calc_features(arr, name, unit=""):
    print(f"{name} Mean: {np.mean(arr):.3f} {unit}")
    print(f"{name} RMS : {np.sqrt(np.mean(arr**2)):.3f} {unit}")
    print(f"{name} Std : {np.std(arr):.3f} {unit}")
    print("-"*40)

calc_features(vRms_arr, "v_Rms", "m/s")
calc_features(aPeak_arr, "a_Peak", "m/s\u00B2")
calc_features(aRms_arr, "a_Rms", "m/s\u00B2")
calc_features(Temp_arr, "Temperature", "\u00B0C")
calc_features(Crest_arr, "Crest Factor", "-")

# -------------------------------
# Plot Data
# -------------------------------
plt.figure()
plt.plot(time_list, vRms_arr, marker='o')
plt.title("v_Rms vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("v_Rms [m/s]")
plt.grid(True)
plt.show()

plt.figure()
plt.plot(time_list, aPeak_arr, marker='o', label='a_Peak')
plt.plot(time_list, aRms_arr, marker='x', label='a_Rms')
plt.title("Acceleration vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("Acceleration [m/s\u00B2]")
plt.legend()
plt.grid(True)
plt.show()

plt.figure()
plt.plot(time_list, Temp_arr, marker='o', color='red')
plt.title("Temperature vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("Temperature [\u00B0C]")
plt.grid(True)
plt.show()

plt.figure()
plt.plot(time_list, Crest_arr, marker='o', color='purple')
plt.title("Crest Factor vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("Crest [-]")
plt.grid(True)
plt.show()
