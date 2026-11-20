"""折り合い フェーズ1（半協力型・3地区）簡略版ルールの数値確認。
docs/phase1-rules-draft.md の「行動は2種類」「人手は引き受けた印だけ」に合わせた版。
区長の方針を決め打ちし、4ラウンド後の状態とフェーズ2の初期住民を集計する。"""
import random
import statistics as st

SOIL = {"家": 1, "森": 1, "学校": 2, "公園": 2, "畑": 2, "田んぼ": 3}
SITES = {
    "A": ["家"] * 3 + ["学校"] + ["田んぼ"] * 2 + ["森"],
    "B": ["家"] * 2 + ["学校"] + ["田んぼ"] * 3 + ["畑"],
    "C": ["家"] * 4 + ["学校"] * 2 + ["公園"],
}
LANDS = {  # (名前, 容量, 住民の負担あり)
    "A": [("公有地", 5, False), ("公有地", 5, False), ("田んぼ", 5, True)],
    "B": [("田んぼ", 4, True), ("田んぼ", 4, True), ("田んぼ", 4, True)],
    "C": [("公園", 3, True)],
}
PRIORITY = {"学校": 0, "家": 1, "公園": 2, "畑": 3, "田んぼ": 3, "森": 4}
ACTIONS = 2
ROUNDS = 4


def free(s):
    return sum(l["cap"] - l["used"] for l in s["lands"] if l["open"])


def put(s, amt):
    """自分の地区の仮置場に、1か所分の土をまとめて入れる"""
    for l in s["lands"]:
        if l["open"] and l["cap"] - l["used"] >= amt:
            l["used"] += amt
            return True
    return False


def run(seed, policy):
    rnd = random.Random(seed)
    S = {d: dict(todo=sorted(SITES[d], key=lambda x: (PRIORITY[x], rnd.random())), done=0, onsite=[],
                 lands=[dict(cap=c, private=p, used=0, open=False) for _, c, p in LANDS[d]],
                 hands=0, flipped=0) for d in "ABC"}
    for r in range(1, ROUNDS + 1):
        for d in "ABC":
            s = S[d]
            for _ in range(ACTIONS):
                nxt = s["todo"][0] if s["todo"] else None
                closed = sorted([l for l in s["lands"] if not l["open"]], key=lambda l: l["private"])
                need = (SOIL[nxt] if nxt else 0) > free(s) or s["onsite"]
                ok_flip = closed and need and (policy[d] != "land_averse" or not closed[0]["private"])
                if ok_flip:
                    l = closed[0]
                    l["open"] = True
                    s["flipped"] += l["private"]
                    for amt in sorted(s["onsite"], reverse=True):  # つくったとき現場保管を移せる
                        if put(s, amt):
                            s["onsite"].remove(amt)
                    continue
                if not nxt:
                    break
                s["todo"].pop(0)
                s["done"] += 1
                amt = SOIL[nxt]
                if put(s, amt):
                    continue
                placed = False
                if policy[d] != "no_ask":
                    for o in "ABC":
                        if o != d and policy[o] != "refuse" and put(S[o], amt):
                            S[o]["hands"] += 1
                            placed = True
                            break
                if not placed:
                    s["onsite"].append(amt)
    out = {}
    for d in "ABC":
        s = S[d]
        oppose = s["flipped"] + (1 if s["hands"] >= 2 else 0)
        n = len(s["onsite"])
        support = 0 if n <= 1 else (1 if n <= 3 else 2)
        out[d] = dict(done=s["done"], onsite=n, flipped=s["flipped"], hands=s["hands"],
                      oppose=min(2 + oppose, 6), support=min(2 + support, 6))
    return out


POLICIES = {
    "ふつう": dict(A="normal", B="normal", C="normal"),
    "全員が土地を出し渋る": dict(A="land_averse", B="land_averse", C="land_averse"),
    "Aが引き受けを断る": dict(A="refuse", B="normal", C="normal"),
    "Bだけ出し渋る": dict(A="normal", B="land_averse", C="normal"),
}
if __name__ == "__main__":
    for name, pol in POLICIES.items():
        outs = [run(seed, pol) for seed in range(200)]
        town = st.mean(sum(o[d]["onsite"] for d in "ABC") for o in outs)
        goal = sum(sum(o[d]["onsite"] for d in "ABC") <= 6 for o in outs) / len(outs)
        cells = []
        for d in "ABC":
            v = [o[d] for o in outs]
            m = lambda k: st.mean(x[k] for x in v)
            cells.append(f"{d} 除染{m('done'):.1f}/7 現場{m('onsite'):.1f} 負担地{m('flipped'):.1f} 人手{m('hands'):.1f} 反対{m('oppose'):.1f} 賛成{m('support'):.1f}")
        print(f"{name:12s} 町の現場保管{town:.1f}（6以下{goal:.0%}） | " + " | ".join(cells))
