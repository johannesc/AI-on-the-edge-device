# Contact sheet of the LCD area of all images in a folder
import cv2, glob, sys, numpy as np
files = sorted(glob.glob(sys.argv[1] + "/*.jpg"))
tiles = []
for f in files:
    im = cv2.imread(f)[165:335, 80:495]
    cv2.putText(im, f.split("/")[-1][9:15], (5, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    tiles.append(im)
while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i+2]) for i in range(0, len(tiles), 2)]
cv2.imwrite(sys.argv[2], np.vstack(rows))
