"""Verifier (LLM 없음). 공개 GitHub/GitLab API로 도구 사실을 재확인하고 ChangeRecord를 남긴다.
- 값은 API 응답에서만 가져온다. 못 얻으면 바꾸지 않고 verification.unresolved 에 기록.
- github.* 변경 = A등급, license 변경 = C등급(POLICY 1장: 24시간 대기 후 재검증 필요).
- GITHUB_TOKEN 환경 변수가 있으면 사용."""
import json, os, glob, re, time, datetime, urllib.request, urllib.parse, urllib.error, uuid, subprocess
from license_keep import LICENSE_KEEP, should_apply_github_spdx

NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
RUN = "verify-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
CHG = "src/content/changes"
# GitHub 저장소가 미러일 때 확인할 공식 저장소 후보(값이 아니라 조회 위치만 지정)
OFFICIAL_HOMES = {
    "GNOME/gimp": ("https://gitlab.gnome.org", "GNOME/gimp"),
    "inkscape/inkscape": ("https://gitlab.com", "inkscape/inkscape"),
    "KDE/krita": ("https://invent.kde.org", "graphics/krita"),
}

def get(url, gh=True):
    h = {"User-Agent": "yeollin-dogu-verifier"}
    if gh:
        h["Accept"] = "application/vnd.github+json"
        if os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if gh and r.headers.get("X-RateLimit-Remaining") == "0":
                raise SystemExit("GitHub 요청 한도 소진 — 중단(값 변경 없이 종료)")
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429): raise SystemExit(f"요청 제한({e.code}) — 중단: {url}")
        if e.code == 404: return None
        raise

def src(url, excerpt, method="github-api"):
    return {"url": url, "fetchedAt": NOW, "excerpt": excerpt, "method": method}

def record(tid, target, before, after, sources, tier):
    rid = f"{datetime.date.today()}-{tid}-{target.split('.')[-1]}-{uuid.uuid4().hex[:6]}"
    json.dump({"at": NOW, "agent": "verifier", "runId": RUN, "target": f"tools/{tid}.{target}",
               "before": before, "after": after, "sources": sources, "tier": tier,
               "gates": [], "commit": "pending"}, open(f"{CHG}/{rid}.json", "w"), ensure_ascii=False, indent=2)

def gitlab(base, path):
    p = urllib.parse.quote(path, safe="")
    proj = get(f"{base}/api/v4/projects/{p}?license=true", gh=False)
    if not proj: return None
    rel = get(f"{base}/api/v4/projects/{p}/releases?per_page=1", gh=False) or []
    tags = get(f"{base}/api/v4/projects/{p}/repository/tags?per_page=1&order_by=updated", gh=False) or []
    out = {"web": proj["web_url"], "lastActivity": proj.get("last_activity_at"),
           "archived": proj.get("archived"), "license": (proj.get("license") or {}).get("key")}
    if rel: out["release"] = {"tag": rel[0]["tag_name"], "date": rel[0]["released_at"][:10], "url": f"{proj['web_url']}/-/releases/{rel[0]['tag_name']}"}
    elif tags: out["release"] = {"tag": tags[0]["name"], "date": (tags[0].get("commit") or {}).get("created_at", "")[:10], "url": f"{proj['web_url']}/-/tags/{tags[0]['name']}", "fromTag": True}
    return out

