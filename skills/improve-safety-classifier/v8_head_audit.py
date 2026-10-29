"""v8 헤드별 재현·오차단 측정과 확신도 높은 오류 추출.

  python <경로>                          # 11 헤드 재현·오차단 표
  python <경로> --axis substance -n 100  # 그 헤드의 오탐·미탐 상위 n장 시트 + 분포 요약

점수: 학습에 쓴 장은 교차 예측(oof), test 장은 헤드 점수. 양성·음성은 학습 때 쓴 라벨(sonnet·사용자 정정 반영)이다.
오탐 = 음성(pos=0) 중 점수 높은 순, 미탐 = 양성 중 점수 낮은 순.
"""
import argparse, collections, datetime, json, pathlib, re
import numpy as np
from PIL import Image, ImageDraw

SD = pathlib.Path("~/lumiteach_wt/exp-safety-classifier-v8/experiments/safety/classifier").expanduser(); RES = SD / "results"
AXES = ["injury", "weapon", "assault", "substance", "hate", "fear", "danger", "exposure", "affection", "sexual", "mind"]
ap = argparse.ArgumentParser()
ap.add_argument("--seed", default="30")
ap.add_argument("--thr", default=str(SD / "models/v8_thresholds_s30.json"))
ap.add_argument("--axis", help="이 헤드의 오탐·미탐 상위 장을 뽑는다")
ap.add_argument("-n", type=int, default=100)
ap.add_argument("--out")
A = ap.parse_args()

THR = json.load(open(A.thr))
S = {}
for a in AXES:
    T = json.load(open(RES / f"v8_{a}_s{A.seed}_test.json"))["1"]; o = T["oof"]
    S[a] = {i: (s, p, sp) for ids, sc, ps, sp in ((o["id"], o["score"], o["pos"], "train"), (T["id"], T["score"], T["pos"], "test")) for i, s, p in zip(ids, sc, ps)}
ROW = {}
for f in RES.glob(f"v8_*_s{A.seed}.jsonl"):
    if re.fullmatch(rf"v8_[a-z0-9]+_s{A.seed}", f.stem):
        ROW.update({r["id"]: r for r in map(json.loads, open(f, encoding="utf-8"))})


def auc(s, p):
    r = np.empty(len(s)); r[np.argsort(s)] = np.arange(1, len(s) + 1)
    n1 = p.sum(); return (r[p].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(s) - n1))


def arr(a):
    ids = list(S[a]); s = np.array([S[a][i][0] for i in ids]); p = np.array([S[a][i][1] for i in ids]); te = np.array([S[a][i][2] == "test" for i in ids])
    return ids, s, p, te


def audit():
    print(f"임계 {A.thr}")
    print("| 헤드 | 임계 | 양성(train/test) | 재현 전체 | 재현 test | 오차단 전체 | 오차단 test | 서빙형 neg/ 오차단 | AUC |\n|---|---|---|---|---|---|---|---|---|")
    for a in AXES:
        ids, s, p, te = arr(a); t = THR[f"{a}≥1"]; f = s > t
        sv = np.array([ROW[i]["group"].startswith("neg/") for i in ids])
        print(f"| {a} | {t:.3f} | {(p & ~te).sum()}/{(p & te).sum()} | {f[p].mean():.1%} | {f[p & te].mean():.1%} | {f[~p].mean():.2%} | {f[~p & te].mean():.2%} | {f[sv & ~p].mean():.2%} | {auc(s, p):.3f} |")


