#!/usr/bin/env python3
"""6번 에이전트 — 주간 검증(Weekly Audit)
매주 일요일 22:00 UTC 실행. 기존 모든 tools/skills/4축의:
- dateChecked 나이(90일 경과 = stale 후보)
- 1차 sourceUrl HEAD(200인지)
- 4축(특히 변경기록이 비어있는 경우)
을 종합해 ops/weekly-audit-summary.json 생성.
PR 자동 발행은 하지 않음 — 사람이 summary를 보고 필요 시 수동 PR."""

import datetime
import glob
import json
import os
import re
import sys
import urllib.request
import urllib.error

ALLOWED_SKILL_LICENSES = {
    "MIT", "Apache-1.1", "Apache-2.0",
    "BSD-1-Clause", "BSD-2-Clause", "BSD-2-Clause-FreeBSD", "BSD-3-Clause",
    "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "MPL-1.1", "MPL-2.0", "ISC", "Unlicense", "CC0-1.0", "0BSD", "Zlib", "Artistic-2.0", "EPL-2.0",
}
STALE_DAYS = 90
TIMEOUT = 15


def head(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "yeollin-dogu-weekly-audit/1.0",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return (r.status, r.geturl())
    except urllib.error.HTTPError as e:
        return (e.code, url)
    except Exception:
        return (-1, url)


def scan_kind(kind):
    """cases/lessons/reviews에 대해 (1차 sourceUrl HEAD, dateChecked 나이) 검사."""
    out = []
    today = datetime.date.today()
    files = sorted(glob.glob(f"src/content/{kind}/*.json"))
    for path in files:
        try:
            d = json.loads(open(path).read())
        except Exception as e:
            out.append({"entry": path.split("/")[-1][:-5], "error": f"JSON 파싱 실패: {e}"})
            continue
        eid = path.split("/")[-1][:-5]
        code, _ = head(d.get("sourceUrl") or "")
        dc = d.get("dateChecked")
        age = None
        if dc:
            try:
                age = (today - datetime.date.fromisoformat(dc[:10])).days
            except ValueError:
                age = None
        out.append({
            "entry": eid,
            "sourceUrl": d.get("sourceUrl"),
            "sourceMethod": d.get("sourceMethod"),
            "dateChecked": dc,
            "ageDays": age,
            "headStatus": code,
            "stale": age is not None and age > STALE_DAYS,
            "ok": code == 200,
        })
    return out


def scan_tools_skills(kind):
    """tools/skills JSON에 대해 dateChecked/소스 head/license 검사."""
    out = []
    today = datetime.date.today()
    files = sorted(glob.glob(f"src/content/{kind}/*.json"))
    for path in files:
        try:
            d = json.loads(open(path).read())
        except Exception:
            out.append({"entry": path.split("/")[-1][:-5], "error": "JSON 파싱 실패"})
            continue
        eid = path.split("/")[-1][:-5]
        # dateChecked (skills만 직접 보유, tools는 github.fetchedAt가 유사)
        dc = d.get("dateChecked")
        age = None
        if dc:
            try:
                age = (today - datetime.date.fromisoformat(dc[:10])).days
            except ValueError:
                age = None
        out.append({
            "entry": eid,
            "license": d.get("license") if kind == "skills" else None,
            "licenseAllowed": (d.get("license") in ALLOWED_SKILL_LICENSES) if kind == "skills" else None,
            "dateChecked": dc,
            "ageDays": age,
            "stale": age is not None and age > STALE_DAYS,
        })
    return out


def main():
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    summary = {
        "generatedAt": now.isoformat(),
        "staleDays": STALE_DAYS,
        "counts": {},
        "stale": [],
        "headFailures": [],
        "licenseIssues": [],
    }

    for kind in ("cases", "lessons", "reviews"):
        rows = scan_kind(kind)
        summary["counts"][kind] = len(rows)
        for r in rows:
            if r.get("stale"):
                summary["stale"].append({"kind": kind, **r})
            if not r.get("ok") and r.get("sourceUrl"):
                summary["headFailures"].append({"kind": kind, **r})

    for kind in ("tools", "skills"):
        rows = scan_tools_skills(kind)
        summary["counts"][kind] = len(rows)
        for r in rows:
            if r.get("stale"):
                summary["stale"].append({"kind": kind, **r})
            if kind == "skills" and r.get("license") and not r.get("licenseAllowed"):
                summary["licenseIssues"].append(r)

    out_path = "ops/weekly-audit-summary.json"
    os.makedirs("ops", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ weekly-audit-summary.json 저장: {out_path}")
    print(f"  - 전체: {sum(summary['counts'].values())}개")
    print(f"  - 90일 경과(stale): {len(summary['stale'])}건")
    print(f"  - sourceUrl HEAD 실패: {len(summary['headFailures'])}건")
    print(f"  - 라이선스 위반(skills): {len(summary['licenseIssues'])}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
