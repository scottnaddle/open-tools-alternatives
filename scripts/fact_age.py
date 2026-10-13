#!/usr/bin/env python3
"""팩트 나이 점검 — verified 팩트 중 lastVerified가 오래된 것을 나열.
빌드를 실패시키지 않는다(정보 제공용). 주간 리서치 때 실행해 재확인 대상을 뽑는다.
사용법: python3 scripts/fact_age.py [경과일 기본 90] [--json 경로]"""

import datetime
import glob
import json
import sys

DEFAULT_AGE = 90


def collect(max_age_days):
    today = datetime.date.today()
    rows = []
    for f in sorted(glob.glob("src/content/tools/*.json")):
        tid = f.rsplit("/", 1)[-1][:-5]
        with open(f) as fp:
            t = json.load(fp)
        for k, v in t.items():
            if not (isinstance(v, dict) and v.get("status") == "verified"):
                continue
            lv = v.get("lastVerified")
            if not isinstance(lv, str):
                continue
            try:
                age = (today - datetime.date.fromisoformat(lv[:10])).days
            except ValueError:
                continue
            if age > max_age_days:
                rows.append({"tool": tid, "field": k, "ageDays": age, "lastVerified": lv[:10]})
    rows.sort(key=lambda r: -r["ageDays"])
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    max_age = int(args[0]) if args else DEFAULT_AGE
    rows = collect(max_age)
    if not rows:
        print(f"✓ {max_age}일 넘게 확인 안 한 verified 팩트가 없습니다.")
        return 0
    print(f"⏰ {max_age}일 넘게 재확인하지 않은 verified 팩트 {len(rows)}건:")
    for r in rows:
        print(f"  - {r['tool']}.{r['field']}: {r['ageDays']}일 경과 (마지막 확인 {r['lastVerified']})")
    print("\n재확인 절차: ops/RESEARCH.md 5절. 출처를 다시 수집해 lastVerified를 갱신하세요.")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        with open(out, "w") as fp:
            json.dump({"generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       "maxAgeDays": max_age, "staleFacts": rows}, fp, ensure_ascii=False, indent=2)
        print(f"저장: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
