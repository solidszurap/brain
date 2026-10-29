"""Append-only prediction ledger.

A prediction is written BEFORE its outcome exists and can never be edited;
resolution is a separate event. Every record carries its data source and a
`synthetic` flag, so results on fake data can never be mistaken for real ones.
"""
import json


class Ledger:
    def __init__(self, path=None):
        self.path = path
        self.records = {}
        self._n = 0
        if path:
            open(path, "a").close()

    def _log(self, ev):
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev) + "\n")

    def predict(self, made_t, target_t, horizon, pred, baselines, source, synthetic,
                expected_abs_err=None, err_baseline=None):
        self._n += 1
        rec = dict(id=self._n, made_t=made_t, target_t=target_t, horizon=horizon,
                   pred=pred, baselines=dict(baselines), source=source,
                   synthetic=synthetic, expected_abs_err=expected_abs_err,
                   err_baseline=err_baseline, actual=None)
        self.records[rec["id"]] = rec
        self._log({"event": "predict", **rec})
        return rec["id"]

    def resolve(self, rid, actual):
        rec = self.records[rid]
        if rec["actual"] is not None:
            raise ValueError("prediction already resolved")
        rec["actual"] = actual
        self._log({"event": "resolve", "id": rid, "actual": actual})

    def resolved(self, horizon=None, warmup=0):
        rs = [r for r in sorted(self.records.values(), key=lambda r: r["id"])
              if r["actual"] is not None and (horizon is None or r["horizon"] == horizon)]
        return rs[warmup:]

    def score(self, horizon, warmup=300):
        """World-prediction skill: 1 - MAE(model) / MAE(best baseline). >0 means an edge."""
        rs = self.resolved(horizon, warmup)
        if not rs:
            return None
        n = len(rs)

        def mae(f):
            return sum(abs(f(r) - r["actual"]) for r in rs) / n

        m = mae(lambda r: r["pred"])
        bases = {k: mae(lambda r, k=k: r["baselines"][k]) for k in rs[0]["baselines"]}
        best = min(bases, key=bases.get)
        skill = 1 - m / bases[best] if bases[best] > 0 else 0.0
        return {"n": n, "mae": m, "baselines": bases, "best_baseline": best,
                "skill": skill, "synthetic": any(r["synthetic"] for r in rs)}

    def score_self_error(self, horizon, warmup=300):
        """Self-knowledge of its own fallibility: does the agent predict its own
        error size better than a running-average baseline?"""
        rs = [r for r in self.resolved(horizon, warmup) if r["expected_abs_err"] is not None]
        if not rs:
            return None
        n = len(rs)
        m = sum(abs(r["expected_abs_err"] - abs(r["pred"] - r["actual"])) for r in rs) / n
        b = sum(abs(r["err_baseline"] - abs(r["pred"] - r["actual"])) for r in rs) / n
        return {"n": n, "mae": m, "baseline_mae": b, "skill": 1 - m / b if b > 0 else 0.0}
