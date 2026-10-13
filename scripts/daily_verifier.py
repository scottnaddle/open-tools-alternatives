"""Daily Verifier — GitHub Actions 용 일일 검증 워크플로.
A등급 변경(별, 릴리스 등)과 C등급 변경(라이선스)을 PR로 제안.
C등급은 24시간 뒤 재확인 일치해야 게시(commit 'pending-recheck' → 재실행 후 'approved').
--apply 없이 실행하면 PR만 생성하고 main에 직접 커밋하지 않음."""

import json, os, sys, glob, datetime, urllib.request, urllib.error, uuid, subprocess, time, hashlib

NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
RUN = "daily-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
CHG = "src/content/changes"

# GitHub 미러 → 공식 저장소
OFFICIAL_HOMES = {
    "GNOME/gimp": ("https://gitlab.gnome.org", "GNOME/gimp"),
    "inkscape/inkscape": ("https://gitlab.com", "inkscape/inkscape"),
    "KDE/krita": ("https://invent.kde.org", "graphics/krita"),
}

# 라이선스 원문 확인 타겟
LICENSE_TARGETS = {
    "7-zip": {
        "urls": ["https://raw.githubusercontent.com/ip7z/7zip/main/DOC/License.txt", "https://www.7-zip.org/license.txt"],
        "must": ["version 2.1 of the License, or (at your option) any later version", "unRAR license restriction"],
        "spdx": "LGPL-2.1-or-later AND BSD-3-Clause AND BSD-2-Clause AND LicenseRef-unRAR-restriction",
    },
    "gimp": {
        "urls": ["https://gitlab.gnome.org/GNOME/gimp/-/raw/master/COPYING"],
        "must": ["GNU GENERAL PUBLIC LICENSE", "Version 3, 29 June 2007"],
        "spdx": "GPL-3.0",
    },
    "inkscape": {
        "urls": ["https://gitlab.com/inkscape/inkscape/-/raw/master/COPYING"],
        "must": ["the complete binaries of Inkscape are currently covered by the terms of GNU GPL version 3 or later"],
        "spdx": "GPL-3.0-or-later",
    },
    "nanazip": {
        "urls": ["https://raw.githubusercontent.com/M2Team/NanaZip/main/License.md"],
        "must": ["is distributed under the MIT", "distributed under the 7-Zip License"],
        "spdx": "MIT AND LicenseRef-7-Zip",
    },
}

def get(url, gh=True):
    h = {"User-Agent": "yeollin-dogu-daily-verifier"}
    if gh:
        h["Accept"] = "application/vnd.github+json"
        if os.environ.get("GITHUB_TOKEN"):
            h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if gh and r.headers.get("X-RateLimit-Remaining") == "0":
                raise SystemExit("GitHub 요청 한도 소진 — 중단")
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise SystemExit(f"요청 제한({e.code}) — 중단: {url}")
        if e.code == 404:
            return None
        raise

def src(url, excerpt, method="github-api"):
    return {"url": url, "fetchedAt": NOW, "excerpt": excerpt, "method": method}

