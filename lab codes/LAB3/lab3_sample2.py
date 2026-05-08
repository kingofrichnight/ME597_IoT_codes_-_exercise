# -*- coding: utf-8 -*-


import requests
import json
import datetime

# --------------------------------------------------
# IO-Link Master IP
# --------------------------------------------------
URL = "http://192.168.1.102/"   # Change if needed

# --------------------------------------------------
# JSON Body (Port 1)
# --------------------------------------------------
BODY = {
        "code":"request",
        "cid":-1,
        "adr":"/iolinkmaster/port[1]/iolinkdevice/iolreadacyclic",
        "data":{"index":40,"subindex":0}    
}

now = datetime.datetime.now()

# --------------------------------------------------
# Send POST request
# --------------------------------------------------
req = requests.post(url=URL, json=BODY)
data_json = req.json()

# --------------------------------------------------
# Extract Raw Value
# --------------------------------------------------
value = data_json['data']['value']

print("\nRaw measured value:", value)

# --------------------------------------------------
# Convert and Scale Values
# --------------------------------------------------

# v_Rms (m/s)
v_Rms = round(int(value[0:4], 16) * 0.0001, 4)

# a_Peak (m/s^2)
a_Peak = round(int(value[8:12], 16) * 0.01, 2)

# a_Rms (m/s^2)
a_Rms = round(int(value[16:20], 16) * 0.01, 2)

# Temperature (\u00B0C)
Temperature = round(int(value[24:28], 16) * 0.1, 1)

# Crest factor (-)
Crest = round(int(value[32:36], 16) * 0.01, 2)

# --------------------------------------------------
# Print Table 4 Format
# --------------------------------------------------

print("\n-------------------- Table 4 --------------------")
print(f"Time               : {now}")
print(f"v_Rms              : {v_Rms} m/s")
print(f"a_Peak             : {a_Peak} m/s\u00B2")
print(f"a_Rms              : {a_Rms} m/s\u00B2")
print(f"Temperature        : {Temperature} \u00B0 C")
print(f"Crest Factor       : {Crest} -")
print("-------------------------------------------------\n")
