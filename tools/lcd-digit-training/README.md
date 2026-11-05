# LCD digit model training

Trains a digit model (`class11`: 0-9 and N) for a 7-segment LCD meter, e.g. a Sagemcom Siconia water meter.
Compared to the standard models it:

- accepts ROIs from tight around the digit up to ~30 % free space, so ROIs of closely spaced digits do not need to overlap,
- handles italic (slanted) digits and rotations up to about ±5°,
- reads blank cells, letters (`E`, `F`, `c`, `-`, `°C`) and a switched off display as `N`.

The model has the same format as `dig-class11_*.tflite` (input 32x20 RGB, 11 outputs, int8 with float in/output) and only uses
operators the firmware supports, so it can be selected as `Model` in the `[Digits]` section.

## How it works
Training data is a mix of

- **real cells** cut from raw images of the meter with random margins, shifts, rotations and lighting, and
- **synthetic cells**: 7-segment digits rendered onto real display-off backgrounds (`raw/off`) and inpainted real images.

## Steps
All scripts expect the working folder to be mounted as `/wm` and the scripts in `/wm/tools`.

```bash
WM=~/lcd-train; mkdir -p $WM/tools $WM/out; cp *.py $WM/tools/
docker build -t wm-train .

# 1. Images: each capture presses the button (meter cycles through its screens)
python3 collect.py watermeter.lan $WM/raw/cycle1 16 2
#    Display off images (no button press), wait until the display switched off first
curl -o $WM/raw/off/1.jpg http://watermeter.lan/capture_with_flashlight

# 2. Digit cells: tight boxes (x, y, w, h) of all digit positions in raw image coordinates -> $WM/cells.json
#    Check them with: docker run --rm -v $WM:/wm wm-train python /wm/tools/ovsheet.py /wm/check.jpg <images>
# 3. Labels: one 10 character string per image (digit or N per cell) -> $WM/labels.json, test images -> $WM/holdout.json
#    (see mklabels.example.py, contact sheets of the display: sheet.py)

# 4. Train and test (old model for comparison)
docker run --rm -u $(id -u) -e HOME=/tmp -v $WM:/wm wm-train python /wm/tools/train.py 25
docker run --rm -u $(id -u) -v $WM:/wm wm-train python /wm/tools/evaluate.py /wm/out/lcd_digits_q.tflite
```

`cells.example.json` contains the cells of the Siconia display (10 digits, the last three smaller) with camera zoom 29.

`models/dig-class11-lcd-siconia_0100_s2_q.tflite` is the model trained this way for a Siconia water meter
(camera zoom 29, about 8 cm distance). Copy it to `/config` on the SD card to use it.