summary = []
for f in sorted(glob.glob("src/content/tools/*.json")):
    tid = os.path.basename(f)[:-5]; t = json.load(open(f)); g = t["github"]; repo = g["repo"]
    api = f"https://api.github.com/repos/{repo}"
    unresolved, notes = [], []
    r = get(api)
    if not r:
        unresolved.append("GitHub 저장소 조회 실패(404)")
    else:
        # 기본 github.* (A등급)
        new = {"stars": r["stargazers_count"], "lastPush": r["pushed_at"][:10], "archived": r["archived"]}
        for k, v in new.items():
            if g.get(k) != v:
                record(tid, f"github.{k}", g.get(k), v, [src(api, f"{k} from repos API")], "A"); g[k] = v
        # 최신 릴리스 → 없으면 최신 태그
        rel = get(api + "/releases/latest"); latest = None
        if rel: latest = {"tag": rel["tag_name"], "date": rel["published_at"][:10], "url": rel["html_url"]}; lsrc = api + "/releases/latest"
        else:
            unresolved.append("GitHub 릴리스 없음 — 태그 목록은 날짜순이 아니라 최신 버전으로 쓰지 않음")
        if latest and g.get("latestRelease") != latest:
            record(tid, "github.latestRelease", g.get("latestRelease"), latest, [src(lsrc, "latest release/tag")], "A"); g["latestRelease"] = latest
        g["fetchedAt"] = NOW[:10]
        # 미러 판정
        desc = (r.get("description") or "").lower()
        mirror = bool(r.get("mirror_url")) or "mirror" in desc
        home = r.get("homepage") or None
        if mirror or repo in OFFICIAL_HOMES:
            notes.append(f"GitHub 저장소는 미러로 보임(설명: {r.get('description')!r})")
            if repo in OFFICIAL_HOMES:
                base, path = OFFICIAL_HOMES[repo]
                try: gl = gitlab(base, path)
                except Exception as e: gl = None; unresolved.append(f"공식 GitLab 조회 실패: {e}")
                if gl:
                    notes.append(f"공식 저장소 {gl['web']} 활동 {str(gl['lastActivity'])[:10]}, 최신 {gl.get('release')}")
                    g["official"] = {"host": gl["web"], "lastActivity": str(gl["lastActivity"])[:10],
                                     "latestRelease": gl.get("release"), "license": gl.get("license"), "fetchedAt": NOW[:10]}
                    if gl.get("release") and not gl["release"].get("fromTag"):
                        if g.get("latestRelease") != gl["release"]:
                            record(tid, "github.latestRelease", g.get("latestRelease"), gl["release"], [src(gl["release"]["url"], "공식 저장소 releases API", "release-assets")], "A")
                            g["latestRelease"] = gl["release"]
                        unresolved[:] = [u for u in unresolved if not u.startswith("GitHub 릴리스 없음")]
                    if gl.get("license"):
                        notes.append(f"공식 저장소 라이선스 키: {gl['license']} (SPDX 표기 확인 후 반영 — C등급)")
            else: unresolved.append("미러인데 공식 저장소 위치 미등록")
        # 라이선스 (C등급). 고정 목록은 GitHub SPDX로 덮지 않는다.
        spdx = (r.get("license") or {}).get("spdx_id")
        lic = t["license"]
        if tid in LICENSE_KEEP:
            pinned = LICENSE_KEEP[tid]
            if lic["value"] != pinned:
                notes.append(f"라이선스 고정값 {pinned} 과 카탈로그 값 {lic['value']} 이 다름 — 자동으로 바꾸지 않음")
            elif spdx and spdx not in (pinned, "NOASSERTION"):
                notes.append(f"GitHub API spdx={spdx} 는 고정값 {pinned} 과 다름 — 공식·원문 값을 유지")
        elif should_apply_github_spdx(tid, lic["value"], spdx):
            record(tid, "license", lic["value"], spdx, [src(api + "/license", "license.spdx_id")], "C")
            notes.append("라이선스 변경은 C등급: 24시간 뒤 재검증 일치해야 게시")
            t["license"] = {"value": spdx, "status": "verified", "lastVerified": NOW,
                            "sources": [src(api + "/license", f"spdx_id={spdx}")]}
        elif spdx and spdx != "NOASSERTION" and lic["value"] == spdx:
            t["license"] = {"value": spdx, "status": "verified", "lastVerified": NOW,
                            "sources": [src(api + "/license", f"spdx_id={spdx}")]}
        else:
            unresolved.append(f"라이선스 자동 판별 불가(spdx={spdx}) — 라이선스 파일 원문 확인 필요")
            if tid not in LICENSE_KEEP:
                t["license"]["sources"] = [src(api + "/license", f"spdx_id={spdx}")] + [s for s in lic["sources"] if s["method"] == "manual-seed"]
        # 활동 상태 (POLICY 4장 규칙).
        # 알려진 GitHub 미러는 공식 저장소 활동일만 쓴다. 미러 lastPush가 얼어 있으면
        # 그 날짜로 stale을 만들지 않는다.
        if repo in OFFICIAL_HOMES:
            ref = str((g.get("official") or {}).get("lastActivity") or "")[:10]
            if not ref:
                notes.append("공식 저장소 활동일을 못 얻어 GitHub 미러 lastPush로 건강도를 바꾸지 않음")
        else:
            ref = str(g.get("lastPush") or "")[:10]
        if ref:
            d = (datetime.date.today() - datetime.date.fromisoformat(ref[:10])).days
            h = "archived" if g["archived"] else "stale" if d > 180 else "slowing" if d > 90 else "active"
            if t["health"] != h:
                record(tid, "health", t["health"], h, [src(api, f"기준일 {ref[:10]}")], "C" if h in ("stale", "archived") else "A"); t["health"] = h
        if home and not t["officialSite"]["value"]:
            notes.append(f"GitHub homepage 필드: {home} (공식 사이트 후보, 미반영 — B등급·공식 사이트 확인 필요)")
    t["verification"] = {"runId": RUN, "at": NOW, "unresolved": unresolved, "notes": notes}
    json.dump(t, open(f, "w"), ensure_ascii=False, indent=2)
    summary.append((tid, t["license"]["value"], t["license"]["status"], g.get("latestRelease"), g.get("official"), unresolved, notes))
    time.sleep(0.3)
json.dump(summary, open("/tmp/verify_summary.json", "w"), ensure_ascii=False, indent=1)
print("done", RUN)
