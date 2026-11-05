import json, glob
S = {"vol1": "0000079025", "vol2": "0000079102", "rev": "N000000003", "ver": "0133NNN071", "E": "NN00000000", "F": "NN00000000", "flow": "NNNNNN000N"}
def temp(v): return "NNN" + v + "NNN"
c1 = {"184539": S["E"], "184547": S["F"], "184553": S["flow"], "184601": temp("1628"), "184608": S["vol1"], "184615": S["rev"], "184622": S["ver"],
      "184629": S["E"], "184636": S["F"], "184643": S["flow"], "184650": temp("1648"), "184657": S["vol1"], "184705": S["rev"], "184711": S["ver"],
      "184718": S["E"], "184725": S["F"]}
order = ["vol2", "rev", "ver", "E", "F", "flow"]
c2files = sorted(glob.glob("/wm/raw/cycle2/*.jpg")); temps = iter(["1216", "1241", "1260"])
labels = {f"/wm/raw/cycle1/20261105_{k}.jpg": v for k, v in c1.items()}
labels["/wm/raw/r_000.jpg"] = S["ver"]
for i, f in enumerate(c2files):
    labels[f] = temp(next(temps)) if i % 7 == 6 else S[order[i % 7]]
for f in sorted(glob.glob("/wm/raw/off/*.jpg")):
    labels[f] = "N" * 10
json.dump(labels, open("/wm/labels.json", "w"), indent=0)
json.dump(c2files[14:], open("/wm/holdout.json", "w"), indent=0)
print(len(labels), "labelled,", len(c2files[14:]), "held out:", [labels[f] for f in c2files[14:]])
