# Training data for an LCD digit classifier (11 classes: 0-9, 10 = N), model input 32x20 RGB (0..255)
import cv2, json, numpy as np, glob, random

W, H = 20, 32
CELLS = json.load(open("/wm/cells.json"))  # tight digit boxes (x, y, w, h) in raw image coords
PITCH = 37.8

# 7-segment patterns: a b c d e f g
SEG = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
DIGIT_SETS = {frozenset(v) for v in SEG.values()}
DIGIT_SETS |= {frozenset("abcdf" + "g"), frozenset("fabc"), frozenset("acdefg"[1:])}  # 9 without d, 7 with f, 6 without a
NONDIGIT = ["adefg", "aefg", "deg", "g", "", "abfg", "adef", "cdeg", "bcdeg", "def", "aef", "cde", "ce", "f", "abef", "abcef", "efg", "ad", "d", "cdefg", "bcefg", "a", "abg"]


def label_of(ch):
    return int(ch) if ch.isdigit() else 10


def crop(img, box, rng, label, between=False):
    """Random crop around a digit box: margin from tight to ~30 %, shift, rotation, aspect jitter"""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    if between:
        cx += PITCH * rng.uniform(0.4, 0.6) * rng.choice([-1, 1])
    else:
        cx += w * rng.uniform(-0.12, 0.12)
        cy += h * rng.uniform(-0.07, 0.07)
    mx, my = rng.uniform(-0.05, 0.32), rng.uniform(-0.04, 0.3)
    cw, ch = w * (1 + 2 * mx), h * (1 + 2 * my)
    ang = rng.uniform(-5, 5)
    # affine: map crop rectangle (rotated around center) to W x H
    M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    src = np.array([[cx - cw / 2, cy - ch / 2], [cx + cw / 2, cy - ch / 2], [cx - cw / 2, cy + ch / 2]], np.float32)
    src = np.hstack([src, np.ones((3, 1), np.float32)]) @ M.T
    dst = np.array([[0, 0], [W, 0], [0, H]], np.float32)
    A = cv2.getAffineTransform(src.astype(np.float32), dst)
    return cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_AREA if rng.random() < 0.5 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def photometric(im, rng):
    im = im.astype(np.float32)
    im = im * rng.uniform(0.6, 1.25) + rng.uniform(-35, 20)                 # brightness / gain
    im = im * rng.uniform(0.88, 1.12, size=3)                               # white balance
    m = im.mean(); im = (im - m) * rng.uniform(0.6, 1.3) + m                # contrast
    if rng.random() < 0.3:                                                  # glare spot
        yy, xx = np.mgrid[0:H, 0:W]
        gx, gy, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(3, 12)
        im += rng.uniform(30, 120) * np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * s * s))[..., None]
    if rng.random() < 0.3:
        im = cv2.GaussianBlur(im, (0, 0), rng.uniform(0.3, 0.9))
    im += rng.normal(0, rng.uniform(0, 7), im.shape)
    im = np.clip(im, 0, 255).astype(np.uint8)
    if rng.random() < 0.5:
        _, enc = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, int(rng.uniform(40, 95))])
        im = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return im


def seg_polys(box, slant, thick):
    """Polygons of the 7 segments of an italic digit in box (x, y, w, h)"""
    x, y, w, h = box
    t, g = thick * w, 0.045 * w         # segment thickness, gap
    hw, hh = w - t, (h - t) / 2         # distance between segment center lines
    def P(px, py):  # local coords (0..w, 0..h, origin top-left of upright digit) -> sheared image coords
        return (x + px + (h - py) * slant - h * slant / 2 + (w * slant * 0), y + py)
    def hbar(cy, x0, x1):
        return [P(x0 + g, cy), P(x0 + g + t / 2, cy - t / 2), P(x1 - g - t / 2, cy - t / 2), P(x1 - g, cy), P(x1 - g - t / 2, cy + t / 2), P(x0 + g + t / 2, cy + t / 2)]
    def vbar(cx, y0, y1):
        return [P(cx, y0 + g), P(cx + t / 2, y0 + g + t / 2), P(cx + t / 2, y1 - g - t / 2), P(cx, y1 - g), P(cx - t / 2, y1 - g - t / 2), P(cx - t / 2, y0 + g + t / 2)]
    l, r, top, mid, bot = t / 2, t / 2 + hw, t / 2, t / 2 + hh, t / 2 + 2 * hh
    return {"a": hbar(top, l, r), "g": hbar(mid, l, r), "d": hbar(bot, l, r),
            "f": vbar(l, top, mid), "b": vbar(r, top, mid), "e": vbar(l, mid, bot), "c": vbar(r, mid, bot)}


