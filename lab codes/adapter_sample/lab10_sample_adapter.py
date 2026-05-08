from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import math
import tensorflow as tf
import time
from data_item import Event, Sample
from mtconnect_adapter import Adapter
import sys

# ==========================
# GLOBAL CONSTANTS
# ==========================
SAMPLE = "sample"
CURRENT = "current"

SAMP_RATE = int(48000)
CHUNK = int(2048)

# MTConnect sound stream agent
AGENT = "http://127.0.0.1:5000/"

N = int(23)
N_FFT = int(2048)
N_MELS = int(128)

# Your trained ML model
model_file = "here.h5"
model_keras = tf.keras.models.load_model(model_file, compile=False)

# Model class order
# Change only this if your training label order is different
CLASS_NAMES = ["OFF", "RUNNING", "REST"]


# ==========================
# SOUND FUNCTIONS
# ==========================
def get_sound_signal(response):
    root = ET.fromstring(response.content)
    MTCONNECT_STR = root.tag.split("}")[0] + "}"

    array = []

    for sample in root.iter(MTCONNECT_STR + "DisplacementTimeSeries"):
        chunk = np.fromstring(sample.text, dtype=np.int16, sep=' ') / (2 ** 15)
        array = np.append(array, chunk)

    return np.array(array, dtype=np.float32)


def get_sound_level(signal):
    signal_rms = np.sqrt(np.mean(signal ** 2))

    if signal_rms <= 0:
        return 0

    sound_level = 20 * math.log10(signal_rms / 9.9963e-7) - 28.87
    return sound_level


def get_rms(signal):
    return float(np.sqrt(np.mean(signal ** 2)))


def get_rms_state(rms):
    if rms > 0.25:
        return "RUNNING"
    elif rms > 0.05:
        return "REST"
    else:
        return "OFF"


def feature_extraction(x):
    M = librosa.feature.melspectrogram(
        y=x,
        sr=SAMP_RATE,
        n_fft=N_FFT,
        hop_length=int(N_FFT / 4),
        win_length=N_FFT,
        window='hann',
        n_mels=N_MELS
    )

    X = 2 * abs(M) / N_FFT

    # Expected shape: (1, 128, 93)
    S = np.reshape(X, (1, -1, X.shape[1]))

    return S


# ==========================
# CURRENT PARSING
# ==========================
class CurrentParsing(object):
    def __init__(self, response):
        root = ET.fromstring(response.content)
        MTCONNECT_STR = root.tag.split("}")[0] + "}"

        header = root.find("./" + MTCONNECT_STR + "Header")

        if header is None:
            print("ERROR: Header not found in MTConnect response")
            print(response.text[:1000])
            raise Exception("MTConnect Header not found")

        header_attribs = header.attrib

        self.nextSeq = int(header_attribs["nextSequence"])
        self.firstSeq = int(header_attribs["firstSequence"])
        self.lastSeq = int(header_attribs["lastSequence"])

        self.timestamp = "N/A"

        for sample in root.iter(MTCONNECT_STR + "DisplacementTimeSeries"):
            self.timestamp = sample.get('timestamp')


# ==========================
# MTCONNECT ADAPTER
# ==========================
class MTConnectAdapter(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.adapter = Adapter((host, port))

        # ==========================
        # Samples
        # ==========================
        self.sound_level = Sample('spl')
        self.adapter.add_data_item(self.sound_level)

        # ==========================
        # Events
        # ==========================
        self.execution = Event('e1')
        self.adapter.add_data_item(self.execution)

        self.compressor_state = Event('vs1')
        self.adapter.add_data_item(self.compressor_state)

        self.avail = Event('avail')
        self.adapter.add_data_item(self.avail)

        # ==========================
        # Start Adapter
        # ==========================
        self.adapter.start()
        self.adapter.begin_gather()
        self.avail.set_value("AVAILABLE")
        self.adapter.complete_gather()

        self.adapter_stream()

    def adapter_stream(self):
        while True:
            try:
                # Read latest current sequence from sound sensor
                Current = CurrentParsing(
                    requests.get(
                        AGENT + CURRENT + "?path=//DataItem[@id=%27sensor1%27]"
                    )
                )

                lastSeq = Current.lastSeq

                # Collect 23 sound chunks
                x = get_sound_signal(
                    requests.get(
                        AGENT + SAMPLE +
                        "?from=" + str(int(lastSeq - N)) +
                        "&count=" + str(N) +
                        "&path=//DataItem[@id=%27sensor1%27]"
                    )
                )

                if len(x) == 0:
                    print("No sound data received.")
                    time.sleep(2)
                    continue

                # Feature extraction
                X = feature_extraction(x)

                # ML Prediction
                yhat = model_keras.predict(X, verbose=0)
                Y = int(np.argmax(yhat))
                confidence = float(np.max(yhat))

                model_state = CLASS_NAMES[Y]

                # RMS backup state
                rms = get_rms(x)
                rms_state = get_rms_state(rms)

                # ==========================
                # Air compressor logic
                # ==========================
                if model_state == "OFF":
                    exe = "OFF"
                    comp_state = "OFF"
                elif model_state == "RUNNING":
                    exe = "ON"
                    comp_state = "RUNNING"
                elif model_state == "REST":
                    exe = "ON"
                    comp_state = "REST"
                else:
                    exe = "UNKNOWN"
                    comp_state = "UNKNOWN"

                sound_pressure = round(get_sound_level(x), 2)

                # Send data to MTConnect adapter
                self.adapter.begin_gather()
                self.execution.set_value(exe)
                self.compressor_state.set_value(comp_state)
                self.sound_level.set_value(sound_pressure)
                self.adapter.complete_gather()

                print("------------------------------------------------")
                print(f"Timestamp        : {Current.timestamp}")
                print(f"Execution        : {exe}")
                print(f"Compressor State : {comp_state}")
                print(f"Sound Level      : {sound_pressure} dB SPL")
                print(f"RMS              : {rms:.6f}")
                print(f"RMS State        : {rms_state}")
                print(f"Model Output     : {yhat}")
                print(f"Confidence       : {confidence:.4f}")
                print("------------------------------------------------")

                time.sleep(2)

            except KeyboardInterrupt:
                print("Stopping MTConnect...")
                self.adapter.stop()
                sys.exit()

            except Exception as e:
                print("Error:")
                print(e)
                time.sleep(2)


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print("Starting Air Compressor MTConnect Adapter...")
    MTConnectAdapter('127.0.0.1', 7878)