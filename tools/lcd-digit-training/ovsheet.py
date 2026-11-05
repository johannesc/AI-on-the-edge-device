import cv2, sys, json, numpy as np
cells = json.load(open("/wm/cells.json")); tiles = []
for f in sys.argv[2:]:
    im = cv2.imread(f)
    for i, (x, y, w, h) in enumerate(cells):
        cv2.rectangle(im, (x, y), (x + w, y + h), (0, 0, 255), 1)
        cv2.putText(im, str(i), (x + 12, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    tiles.append(cv2.resize(im[165:260, 80:500], None, fx=1.6, fy=1.6))
cv2.imwrite(sys.argv[1], np.vstack(tiles))
