"""Bundle viewer.html + recorded runs + ablation results into one self-contained page."""
import json
import sys

RUNS = [
    ("Full mind · harsh world", "runs/harsh_full.json"),
    ("No self/other distinction · harsh world", "runs/harsh_no_self_other.json"),
    ("Full mind · easy world", "runs/latest.json"),
]


def main(out):
    html = open("viewer.html", encoding="utf-8").read()
    for drop in ('<!doctype html>\n', '<meta charset="utf-8">\n',
                 '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'):
        html = html.replace(drop, "", 1)
    runs = [{"label": label, "data": json.load(open(path))} for label, path in RUNS]
    res = json.load(open("results/results.json"))
    res.pop("runs", None)
    payload = ("window.MIND_RUNS=" + json.dumps(runs, separators=(",", ":")) +
               ";window.MIND_RESULTS=" + json.dumps(res, separators=(",", ":")) + ";")
    html = html.replace("<!--EMBED-->", "<script>" + payload.replace("</", "<\\/") + "</script>")
    open(out, "w", encoding="utf-8").write(html)
    print(out, len(html) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "viewer_bundle.html")
