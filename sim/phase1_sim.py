"""折り合い フェーズ1（半協力型・3地区）の数値確認用の簡易シミュレーション。
区長の方針をいくつか決め打ちし、4ラウンド後の状態とフェーズ2の初期住民を集計する。"""
import random, itertools, statistics as st, sys

SOIL = {"家": 1, "森": 1, "学校": 2, "公園": 2, "畑": 2, "田んぼ": 3}
SITES = {
    "A": ["家"] * 3 + ["学校"] + ["田んぼ"] * 2 + ["森"],
    "B": ["家"] * 2 + ["学校"] + ["田んぼ"] * 3 + ["畑"],
    "C": ["家"] * 4 + ["学校"] * 2 + ["公園"],
}
# 仮置場の候補地：(名前, 容量, 私有地か)
LANDS = {
    "A": [("公有地", 5, False), ("公有地", 5, False), ("田んぼ", 5, True)],
    "B": [("田んぼ", 4, True), ("田んぼ", 4, True), ("田んぼ", 4, True)],
    "C": [("公園", 3, True)],
}
PRIORITY = {"学校": 0, "家": 1, "公園": 2, "畑": 3, "田んぼ": 3, "森": 4}


def run(seed, actions_per_round, start_hands, policy):
    rnd = random.Random(seed)
    st_ = {}
    for d in "ABC":
        st_[d] = dict(todo=sorted(SITES[d], key=lambda s: (PRIORITY[s], rnd.random())), done=[],
                      onsite=[],  # 現場保管：各箇所の土量
                      lands=[dict(name=n, cap=c, private=p, used=0, open=False) for n, c, p in LANDS[d]],
                      hands=start_hands, received=0, sent=0, flipped_private=0)
    school_late = False
    for r in range(1, 5):
        for d in "ABC":
            s = st_[d]
            acts = actions_per_round
            # 人手を使うか（仕事が残っていれば使う）
            while acts > 0 or (s["hands"] > 0 and (s["todo"] or s["onsite"])):
                if acts == 0:
                    s["hands"] -= 1
                acts = max(acts - 1, 0) if acts > 0 else 0
                free = sum(l["cap"] - l["used"] for l in s["lands"] if l["open"])
                need_place = s["todo"][0] if s["todo"] else None
                # 1) 置き場が足りず、方針として作るなら仮置場をつくる
                closed = [l for l in s["lands"] if not l["open"]]
                want_flip = closed and need_place and free < SOIL[need_place] and (
                    policy[d] != "land_averse" or not closed[0]["private"])
                if want_flip:
                    closed.sort(key=lambda l: l["private"])  # 公有地から
                    closed[0]["open"] = True
                    if closed[0]["private"]:
                        s["flipped_private"] += 1
                    continue
                # 2) 除染する
                if need_place:
                    site = s["todo"].pop(0)
                    amt = SOIL[site]
                    s["done"].append(site)
                    for l in s["lands"]:
                        if l["open"] and l["cap"] - l["used"] >= amt:
                            l["used"] += amt
                            break
                    else:
                        s["onsite"].append(amt)
                    continue
                # 3) 現場保管を運ぶ（自分の仮置場、なければ他地区に頼む）
                if s["onsite"]:
                    amt = s["onsite"][0]
                    placed = False
                    for l in s["lands"]:
                        if l["open"] and l["cap"] - l["used"] >= amt:
                            l["used"] += amt; placed = True; break
                    if not placed and policy[d] != "no_ask":
                        for o in "ABC":
                            if o == d or policy[o] == "refuse":
                                continue
                            for l in st_[o]["lands"]:
                                if l["open"] and l["cap"] - l["used"] >= amt:
                                    l["used"] += amt; placed = True
                                    st_[o]["received"] += amt; s["sent"] += amt
                                    st_[o]["hands"] += 1
                                    break
                            if placed:
                                break
                    if placed:
                        s["onsite"].pop(0)
                        continue
                break
        if r == 2 and any("学校" in st_[d]["todo"] for d in "ABC"):
            school_late = True
    out = {}
    for d in "ABC":
        s = st_[d]
        res = [-1, -1, 0, 0, 1, 1]  # 反対2・条件次第2・賛成2

        def move(n):
            for _ in range(abs(n)):
                if n < 0:
                    i = res.index(0) if 0 in res else (res.index(1) if 1 in res else None)
                    if i is not None: res[i] -= 1
                else:
                    i = res.index(0) if 0 in res else (res.index(-1) if -1 in res else None)
                    if i is not None: res[i] += 1
        move(-s["flipped_private"])
        if s["received"] >= 3: move(-1)
        move(len(s["onsite"]) // 2)
        if school_late: move(-1)
        out[d] = dict(done=len(s["done"]), onsite=len(s["onsite"]), onsite_soil=sum(s["onsite"]),
                      flipped=s["flipped_private"], recv=s["received"], sent=s["sent"],
                      res=(res.count(-1), res.count(0), res.count(1)))
    return out, school_late


POLICIES = {
    "全員ふつう": dict(A="normal", B="normal", C="normal"),
    "全員土地を出し渋る": dict(A="land_averse", B="land_averse", C="land_averse"),
    "Aが受け入れを断る": dict(A="refuse", B="normal", C="normal"),
}
for apr in (2, 3):
    for hands in (1, 2):
        print(f"\n=== 1ラウンドの行動 {apr}、はじめの人手 {hands} ===")
        for name, pol in POLICIES.items():
            outs = [run(seed, apr, hands, pol) for seed in range(200)]
            late = sum(o[1] for o in outs) / len(outs)
            line = [f"{name:12s} 学校遅れ{late:.0%}"]
            for d in "ABC":
                v = [o[0][d] for o in outs]
                f = lambda k: st.mean(x[k] for x in v)
                res = st.mean(x["res"][0] for x in v), st.mean(x["res"][2] for x in v)
                line.append(f"{d}: 除染{f('done'):.1f}/7 現場{f('onsite'):.1f}箇所 私有地{f('flipped'):.1f} 受入{f('recv'):.1f} 反対{res[0]:.1f}賛成{res[1]:.1f}")
            print("  " + " | ".join(line))
