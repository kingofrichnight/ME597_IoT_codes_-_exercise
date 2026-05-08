from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import time
import csv
import numpy as np
import matplotlib.pyplot as plt

def registers_to_float(registers):
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers,
        byteorder=Endian.Big,
        wordorder=Endian.Big
    )
    return decoder.decode_32bit_float()
    
host = "192.168.1.100"   # Change if needed
port = 502
unit_id = 1

client = ModbusTcpClient(host, port=port)

if not client.connect():
    raise RuntimeError(f"Connection failed: {host}:{port}")

print("Connected to Power Meter...")

# --------------------------------------------------
# Data Storage
# --------------------------------------------------
time_list = []
freq_list = []
volt_list = []
curr_list = []
pf_list = []
power_list = []

duration = 60  # seconds
start_time = time.time()

while (time.time() - start_time) < duration:
    
    elapsed_time = int(time.time() - start_time)

    # Read registers (Modify addresses if different in your meter)
    freq_read  = client.read_holding_registers(1536, 2, unit=unit_id)
    volt_read  = client.read_holding_registers(1538, 2, unit=unit_id)
    curr_read  = client.read_holding_registers(1550, 2, unit=unit_id)
    pf_read    = client.read_holding_registers(1564, 2, unit=unit_id)
    power_read = client.read_holding_registers(1582, 2, unit=unit_id)

    if not freq_read.isError():

        freq_value  = registers_to_float(freq_read.registers)
        volt_value  = registers_to_float(volt_read.registers)
        curr_value  = registers_to_float(curr_read.registers)
        pf_value    = registers_to_float(pf_read.registers)
        power_value = registers_to_float(power_read.registers)

        # Store values
        time_list.append(elapsed_time)     # Time [sec]
        freq_list.append(freq_value)       # Frequency [Hz]
        volt_list.append(volt_value)       # Voltage [V]
        curr_list.append(curr_value)       # Current [A]
        pf_list.append(pf_value)           # Power factor [-]
        power_list.append(power_value)     # True power [W]

        print(f"Time:{elapsed_time}s | "
              f"F:{freq_value:.2f} Hz | "
              f"V:{volt_value:.2f} V | "
              f"I:{curr_value:.2f} A | "
              f"PF:{pf_value:.2f} | "
              f"P:{power_value:.2f} W")

    time.sleep(1)
    
client.close()
print("Data collection completed.")

with open("power_meter_data.csv", mode="w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "Time [sec]",
        "Frequency [Hz]",
        "Voltage 1 [V]",
        "Current 1 [A]",
        "Power factor [-]",
        "True power [W]"
    ])

    for i in range(len(time_list)):
        writer.writerow([
            time_list[i],
            freq_list[i],
            volt_list[i],
            curr_list[i],
            pf_list[i],
            power_list[i]
        ])

print("CSV file saved successfully.")

# --------------------------------------------------
# Convert to NumPy Arrays
# --------------------------------------------------
freq_arr = np.array(freq_list)
volt_arr = np.array(volt_list)
curr_arr = np.array(curr_list)
power_arr = np.array(power_list)

# --------------------------------------------------
# Time-Domain Feature Calculation
# --------------------------------------------------
print("\n----- Time Domain Features -----")

print("Voltage Mean:", np.mean(volt_arr))
print("Voltage RMS:", np.sqrt(np.mean(volt_arr**2)))
print("Voltage Std Dev:", np.std(volt_arr))

print("Current Mean:", np.mean(curr_arr))
print("Current RMS:", np.sqrt(np.mean(curr_arr**2)))
print("Current Std Dev:", np.std(curr_arr))

print("True Power Mean:", np.mean(power_arr))
print("True Power Std Dev:", np.std(power_arr))

# --------------------------------------------------
# Plot Data
# --------------------------------------------------
plt.figure()
plt.plot(time_list, volt_arr)
plt.title("Voltage vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("Voltage 1 [V]")
plt.show()

plt.figure()
plt.plot(time_list, curr_arr)
plt.title("Current vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("Current 1 [A]")
plt.show()

plt.figure()
plt.plot(time_list, power_arr)
plt.title("True Power vs Time")
plt.xlabel("Time [sec]")
plt.ylabel("True power [W]")
plt.show()