def render(bg, cells_content, rng):
    """Draw 7-segment content (list of segment strings per cell) on a display-off background"""
    img = bg.astype(np.float32)
    mask = np.zeros(bg.shape[:2], np.float32)
    slant = rng.uniform(0.12, 0.26)
    thick = rng.uniform(0.26, 0.36)
    S = 4  # supersampling for smooth edges
    big = np.zeros((bg.shape[0] * S, bg.shape[1] * S), np.uint8)
    for (x, y, w, h), segs in zip(CELLS, cells_content):
        ox, oy = rng.uniform(-1, 1), rng.uniform(-1, 1)
        polys = seg_polys((x + ox + 1, y + oy, w - h * slant * 0.6 - 1, h), slant, thick)
        for s in segs:
            cv2.fillPoly(big, [np.round(np.array(polys[s]) * S).astype(np.int32)], 255)
    mask = cv2.resize(big, (bg.shape[1], bg.shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    mask = cv2.GaussianBlur(mask, (0, 0), rng.uniform(0.4, 1.0))
    k = rng.uniform(0.45, 0.66) * np.array([1.2, 1.0, 0.95]) * rng.uniform(0.93, 1.07, size=3)  # segment darkening per channel (BGR), measured on real images
    img = img * (1 - mask[..., None] * (1 - k))
    return np.clip(img, 0, 255).astype(np.uint8)


def random_cells(rng):
    out, labels = [], []
    for i in range(10):
        r = rng.random()
        if r < 0.78:
            d = rng.randrange(10); out.append(SEG[d]); labels.append(d)
        elif r < 0.9:
            out.append(rng.choice(NONDIGIT)); labels.append(10)
        else:
            while True:  # random non-digit segment pattern
                s = "".join(c for c in "abcdefg" if rng.random() < 0.45)
                if frozenset(s) not in DIGIT_SETS:
                    break
            out.append(s); labels.append(10)
    return out, labels


def make_dataset(real, backgrounds, n_real, n_syn, n_between, seed):
    """real: list of (image, label string of 10 cells)"""
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    X, Y = [], []
    class R:  # random source compatible with both APIs
        uniform = staticmethod(rng.uniform); random = staticmethod(rng.random); choice = staticmethod(rng.choice)
        normal = staticmethod(nrng.normal)
    def uni(a, b, size=None):
        return nrng.uniform(a, b, size) if size else rng.uniform(a, b)
    R.uniform = staticmethod(uni)
    for _ in range(n_real):
        img, lab = rng.choice(real); i = rng.randrange(10)
        X.append(photometric(crop(img, CELLS[i], R, None), R)); Y.append(label_of(lab[i]))
    for _ in range(n_between):
        img, lab = rng.choice(real); i = rng.randrange(1, 9)
        X.append(photometric(crop(img, CELLS[i], R, None, between=True), R)); Y.append(10)
    per = 10
    for _ in range(n_syn // per):
        content, labels = random_cells(rng)
        img = render(rng.choice(backgrounds), content, R)
        for i in range(10):
            if rng.random() < 0.08:
                X.append(photometric(crop(img, CELLS[i], R, None, between=True), R)); Y.append(10)
            else:
                X.append(photometric(crop(img, CELLS[i], R, None), R)); Y.append(labels[i])
    return np.array(X), np.array(Y)


def eval_crops(img, rois):
    """Crops like the firmware does: plain resize of the ROI to the model input size"""
    return np.array([cv2.resize(img[y:y + h, x:x + w], (W, H), interpolation=cv2.INTER_LINEAR) for (x, y, w, h) in rois])