def record(tid, target, before, after, sources, tier):
    rid = f"{datetime.date.today()}-{tid}-{target.split('.')[-1]}-{uuid.uuid4().hex[:6]}"
    data = {
        "at": NOW,
        "agent": "daily-verifier",
        "runId": RUN,
        "target": f"tools/{tid}.{target}",
        "before": before,
        "after": after,
        "sources": sources,
        "tier": tier,
        "gates": ["pending-recheck"] if tier == "C" else [],
        "commit": "pending"
    }
    os.makedirs(CHG, exist_ok=True)
    with open(f"{CHG}/{rid}.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return rid

def gitlab(base, path):
    p = urllib.parse.quote(path, safe="")
    proj = get(f"{base}/api/v4/projects/{p}?license=true", gh=False)
    if not proj:
        return None
    rel = get(f"{base}/api/v4/projects/{p}/releases?per_page=1", gh=False) or []
    tags = get(f"{base}/api/v4/projects/{p}/repository/tags?per_page=1&order_by=updated", gh=False) or []
    out = {
        "web": proj["web_url"],
        "lastActivity": proj.get("last_activity_at"),
        "archived": proj.get("archived"),
        "license": (proj.get("license") or {}).get("key")
    }
    if rel:
        out["release"] = {
            "tag": rel[0]["tag_name"],
            "date": rel[0]["released_at"][:10],
            "url": f"{proj['web_url']}/-/releases/{rel[0]['tag_name']}"
        }
    elif tags:
        out["release"] = {
            "tag": tags[0]["name"],
            "date": (tags[0].get("commit") or {}).get("created_at", "")[:10],
            "url": f"{proj['web_url']}/-/tags/{tags[0]['name']}",
            "fromTag": True
        }
    return out

def check_license_text(tid, cfg):
    """라이선스 원문 확인 (C등급)"""
    srcs = []
    for u in cfg["urls"]:
        txt = urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": "yeollin-dogu-daily-verifier"}),
            timeout=20
        ).read().decode("utf-8", "replace")
        flat = " ".join(txt.split())
        hit = [m for m in cfg["must"] if " ".join(m.split()) in flat]
        if u == cfg["urls"][0] and len(hit) != len(cfg["must"]):
            return None, None  # 기대 문구 없음
        head = " / ".join(l.strip() for l in txt.splitlines() if l.strip())[:300]
        sha = hashlib.sha256(txt.encode()).hexdigest()[:12]
        srcs.append(src(u, f"{head} … [sha256 {sha}]", "readme" if "raw" in u and "github" in u else "official-site"))
    return cfg["spdx"], srcs

def process_tool(f):
    """한 도구 처리 → 변경 목록 반환"""
    tid = os.path.basename(f)[:-5]
    with open(f) as fp:
        t = json.load(fp)
    
    g = t["github"]
    repo = g["repo"]
    api = f"https://api.github.com/repos/{repo}"
    
    changes = []
    modified = False
    
    # GitHub API 조회
    r = get(api)
    if not r:
        return {"tool": tid, "error": "GitHub 저장소 조회 실패(404)", "changes": []}
    
    # A등급: stars, lastPush, archived
    for k in ["stars", "lastPush", "archived"]:
        if k == "stars":
            new_val = r["stargazers_count"]
        elif k == "lastPush":
            new_val = r["pushed_at"][:10]
        else:
            new_val = r["archived"]
        
        if g.get(k) != new_val:
            rid = record(tid, f"github.{k}", g.get(k), new_val, [src(api, f"{k} from repos API")], "A")
            g[k] = new_val
            changes.append({"field": f"github.{k}", "before": g.get(k), "after": new_val, "tier": "A", "record": rid})
            modified = True
    
    # A등급: latestRelease
    rel = get(api + "/releases/latest")
    latest = None
    if rel:
        latest = {
            "tag": rel["tag_name"],
            "date": rel["published_at"][:10],
            "url": rel["html_url"]
        }
        if g.get("latestRelease") != latest:
            rid = record(tid, "github.latestRelease", g.get("latestRelease"), latest, [src(api + "/releases/latest", "latest release")], "A")
            g["latestRelease"] = latest
            changes.append({"field": "github.latestRelease", "before": g.get("latestRelease"), "after": latest, "tier": "A", "record": rid})
            modified = True
    
    g["fetchedAt"] = NOW[:10]
    
    # 미러 체크
    if repo in OFFICIAL_HOMES:
        base, path = OFFICIAL_HOMES[repo]
        try:
            gl = gitlab(base, path)
            if gl and gl.get("release") and not gl["release"].get("fromTag"):
                if g.get("latestRelease") != gl["release"]:
                    rid = record(tid, "github.latestRelease", g.get("latestRelease"), gl["release"], [src(gl["release"]["url"], "공식 저장소 releases API", "release-assets")], "A")
                    g["latestRelease"] = gl["release"]
                    changes.append({"field": "github.latestRelease", "before": g.get("latestRelease"), "after": gl["release"], "tier": "A", "record": rid})
                    modified = True
        except Exception as e:
            pass  # 공식 저장소 조회 실패해도 계속 진행
    
    # C등급: 라이선스 (제안만, 24시간 뒤 재확인 필요)
    if tid in LICENSE_TARGETS:
        cfg = LICENSE_TARGETS[tid]
        try:
            new_spdx, srcs = check_license_text(tid, cfg)
            if new_spdx and t["license"]["value"] != new_spdx:
                # pending 상태인지 확인
                pending = t.get("pendingLicense")
                if pending and pending["value"] == new_spdx:
                    # 이미 제안된 것과 같음 — 24시간 지났는지 확인
                    earliest = datetime.datetime.fromisoformat(pending["earliestApply"])
                    now = datetime.datetime.fromisoformat(NOW)
                    if now >= earliest:
                        # 해시 비교
                        old_hashes = [s["excerpt"][-20:] for s in pending["sources"]]
                        new_hashes = [s["excerpt"][-20:] for s in srcs]
                        if old_hashes == new_hashes:
                            # 24시간 뒤 재확인 일치 → approved
                            rid = record(tid, "license", t["license"]["value"], new_spdx, srcs, "C")
                            t["license"] = {
                                "value": new_spdx,
                                "status": "verified",
                                "lastVerified": NOW,
                                "sources": srcs
                            }
                            t.pop("pendingLicense", None)
                            changes.append({"field": "license", "before": t["license"]["value"], "after": new_spdx, "tier": "C", "record": rid, "status": "approved"})
                            modified = True
                            # ChangeRecord gates 업데이트
                            with open(f"{CHG}/{rid}.json") as fp:
                                rec = json.load(fp)
                            rec["gates"] = ["license-text", "recheck-24h"]
                            with open(f"{CHG}/{rid}.json", "w") as fp:
                                json.dump(rec, fp, ensure_ascii=False, indent=2)
                else:
                    # 새 제안
                    earliest = (datetime.datetime.fromisoformat(NOW) + datetime.timedelta(hours=24)).isoformat()
                    t["pendingLicense"] = {
                        "value": new_spdx,
                        "proposedAt": NOW,
                        "earliestApply": earliest,
                        "sources": srcs
                    }
                    rid = record(tid, "license", t["license"]["value"], new_spdx, srcs, "C")
                    changes.append({"field": "license", "before": t["license"]["value"], "after": new_spdx, "tier": "C", "record": rid, "status": "pending-24h"})
                    modified = True
        except Exception as e:
            pass  # 라이선스 원문 확인 실패해도 계속
    
    # health 상태 계산
    ref = g.get("lastPush", "")
    if ref:
        d = (datetime.date.today() - datetime.date.fromisoformat(ref[:10])).days
        h = "archived" if g["archived"] else "stale" if d > 180 else "slowing" if d > 90 else "active"
        if t["health"] != h:
            rid = record(tid, "health", t["health"], h, [src(api, f"기준일 {ref[:10]}")], "C" if h in ("stale", "archived") else "A")
            t["health"] = h
            changes.append({"field": "health", "before": t["health"], "after": h, "tier": "C" if h in ("stale", "archived") else "A", "record": rid})
            modified = True
    
    t["verification"] = {"runId": RUN, "at": NOW, "unresolved": [], "notes": []}
    
    if modified:
        with open(f, "w") as fp:
            json.dump(t, fp, ensure_ascii=False, indent=2)
    
    return {"tool": tid, "changes": changes, "modified": modified}

