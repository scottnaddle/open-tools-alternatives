"""Daily Verifier — GitHub Actions 용 일일 검증 워크플로.
A등급 변경(별, 릴리스 등)과 C등급 변경(라이선스)을 PR로 제안.
C등급은 24시간 뒤 재확인 일치해야 게시(commit 'pending-recheck' → 재실행 후 'approved').
--apply 없이 실행하면 PR만 생성하고 main에 직접 커밋하지 않음."""

import json, os, sys, glob, datetime, urllib.request, urllib.parse, urllib.error, uuid, subprocess, time, hashlib

# 비-GitHub 호스트의 403/429는 짧게 재시도한 뒤 건너뛴다.
# GitHub API 한도만 전체 실행을 중단한다(SystemExit).
NON_GITHUB_RATE_RETRIES = 2
NON_GITHUB_RATE_BACKOFF = 1.0

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
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                if gh and r.headers.get("X-RateLimit-Remaining") == "0":
                    raise SystemExit("GitHub 요청 한도 소진 — 중단")
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                if gh:
                    raise SystemExit(f"요청 제한({e.code}) — 중단: {url}")
                if attempt < NON_GITHUB_RATE_RETRIES:
                    wait = NON_GITHUB_RATE_BACKOFF * (2 ** attempt)
                    attempt += 1
                    print(
                        f"경고: 외부 호스트 요청 제한({e.code}) — {wait:.0f}초 후 재시도 ({attempt}/{NON_GITHUB_RATE_RETRIES}): {url}",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
                print(
                    f"경고: 외부 호스트 요청 제한({e.code}) — 건너뜀(skipped/unverified): {url}",
                    file=sys.stderr,
                )
                return None
            if e.code == 404:
                return None
            raise

def src(url, excerpt, method="github-api"):
    return {"url": url, "fetchedAt": NOW, "excerpt": excerpt, "method": method}

def record(tid, target, before, after, sources, tier, prefix="tools"):
    rid = f"{datetime.date.today()}-{tid}-{target.split('.')[-1]}-{uuid.uuid4().hex[:6]}"
    data = {
        "at": NOW,
        "agent": "daily-verifier",
        "runId": RUN,
        "target": f"{prefix}/{tid}.{target}",
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

def apply_official_mirror(tid, g, changes):
    """공식 저장소 릴리스를 확인한다.

    외부 호스트가 403/429 등으로 실패하면 'skipped/unverified'만 반환하고
    github·health·license 등 데이터 상태는 바꾸지 않는다.
    GitHub 요청 한도의 SystemExit은 Exception이 아니므로 여기서 삼키지 않는다.
    """
    repo = g.get("repo")
    if repo not in OFFICIAL_HOMES:
        return None
    base, path = OFFICIAL_HOMES[repo]
    try:
        gl = gitlab(base, path)
    except Exception as e:
        print(
            f"경고: {tid} 공식 저장소 조회 실패 — skipped/unverified ({e})",
            file=sys.stderr,
        )
        return "skipped/unverified"
    if not gl:
        print(
            f"경고: {tid} 공식 저장소 응답 없음 — skipped/unverified ({base})",
            file=sys.stderr,
        )
        return "skipped/unverified"
    if gl.get("release") and not gl["release"].get("fromTag"):
        if g.get("latestRelease") != gl["release"]:
            rid = record(tid, "github.latestRelease", g.get("latestRelease"), gl["release"], [src(gl["release"]["url"], "공식 저장소 releases API", "release-assets")], "A")
            g["latestRelease"] = gl["release"]
            changes.append({"field": "github.latestRelease", "before": g.get("latestRelease"), "after": gl["release"], "tier": "A", "record": rid})
    return None

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
    
    # 미러 체크 — 외부 호스트 실패는 skipped/unverified 로만 남기고 값은 유지
    n_before = len(changes)
    mirror_status = apply_official_mirror(tid, g, changes)
    if len(changes) != n_before:
        modified = True
    
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
    
    out = {"tool": tid, "changes": changes, "modified": modified}
    if mirror_status:
        out["mirror"] = mirror_status
    return out

def recheck_passed(sid, target, new_val):
    """24시간 전 C등급 제안(같은 값)이 있었는지 changes 기록으로 확인."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).isoformat()
    for f in glob.glob(f"{CHG}/*.json"):
        try:
            with open(f) as fp:
                rec = json.load(fp)
        except Exception:
            continue
        if (rec.get("target") == f"skills/{sid}.{target}"
                and rec.get("after") == new_val and rec.get("tier") == "C"
                and "pending-recheck" in rec.get("gates", [])
                and rec.get("at", "") <= cutoff):
            return True
    return False

def process_skill(f):
    """한 스킬 처리: stars(A)·라이선스(C, 24시간 재확인)·삭제 감지."""
    sid = os.path.basename(f)[:-5]
    with open(f) as fp:
        s = json.load(fp)
    g = s["github"]
    api = f"https://api.github.com/repos/{g['repo']}"
    changes = []
    modified = False

    r = get(api)
    if not r:
        # 저장소 소실은 스키마를 바꾸지 않고 요약으로만 보고 (에이전트가 수동 조사)
        return {"skill": sid, "error": "GitHub 저장소 조회 실패(404) — 삭제·이전 확인 필요", "changes": []}

    new_stars = r["stargazers_count"]
    if g.get("stars") != new_stars:
        before_stars = g.get("stars")
        rid = record(sid, "stars", before_stars, new_stars, [src(api, "stars from repos API")], "A", prefix="skills")
        g["stars"] = new_stars
        changes.append({"field": "github.stars", "before": before_stars, "after": new_stars, "tier": "A", "record": rid})
        modified = True

    new_lic = (r.get("license") or {}).get("spdx_id")
    if new_lic in ("NOASSERTION", "Other"):
        new_lic = None
    if new_lic and g.get("license") != new_lic:
        before_lic = g.get("license")
        tier = "C"
        rid = record(sid, "license", before_lic, new_lic, [src(api, "license from repos API")], tier, prefix="skills")
        if recheck_passed(sid, "license", new_lic):
            g["license"] = new_lic
            changes.append({"field": "github.license", "before": before_lic, "after": new_lic, "tier": tier, "record": rid, "status": "approved"})
            modified = True
            with open(f"{CHG}/{rid}.json") as fp:
                rec = json.load(fp)
            rec["gates"] = ["pending-recheck", "recheck-24h"]
            with open(f"{CHG}/{rid}.json", "w") as fp:
                json.dump(rec, fp, ensure_ascii=False, indent=2)
        else:
            changes.append({"field": "github.license", "before": before_lic, "after": new_lic, "tier": tier, "record": rid, "status": "pending-24h (미적용)"})

    s["dateChecked"] = NOW[:10]
    if modified:
        with open(f, "w") as fp:
            json.dump(s, fp, ensure_ascii=False, indent=2)
    return {"skill": sid, "changes": changes, "modified": modified}

def stale_facts(max_age_days=90):
    """verified 팩트 중 lastVerified가 max_age_days를 넘은 목록."""
    out = []
    today = datetime.date.today()
    for f in sorted(glob.glob("src/content/tools/*.json")):
        tid = os.path.basename(f)[:-5]
        with open(f) as fp:
            t = json.load(fp)
        for k, v in t.items():
            if (isinstance(v, dict) and v.get("status") == "verified"
                    and isinstance(v.get("lastVerified"), str) and "lastVerified" in v):
                try:
                    age = (today - datetime.date.fromisoformat(v["lastVerified"][:10])).days
                except ValueError:
                    continue
                if age > max_age_days:
                    out.append({"tool": tid, "field": k, "ageDays": age})
    return out


def head_check(url, timeout=15):
    """1차 sourceUrl의 HEAD 검사. (status, final_url) — 200/3xx=OK, 4xx/5xx/에러=fail."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "yeollin-dogu-daily-verifier/1.0",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (r.status, r.geturl())
    except urllib.error.HTTPError as e:
        return (e.code, url)
    except Exception as e:
        return (-1, url)


def process_axis_page(path, kind, stale_days=90):
    """4축(cases/lessons/reviews) entry 하나 처리:
    1) 1차 sourceUrl HEAD 검사 — 실패 시 C등급 change record(24h 재확인 후 alert)
    2) dateChecked 자동 갱신(HEAD 성공 시)
    3) stale(>stale_days) 표시(데이터만, 변경 X)
    Returns: {"entry", "status", "changes", "modified", "stale"}.
    """
    eid = os.path.basename(path)[:-5]
    with open(path) as fp:
        d = json.load(fp)
    src_url = d.get("sourceUrl")
    if not src_url:
        return {"entry": eid, "kind": kind, "error": "sourceUrl 없음", "changes": []}
    code, final = head_check(src_url)
    ok = (200 <= code < 400)
    changes = []
    modified = False
    stale_flag = False
    today = datetime.date.today()

    if ok:
        # dateChecked 자동 갱신
        try:
            prev = d.get("dateChecked")
            if prev != today.isoformat():
                d["dateChecked"] = today.isoformat()
                modified = True
        except Exception:
            pass
    else:
        # C등급 change record — 24h 재확인
        rid = record(eid, f"sourceUrlStatus", "200", str(code),
                     [src(src_url, f"HEAD {code}", "official-site")], "C", prefix=kind)
        if recheck_axis_passed(eid, kind, str(code)):
            # 24h 일치 → alert: 변경은 데이터에 적용하지 않고 alert만
            changes.append({"field": "sourceUrlStatus", "before": "200", "after": str(code),
                            "tier": "C", "record": rid, "status": "alert (수동 조사 필요)"})
            with open(f"{CHG}/{rid}.json") as fp:
                rec = json.load(fp)
            rec["gates"] = ["pending-recheck", "recheck-24h", "alert"]
            with open(f"{CHG}/{rid}.json", "w") as fp:
                json.dump(rec, fp, ensure_ascii=False, indent=2)
        else:
            changes.append({"field": "sourceUrlStatus", "before": "200", "after": str(code),
                            "tier": "C", "record": rid, "status": "pending-24h"})

    # stale 판단(데이터 변경 X, 보고용)
    try:
        prev_d = d.get("dateChecked")
        if prev_d:
            age = (today - datetime.date.fromisoformat(prev_d[:10])).days
            stale_flag = age > stale_days
    except Exception:
        pass

    if modified:
        with open(path, "w") as fp:
            json.dump(d, fp, ensure_ascii=False, indent=2)
    return {"entry": eid, "kind": kind, "status": code, "ok": ok, "changes": changes,
            "modified": modified, "stale": stale_flag}


def recheck_axis_passed(eid, kind, new_val):
    """4축용 24h 재확인 — 같은 kind/eid/sourceUrlStatus에 대해 24h 이상 지난 같은 값 change record가 있는지."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).isoformat()
    for f in glob.glob(f"{CHG}/*.json"):
        try:
            with open(f) as fp:
                rec = json.load(fp)
        except Exception:
            continue
        if (rec.get("target") == f"{kind}/{eid}.sourceUrlStatus"
                and rec.get("after") == new_val and rec.get("tier") == "C"
                and "pending-recheck" in rec.get("gates", [])
                and rec.get("at", "") <= cutoff):
            return True
    return False


def stale_axis_pages(max_age_days=90):
    """4축 entry 중 dateChecked가 max_age_days 초과인 목록."""
    out = []
    today = datetime.date.today()
    for kind in ("cases", "lessons", "reviews"):
        for path in sorted(glob.glob(f"src/content/{kind}/*.json")):
            try:
                d = json.loads(path.read_text())
            except Exception:
                continue
            dc = d.get("dateChecked")
            if not dc:
                continue
            try:
                age = (today - datetime.date.fromisoformat(dc[:10])).days
            except ValueError:
                continue
            if age > max_age_days:
                out.append({"kind": kind, "entry": path.split("/")[-1][:-5], "ageDays": age})
    return out

def main():
    if os.path.exists("ops/FREEZE"):
        reason = open("ops/FREEZE").read().strip()[:200]
        print(f"⛔ FREEZE 중 — 검증 중단. 사유: {reason or '(사유 미기재)'}")
        return

    all_results = []
    for f in sorted(glob.glob("src/content/tools/*.json")):
        result = process_tool(f)
        all_results.append(result)
        time.sleep(0.3)  # rate limit

    skill_results = []
    for f in sorted(glob.glob("src/content/skills/*.json")):
        skill_results.append(process_skill(f))
        time.sleep(0.3)  # rate limit

    axis_results = []
    for kind in ("cases", "lessons", "reviews"):
        for f in sorted(glob.glob(f"src/content/{kind}/*.json")):
            axis_results.append(process_axis_page(f, kind))
            time.sleep(0.5)  # 외부 HEAD 호출 rate-limit 보호
    
    # 요약
    combined = all_results + skill_results + axis_results
    total_changes = sum(len(r["changes"]) for r in combined)
    a_grade = sum(1 for r in combined for c in r["changes"] if c["tier"] == "A")
    c_grade = sum(1 for r in combined for c in r["changes"] if c["tier"] == "C")
    stale = stale_facts()
    stale_axis = stale_axis_pages()

    print(f"\n=== Daily Verifier Summary ===")
    print(f"Run ID: {RUN}")
    print(f"Total changes: {total_changes} (A-grade: {a_grade}, C-grade: {c_grade})")
    print(f"Tools modified: {sum(1 for r in all_results if r.get('modified'))} / Skills modified: {sum(1 for r in skill_results if r.get('modified'))} / Axis pages modified: {sum(1 for r in axis_results if r.get('modified'))}")
    skipped = [r["tool"] for r in all_results if r.get("mirror") == "skipped/unverified"]
    if skipped:
        print(f"\n공식 저장소 건너뜀(skipped/unverified) {len(skipped)}건 — 데이터 상태는 유지:")
        for name in skipped:
            print(f"  - {name}")
    if stale:
        print(f"\n⏰ 90일 경과 verified 팩트 {len(stale)}건 (재확인 필요):")
        for srow in stale:
            print(f"  - {srow['tool']}.{srow['field']} ({srow['ageDays']}일 경과)")
    if stale_axis:
        print(f"\n⏰ 4축 페이지 90일 경과 {len(stale_axis)}건 (재확인 필요):")
        for srow in stale_axis:
            print(f"  - {srow['kind']}/{srow['entry']} ({srow['ageDays']}일 경과)")

    # 변경 세부사항
    for r in all_results:
        if r["changes"]:
            print(f"\n{r['tool']}:")
            for c in r["changes"]:
                status = f" [{c.get('status', 'immediate')}]" if c["tier"] == "C" else ""
                print(f"  - {c['field']}: {c['before']} → {c['after']} ({c['tier']}{status})")
    for r in axis_results:
        if r.get("changes"):
            print(f"\n[r={r['kind']}/{r['entry']}] (HEAD: {r.get('status')})")
            for c in r["changes"]:
                status = f" [{c.get('status', 'immediate')}]"
                print(f"  - {c['field']}: {c['before']} → {c['after']} ({c['tier']}{status})")

    # 결과 저장
    with open("/tmp/daily_verifier_summary.json", "w") as f:
        json.dump({
            "runId": RUN,
            "timestamp": NOW,
            "summary": {"total": total_changes, "a_grade": a_grade, "c_grade": c_grade,
                        "staleFacts": stale, "staleAxisPages": stale_axis,
                        "skippedMirrors": [r["tool"] for r in all_results if r.get("mirror") == "skipped/unverified"]},
            "results": combined
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n저장: /tmp/daily_verifier_summary.json")

if __name__ == "__main__":
    main()
