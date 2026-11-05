# Accuracy of TFLite models on held-out real images, with firmware-like ROI crops
import sys, json, cv2, numpy as np, tensorflow as tf
sys.path.insert(0, "/wm/tools")
import data

labels = json.load(open("/wm/labels.json"))
test = json.load(open("/wm/holdout.json"))

def rois(scale_w, scale_h, dx=0):
    out = []
    for x, y, w, h in data.CELLS:
        cw, ch = w * scale_w, h * scale_h
        out.append((int(round(x + w / 2 - cw / 2 + dx)), int(round(y + h / 2 - ch / 2)), int(round(cw)), int(round(ch))))
    return out

variants = {"tight (1.0x)": rois(1.0, 1.0), "10% margin": rois(1.2, 1.2), "20% margin": rois(1.4, 1.4),
            "like current ROIs (52x100)": rois(52 / 34, 100 / 60), "tight, shifted +4px": rois(1.0, 1.0, 4),
            "tight, shifted -4px": rois(1.0, 1.0, -4), "10%, rotated -1.5 deg": rois(1.2, 1.2)}
ROT = {"10%, rotated -1.5 deg": -1.5}
for path in sys.argv[1:]:
    it = tf.lite.Interpreter(path); it.allocate_tensors()
    inp, outp = it.get_input_details()[0]["index"], it.get_output_details()[0]["index"]
    print("==", path.split("/")[-1])
    for name, r in variants.items():
        ok = n = 0; errors = []
        for p in test:
            img = cv2.imread(p)
            if name in ROT:  # like the firmware's InitialRotate (rotation around the image center)
                img = cv2.warpAffine(img, cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), ROT[name], 1), (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REPLICATE)
            X = data.eval_crops(img, r)[..., ::-1].astype(np.float32)
            for i in range(10):
                it.set_tensor(inp, X[i:i + 1]); it.invoke()
                pred = int(np.argmax(it.get_tensor(outp)[0])); want = data.label_of(labels[p][i])
                ok += pred == want; n += 1
                if pred != want: errors.append(f"{p.split('/')[-1][9:15]}#{i}:{want}->{pred}")
        print(f"  {name:28s} {ok}/{n} = {100 * ok / n:.1f}%  {' '.join(errors[:12])}")
