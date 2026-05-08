import tensorflow as tf

model = tf.keras.models.load_model(
    "20260407_182820_Prelab10_CNN_model1.h5",
    compile=False
)

model.summary()