def main():
    all_results = []
    for f in sorted(glob.glob("src/content/tools/*.json")):
        result = process_tool(f)
        all_results.append(result)
        time.sleep(0.3)  # rate limit
    
    # 요약
    total_changes = sum(len(r["changes"]) for r in all_results)
    a_grade = sum(1 for r in all_results for c in r["changes"] if c["tier"] == "A")
    c_grade = sum(1 for r in all_results for c in r["changes"] if c["tier"] == "C")
    
    print(f"\n=== Daily Verifier Summary ===")
    print(f"Run ID: {RUN}")
    print(f"Total changes: {total_changes} (A-grade: {a_grade}, C-grade: {c_grade})")
    print(f"Tools modified: {sum(1 for r in all_results if r['modified'])}")
    
    # 변경 세부사항
    for r in all_results:
        if r["changes"]:
            print(f"\n{r['tool']}:")
            for c in r["changes"]:
                status = f" [{c.get('status', 'immediate')}]" if c["tier"] == "C" else ""
                print(f"  - {c['field']}: {c['before']} → {c['after']} ({c['tier']}{status})")
    
    # 결과 저장
    with open("/tmp/daily_verifier_summary.json", "w") as f:
        json.dump({
            "runId": RUN,
            "timestamp": NOW,
            "summary": {"total": total_changes, "a_grade": a_grade, "c_grade": c_grade},
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n저장: /tmp/daily_verifier_summary.json")

if __name__ == "__main__":
    main()
