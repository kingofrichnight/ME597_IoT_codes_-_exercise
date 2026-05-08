# -*- coding: utf-8 -*-
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import requests
import json
import time
import datetime

# -------------------------------
# Power Meter Configuration
# -------------------------------
def registers_to_float(registers):
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers,
        byteorder=Endian.Big,
        wordorder=Endian.Big
    )
    return decoder.decode_32bit_float()

pm_host = "192.168.1.100"  # Power meter IP
pm_port = 502
pm_unit_id = 1

pm_client = ModbusTcpClient(pm_host, port=pm_port)
if not pm_client.connect():
    raise RuntimeError(f"Cannot connect to Power Meter: {pm_host}:{pm_port}")
print("Connected to Power Meter...")

# -------------------------------
# IO-Link Configuration
# -------------------------------
iolink_URL = "http://192.168.1.102/"  # IO-Link Master IP
iolink_BODY = {
    "code": "request",
    "cid": -1,
    "adr": "/iolinkmaster/port[1]/iolinkdevice/iolreadacyclic",
    "data": {"index": 40, "subindex": 0}
}

# -------------------------------
# Infinite Data Collection
# -------------------------------
try:
    print("\nStarting infinite data printing. Press Ctrl+C to stop.\n")
    start_time = time.time()
    while True:
        elapsed_time = int(time.time() - start_time)

        # ----- Power Meter Data -----
        freq_read  = pm_client.read_holding_registers(1536, 2, unit=pm_unit_id)
        volt_read  = pm_client.read_holding_registers(1538, 2, unit=pm_unit_id)
        curr_read  = pm_client.read_holding_registers(1550, 2, unit=pm_unit_id)
        pf_read    = pm_client.read_holding_registers(1564, 2, unit=pm_unit_id)
        power_read = pm_client.read_holding_registers(1582, 2, unit=pm_unit_id)

        if not freq_read.isError():
            F  = registers_to_float(freq_read.registers)
            V  = registers_to_float(volt_read.registers)
            I  = registers_to_float(curr_read.registers)
            PF = registers_to_float(pf_read.registers)
            P  = registers_to_float(power_read.registers)
        else:
            F = V = I = PF = P = float('nan')

        # ----- IO-Link Data -----
        try:
            req = requests.post(url=iolink_URL, json=iolink_BODY, timeout=2)
            data_json = req.json()
            value = data_json['data']['value']

            v_Rms       = round(int(value[0:4], 16) * 0.0001, 4)
            a_Peak      = round(int(value[8:12], 16) * 0.01, 2)
            a_Rms       = round(int(value[16:20], 16) * 0.01, 2)
            Temperature = round(int(value[24:28], 16) * 0.1, 1)
            Crest       = round(int(value[32:36], 16) * 0.01, 2)
        except Exception:
            v_Rms = a_Peak = a_Rms = Temperature = Crest = float('nan')

        # ----- Print All Data -----
        print(f"Time:{elapsed_time}s | "
              f"Power Meter -> F:{F:.2f}Hz V:{V:.2f}V I:{I:.2f}A PF:{PF:.2f} P:{P:.2f}W | "
              f"IO-Link -> v_Rms:{v_Rms} m/s a_Peak:{a_Peak} m/s\u00B2 a_Rms:{a_Rms} m/s\u00B2 Temp:{Temperature} \u00B0C Crest:{Crest} -")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nProgram stopped by user (Ctrl+C).")
finally:
    pm_client.close()
    print("Power Meter connection closed.")