def errors(a):
    ids, s, p, te = arr(a); t = THR[f"{a}≥1"]
    out = pathlib.Path(A.out) if A.out else SD.parent / "reports" / f"head_errors_{a}_{datetime.date.today():%Y%m%d}"
    out.mkdir(parents=True, exist_ok=True)
    others = collections.defaultdict(list)
    for b in AXES:
        for i, (_, pp, _) in S[b].items():
            if pp and b != a: others[i].append(b)
    pools = {"FA": np.where(~p)[0], "FN": np.where(p)[0]}
    picks = {"FA": pools["FA"][np.argsort(-s[pools["FA"]])][:A.n], "FN": pools["FN"][np.argsort(s[pools["FN"]])][:A.n]}
    meta = {}
    for k, ix in picks.items():
        for c in range(0, len(ix), 25):
            m = Image.new("RGB", (1500, 1500), "white")
            for j, q in enumerate(ix[c:c + 25]):
                r = ROW[ids[q]]; im = Image.open(SD / f"images/{r['corpus']}/full/{ids[q]}.jpg").convert("RGB").resize((300, 300))
                d = ImageDraw.Draw(im); d.rectangle((0, 0, 150, 14), fill="black"); d.text((2, 1), f"{c + j + 1} p{s[q]:.2f} {'T' if te[q] else 'tr'}", fill="yellow")
                m.paste(im, ((j % 5) * 300, (j // 5) * 300))
            m.save(out / f"{k}_{c // 25}.jpg", quality=88)
        meta[k] = [{"rank": n + 1, "id": ids[q], "score": round(float(s[q]), 4), "split": "test" if te[q] else "train", "group": ROW[ids[q]]["group"],
                    "style": ROW[ids[q]]["style"], "other_axes": others.get(ids[q], []), "scene": ROW[ids[q]]["scene"]} for n, q in enumerate(ix)]
    json.dump(meta, open(out / "meta.json", "w"), ensure_ascii=False, indent=1)
    print(f"{a}: 임계 {t:.3f} · 시트 {out} (FA_0..·FN_0.. 25장씩, meta.json)")
    stop = set("with that this from their into near beside while onto over under other each than then them they have been being very some what when where which who whom".split())
    for k in ("FA", "FN"):
        pool = [ROW[ids[q]] for q in pools[k]]; top = meta[k]
        print(f"\n## {k} 상위 {len(top)} — 점수 {top[0]['score']}~{top[-1]['score']} · split {dict(collections.Counter(x['split'] for x in top))}")
        gp = collections.Counter(r["group"] for r in pool); gt = collections.Counter(x["group"] for x in top)
        print("그룹(상위 수 / 풀 비중 → 배율):")
        for g, n in gt.most_common(8): print(f"  {g}: {n} / {gp[g] / len(pool):.1%} → ×{n / len(top) / (gp[g] / len(pool)):.1f}")
        if k == "FA": print("다른 축 양성:", dict(collections.Counter(b for x in top for b in x["other_axes"]).most_common(5)), "· 어느 축도 양성 아님", sum(not x["other_axes"] for x in top))
        print("스타일:", dict(collections.Counter(x["style"] for x in top).most_common(4)))
        wp = collections.Counter(w for r in pool for w in set(re.findall(r"[a-z]{4,}", r["scene"].lower())) if w not in stop)
        wt = collections.Counter(w for x in top for w in set(re.findall(r"[a-z]{4,}", x["scene"].lower())) if w not in stop)
        lift = sorted(((n / len(top)) / (wp[w] / len(pool)), w, n) for w, n in wt.items() if n >= 5)[::-1][:10]
        print("장면 단어(상위 수 ≥5, 배율순):", ", ".join(f"{w} {n}(×{x:.1f})" for x, w, n in lift))
    ps = s[pools["FN"]]; pg = collections.Counter(ROW[ids[q]]["group"] for q in pools["FN"])
    print(f"\n## 진단 — 양성 {len(ps)}장(train {(p & ~te).sum()} / test {(p & te).sum()}) · 그룹 {len(pg)}종 · 상위3 그룹 {sum(n for _, n in pg.most_common(3)) / len(ps):.0%}")
    print(f"양성 점수 분위 10/25/50/75%: {np.percentile(ps, [10, 25, 50, 75]).round(2).tolist()} · 임계 미만 {np.mean(ps <= t):.0%} · 점수<0.1 {np.mean(ps < 0.1):.0%} · AUC {auc(s, p):.3f}")


errors(A.axis) if A.axis else audit()
