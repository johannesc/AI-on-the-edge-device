# Train the LCD digit model and convert it to an int8 TFLite model with float input/output
import sys, json, glob, cv2, numpy as np, tensorflow as tf
sys.path.insert(0, "/wm/tools")
import data

labels = json.load(open("/wm/labels.json"))           # {image path: 10-char label string}
holdout = set(json.load(open("/wm/holdout.json")))    # images only used for testing
real_train = [(cv2.imread(p), l) for p, l in labels.items() if p not in holdout]
real_test = [(cv2.imread(p), l) for p, l in labels.items() if p in holdout]
def inpaint(img):  # remove the segments of a real image -> display background with its real lighting
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float)
    dark = ((cv2.GaussianBlur(g, (0, 0), 12) - g) > 10).astype(np.uint8) * 255
    return cv2.inpaint(img, cv2.dilate(dark, np.ones((5, 5))), 5, cv2.INPAINT_TELEA)
backgrounds = [cv2.imread(p) for p in sorted(glob.glob("/wm/raw/off/*.jpg"))]
backgrounds += [inpaint(img) for img, _ in real_train[::3]]
print("real train", len(real_train), "test", len(real_test), "backgrounds", len(backgrounds))

Xr, Yr = data.make_dataset(real_train, backgrounds, n_real=30000, n_syn=40000, n_between=4000, seed=1)
Xv, Yv = data.make_dataset(real_test, backgrounds, n_real=4000, n_syn=0, n_between=500, seed=2)
print("train", Xr.shape, np.bincount(Yr, minlength=11), "val", Xv.shape)
# OpenCV is BGR, the firmware feeds RGB
Xr, Xv = Xr[..., ::-1].astype(np.float32), Xv[..., ::-1].astype(np.float32)

def block(x, f):
    x = tf.keras.layers.Conv2D(f, 3, padding="same", use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    return tf.keras.layers.ReLU()(x)

inp = tf.keras.Input((32, 20, 3))
x = tf.keras.layers.Rescaling(1 / 255.0)(inp)
x = block(x, 16); x = block(x, 16); x = tf.keras.layers.MaxPool2D()(x)    # 16x10
x = block(x, 32); x = block(x, 32); x = tf.keras.layers.MaxPool2D()(x)    # 8x5
x = block(x, 64); x = tf.keras.layers.MaxPool2D()(x)                      # 4x2
x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.Dropout(0.3)(x)
x = tf.keras.layers.Dense(96, activation="relu")(x)
x = tf.keras.layers.Dropout(0.3)(x)
out = tf.keras.layers.Dense(11, activation="softmax")(x)
model = tf.keras.Model(inp, out)
model.compile(tf.keras.optimizers.Adam(2e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
model.fit(Xr, Yr, validation_data=(Xv, Yv), epochs=int(sys.argv[1]) if len(sys.argv) > 1 else 25, batch_size=128,
          callbacks=[tf.keras.callbacks.ReduceLROnPlateau(patience=2, factor=0.4, verbose=1),
                     tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=4, restore_best_weights=True, verbose=1)], verbose=2)
model.save("/wm/out/lcd_digits.keras")

# Validation errors: confusion and an image of the wrong crops (label -> prediction)
pred = model.predict(Xv, verbose=0).argmax(1)
conf = np.zeros((11, 11), int)
for t, p_ in zip(Yv, pred): conf[t, p_] += 1
print("confusion (rows = label, 10 = N):\n", conf)
wrong = np.where(pred != Yv)[0][:120]
if len(wrong):
    tiles = [cv2.putText(cv2.resize(Xv[i][..., ::-1].astype(np.uint8), (60, 96), interpolation=cv2.INTER_NEAREST), f"{Yv[i]}>{pred[i]}", (2, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1) for i in wrong]
    while len(tiles) % 15: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite("/wm/out/val_errors.jpg", np.vstack([np.hstack(tiles[i:i + 15]) for i in range(0, len(tiles), 15)]))

def rep():
    for i in np.random.default_rng(0).choice(len(Xr), 400, replace=False):
        yield [Xr[i:i + 1]]
conv = tf.lite.TFLiteConverter.from_keras_model(model)
conv.optimizations = [tf.lite.Optimize.DEFAULT]
conv.representative_dataset = rep
conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
conv.inference_input_type = tf.float32
conv.inference_output_type = tf.float32
open("/wm/out/lcd_digits_q.tflite", "wb").write(conv.convert())
print("saved")
