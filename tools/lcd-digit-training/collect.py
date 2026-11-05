# Capture raw images from the meter: collect.py <host> <out folder> <count> <pause s>
# Each capture of /img_tmp/raw.jpg presses the button once (servo mode), so the meter cycles through its screens.
import sys, time, urllib.request, os
host, out, n, gap = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
os.makedirs(out, exist_ok=True)
for i in range(n):
    t = time.strftime("%Y%m%d_%H%M%S")
    try:
        data = urllib.request.urlopen(f"http://{host}/img_tmp/raw.jpg", timeout=40).read()
        open(f"{out}/{t}.jpg", "wb").write(data)
        print(t, len(data), flush=True)
    except Exception as e:
        print(t, "ERR", e, flush=True)
    time.sleep(gap)
