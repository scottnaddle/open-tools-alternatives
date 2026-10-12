"""PLAN.md 12장 1차 공개 6개 묶음만 씨앗 데이터에서 변환. 전부 unverified / manual-seed."""
import json, pathlib, shutil
SEED = pathlib.Path(__file__).resolve().parents[2] / "seed"
OUT = pathlib.Path(__file__).resolve().parents[1] / "src/content"
BUNDLES = {1: ["alzip", "alcapture"], 2: ["photoshop", "illustrator"], 3: ["bandicam-ocam"],
           4: ["visio-almind", "file-transfer"], 5: ["capcut"], 6: ["hancom-office"]}
FETCHED = "2026-10-12T00:00:00+09:00"
tools = {t["id"]: t for t in json.load(open(SEED / "tools.json"))["tools"]}
apps = {a["id"]: a for a in json.load(open(SEED / "school-apps.json"))["schoolApps"]}

import datetime
def health(g):
    if g["archived"]: return "archived"
    d = (datetime.date(2026, 10, 12) - datetime.date.fromisoformat(g["lastPush"][:10])).days
    return "stale" if d > 180 else "slowing" if d > 90 else "active"

def fact(value, url, excerpt):
    return {"value": value, "status": "unverified", "lastVerified": None,
            "sources": [{"url": url, "fetchedAt": FETCHED, "excerpt": excerpt, "method": "manual-seed"}]}

for d in ("tools", "school-apps"):
    shutil.rmtree(OUT / d, ignore_errors=True); (OUT / d).mkdir(parents=True)
used, issues = set(), []
for b, ids in BUNDLES.items():
    for aid in ids:
        a = apps[aid]
        alts = []
        for x in a["alternatives"]:
            used.add(x["toolId"])
            alts.append({"tool": x["toolId"], "summary": x["summary"], "installDifficulty": x["installDifficulty"],
                         "level": fact(x["level"], "https://school-edtech.kr", "씨앗 데이터 조사값")})
        out = {"name": a["name"], "category": a["category"], "icon": a["icon"], "source": a["source"], "bundle": b,
               "procurementNote": fact(a["procurementNote"], "https://school-edtech.kr", "2026년 1~10월 조달 기록") if a.get("procurementNote") else None,
               "gap": fact(a["gap"], "https://school-edtech.kr", "씨앗 데이터 조사값") if a.get("gap") else None,
               "alternatives": alts}
        json.dump(out, open(OUT / "school-apps" / f"{aid}.json", "w"), ensure_ascii=False, indent=2)
for tid in sorted(used):
    t = tools[tid]; g = t["github"]; repo = f"https://github.com/{g['repo']}"
    lic = g.get("license")
    if lic in (None, "NOASSERTION"): issues.append(f"{tid}: license={lic}")
    if t.get("installDifficultySource") == "auto": issues.append(f"{tid}: installDifficulty 자동 분류")
    out = {"name": t["name"], "category": t["category"], "notes": t.get("notes", []),
           "schoolUse": fact(t["schoolUse"], repo, "씨앗 데이터 조사값"),
           "usageMode": fact(t["usageMode"], repo, "씨앗 데이터 조사값"),
           "installDifficulty": fact(t["installDifficulty"], repo, f"씨앗 데이터 ({t.get('installDifficultySource')})"),
           "platforms": fact(t["platforms"], repo, "공식 배포 현황 조사값, 검증 필요"),
           "license": fact(lic, repo, "GitHub 검색 API 조회값"),
           "officialSite": fact(None, repo, "씨앗 데이터에 없음"),
           "github": {"repo": g["repo"], "stars": g["stars"], "lastPush": g["lastPush"], "archived": g["archived"],
                      "latestRelease": None, "fetchedAt": g["fetchedAt"]},
           "health": health(g)}
    json.dump(out, open(OUT / "tools" / f"{tid}.json", "w"), ensure_ascii=False, indent=2)
print("apps", sum(len(v) for v in BUNDLES.values()), "tools", len(used))
print("\n".join(issues))
