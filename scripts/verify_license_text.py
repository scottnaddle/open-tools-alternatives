"""라이선스 원문 근거 확인 (POLICY 4장: NOASSERTION·미판별이면 원문 첫 부분을 근거로 첨부).
라이선스 값 변경은 C등급(POLICY 1장) → 바로 반영하지 않고 제안(pendingLicense)과 C등급 ChangeRecord(gates: pending)만 남긴다.
24시간 뒤 다시 실행해 원문 해시가 같으면 --apply 로 반영. 판정 문구는 아래 TARGETS에 사람이 읽은 원문 근거와 함께 고정."""
import json, sys, hashlib, datetime, urllib.request, uuid
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
RUN = "license-text-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
TARGETS = {
  "7-zip": {"urls": ["https://raw.githubusercontent.com/ip7z/7zip/main/DOC/License.txt", "https://www.7-zip.org/license.txt"],
            "must": ["version 2.1 of the License, or (at your option) any later version", "unRAR license restriction", "BSD 3-clause License", "BSD 2-clause License"],
            "spdx": "LGPL-2.1-or-later AND BSD-3-Clause AND BSD-2-Clause AND LicenseRef-unRAR-restriction",
            "note": "대부분 GNU LGPL 2.1 이상, Rar* 파일은 LGPL+unRAR 제한, 일부 BSD 3/2-clause, 일부 public domain"},
  "gimp": {"urls": ["https://gitlab.gnome.org/GNOME/gimp/-/raw/master/COPYING"],
           "must": ["GNU GENERAL PUBLIC LICENSE", "Version 3, 29 June 2007"],
           "spdx": "GPL-3.0",
           "note": "COPYING은 GPL v3 전문. 'or later' 여부는 이 파일에 없음(GitLab 자동 판별은 gpl-3.0+) — 소스 헤더 확인 전까지 GPL-3.0으로만 기재"},
  "inkscape": {"urls": ["https://gitlab.com/inkscape/inkscape/-/raw/master/COPYING"],
               "must": ["the complete binaries of Inkscape are currently covered by the terms of GNU GPL version 3 or later",
                        "Most Inkscape source code is available under the GNU General Public License, version 2 or later"],
               "spdx": "GPL-3.0-or-later",
               "note": "배포 바이너리 기준 GPL 3 이상. 소스 대부분은 GPL-2.0-or-later, 일부 CC0·LGPL·MPL"},
  "nanazip": {"urls": ["https://raw.githubusercontent.com/M2Team/NanaZip/main/License.md"],
              "must": ["is distributed under the MIT", "distributed under the 7-Zip License", "CC BY-ND 4.0"],
              "spdx": "MIT AND LicenseRef-7-Zip",
              "note": "NanaZip 자체 코드 MIT, 7-Zip 유래 코드는 7-Zip 라이선스, 로고·아이콘은 CC BY-ND 4.0"},
}
apply = "--apply" in sys.argv
for tid, cfg in TARGETS.items():
    p = f"src/content/tools/{tid}.json"; t = json.load(open(p))
    srcs, ok = [], True
    for u in cfg["urls"]:
        txt = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "yeollin-dogu-verifier"}), timeout=20).read().decode("utf-8", "replace")
        flat = " ".join(txt.split())
        hit = [m for m in cfg["must"] if " ".join(m.split()) in flat]
        if u == cfg["urls"][0] and len(hit) != len(cfg["must"]): ok = False
        head = " / ".join(l.strip() for l in txt.splitlines() if l.strip())[:300]
        srcs.append({"url": u, "fetchedAt": NOW, "method": "readme" if "raw" in u and "github" in u else "official-site",
                     "excerpt": f"{head} … [sha256 {hashlib.sha256(txt.encode()).hexdigest()[:12]}]"})
    v = t["verification"]
    if not ok:
        v["unresolved"].append("라이선스 원문에서 기대 문구를 찾지 못함 — 판정 보류"); json.dump(t, open(p, "w"), ensure_ascii=False, indent=2); continue
    prev = t.get("pendingLicense")
    if apply and prev and prev["value"] == cfg["spdx"] and [s["excerpt"][-20:] for s in prev["sources"]] == [s["excerpt"][-20:] for s in srcs]:
        before = t["license"]["value"]
        t["license"] = {"value": cfg["spdx"], "status": "verified", "lastVerified": NOW, "sources": srcs}
        t.pop("pendingLicense")
        rec = {"at": NOW, "agent": "verifier", "runId": RUN, "target": f"tools/{tid}.license", "before": before, "after": cfg["spdx"],
               "sources": srcs, "tier": "C", "gates": ["license-text", "recheck-24h"], "commit": "pending"}
        json.dump(rec, open(f"src/content/changes/{datetime.date.today()}-{tid}-license-applied-{uuid.uuid4().hex[:6]}.json", "w"), ensure_ascii=False, indent=2)
    elif not apply:
        t["pendingLicense"] = {"value": cfg["spdx"], "note": cfg["note"], "proposedAt": NOW, "earliestApply": (datetime.datetime.fromisoformat(NOW) + datetime.timedelta(hours=24)).isoformat(), "sources": srcs}
        t["license"]["sources"] = srcs + [s for s in t["license"]["sources"] if s["method"] == "manual-seed"]
        v["unresolved"] = [u for u in v["unresolved"] if not u.startswith("라이선스 자동 판별 불가")] + [f"라이선스 C등급 대기: 제안 {cfg['spdx']} (24시간 뒤 재확인)"]
        rec = {"at": NOW, "agent": "verifier", "runId": RUN, "target": f"tools/{tid}.license", "before": t["license"]["value"], "after": cfg["spdx"],
               "sources": srcs, "tier": "C", "gates": ["license-text", "pending:recheck-24h"], "commit": "pending"}
        json.dump(rec, open(f"src/content/changes/{datetime.date.today()}-{tid}-license-proposed-{uuid.uuid4().hex[:6]}.json", "w"), ensure_ascii=False, indent=2)
    json.dump(t, open(p, "w"), ensure_ascii=False, indent=2)
    print(tid, cfg["spdx"], "applied" if apply else "pending", [s["url"] for s in srcs])
