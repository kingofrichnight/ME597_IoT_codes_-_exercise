import datetime
import time
import random
import pymysql.cursors
import board
import busio
import adafruit_adxl34x
import os
import glob

# ---------------- MySQL Credentials ----------------
HOST = 'mepotrb16.ecn.purdue.edu'
PORT = 3306
USER = 'aaryafarheen'
PASSWORD = 'Abcd1234!'
DB = 'ME597Spring26'
TABLE = 'aaryafarheen_lab6'

# ---------------- Sensor Names ----------------
sensor_ADXL = "ADXL345"
sensor_DS = "DS18B20"
sensor_virtual = "Virtual"

# ---------------- Measurements ----------------
m_x = "Xacc"
m_y = "Yacc"
m_z = "Zacc"
m_temp = "Temp"
m_humd = "Humd"

# ---------------- MySQL Connection ----------------
connection = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, port=PORT)
cursor = connection.cursor()

# ---------------- ADXL345 Setup ----------------
i2c = busio.I2C(board.SCL, board.SDA)
acc = adafruit_adxl34x.ADXL345(i2c)

# ---------------- DS18B20 Setup ----------------
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
        return temp_c

# ---------------- Data Collection Settings ----------------
duration = 120
Ts = 3
start_time = time.time()

while time.time() - start_time < duration:

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # -------- ADXL345 --------
    x_acc, y_acc, z_acc = acc.acceleration

    # -------- DS18B20 --------
    temperature = read_temp()

    # -------- Virtual Humidity --------
    humidity = random.uniform(30, 80)

    print(timestamp)
    print(f"Xacc={x_acc:.4f}")
    print(f"Yacc={y_acc:.4f}")
    print(f"Zacc={z_acc:.4f}")
    print(f"Temp={temperature:.2f}")
    print(f"Humd={humidity:.2f}")

    # -------- SQL Queries --------
    query1 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor_ADXL+"','"+m_x+"','"+str(x_acc)+"');"
    query2 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor_ADXL+"','"+m_y+"','"+str(y_acc)+"');"
    query3 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor_ADXL+"','"+m_z+"','"+str(z_acc)+"');"

    query4 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor_DS+"','"+m_temp+"','"+str(temperature)+"');"

    query5 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor_virtual+"','"+m_humd+"','"+str(humidity)+"');"

    cursor.execute(query1)
    cursor.execute(query2)
    cursor.execute(query3)
    cursor.execute(query4)
    cursor.execute(query5)

    connection.commit()

    print("==INSERT QUERIES DONE==\n")

    time.sleep(Ts)

connection.close()

print("==Program DONE==")
