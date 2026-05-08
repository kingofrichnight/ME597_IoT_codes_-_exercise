import tensorflow as tf

MODEL_DIR = "/home/pi/prelab9/content/models/20260330_174619_lab8_anomaly_x-axis_raw"

loaded = tf.saved_model.load(MODEL_DIR)
infer = loaded.signatures["serving_default"]

_ = infer(tf.zeros((1, 1000), dtype=tf.float32))

print("Model load success.")
