#!/usr/bin/env python3
"""스킬 데이터 검증 — src/content/skills/*.json의 게이트 (src/content.config.ts와 목록 일치 필수).
위반 시 exit 1로 CI/빌드 실패. 규칙 근거: ops/RESEARCH.md 4절."""

import json
import re
import sys
from pathlib import Path

ALLOWED = {
    "MIT", "Apache-1.1", "Apache-2.0",
    "BSD-1-Clause", "BSD-2-Clause", "BSD-2-Clause-FreeBSD", "BSD-3-Clause",
    "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "MPL-1.1", "MPL-2.0", "ISC", "Unlicense", "CC0-1.0", "0BSD", "Zlib", "Artistic-2.0", "EPL-2.0",
}
CATEGORIES = {"수업자료·발표", "그림·도해", "영상·미디어", "데이터·차트", "교사 업무·글쓰기", "웹·앱 만들기", "기타"}
SCOPES = {"수업용", "교사 개인용"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check_file(path: Path) -> list[str]:
    errors = []
    try:
        s = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path.name}: JSON 파싱 실패 ({e})"]
    sid = s.get("slug", path.stem)

    lic = s.get("license")
    if lic is None:
        errors.append(f"{sid}: license가 없음 — 라이선스 없는 스킬은 게시 금지")
    elif lic not in ALLOWED:
        errors.append(f"{sid}: license '{lic}'이(가) 허용목록에 없음 (AGPL·NOASSERTION·비OSI 제외 규칙)")

    if s.get("category") not in CATEGORIES:
        errors.append(f"{sid}: category '{s.get('category')}' 미정의 값")
    if s.get("usageScope") not in SCOPES:
        errors.append(f"{sid}: usageScope '{s.get('usageScope')}' 미정의 값")

    url = (s.get("sourceUrl") or "").rstrip("/")
    repo = (s.get("github") or {}).get("repo") or ""
    norm = re.sub(r"^https?://github\.com/", "", url).rstrip("/").lower()
    if not repo or norm != repo.lower():
        errors.append(f"{sid}: sourceUrl({url})과 github.repo({repo}) 불일치")

    if not DATE.match(s.get("dateChecked") or ""):
        errors.append(f"{sid}: dateChecked가 YYYY-MM-DD 형식 아님: {s.get('dateChecked')}")

    pt, pp = s.get("previewType"), s.get("previewPath")
    if pt in ("iframe", "image") and not pp:
        errors.append(f"{sid}: previewType={pt}인데 previewPath 없음")

    pm = s.get("previewMethod")
    if pt in ("iframe", "image") and pm not in ("self-made", "official-example"):
        errors.append(f"{sid}: 미리보기가 있는데 previewMethod(직접 생성/공식 예시) 표기 없음 — 출처 표기 원칙(AGENTS.md 1·2)")

    gh_lic = (s.get("github") or {}).get("license")
    if lic and gh_lic and gh_lic.startswith(("AGPL", "NOASSERTION", "Other")):
        errors.append(f"{sid}: github.license '{gh_lic}'이 제외 대상 — 재조사 필요")
    return errors


def main() -> int:
    files = sorted(Path("src/content/skills").glob("*.json"))
    if not files:
        print("✗ src/content/skills에 데이터가 없음")
        return 1
    all_errors = []
    for f in files:
        all_errors.extend(check_file(f))
    if all_errors:
        print("❌ 스킬 게이트 위반:")
        for e in all_errors:
            print(f"  - {e}")
        print(f"\n총 {len(all_errors)}건. 규칙: ops/RESEARCH.md 4절. 데이터 수정 후 다시 실행하세요.")
        return 1
    print(f"✓ 스킬 게이트 검증 통과 ({len(files)}개 스킬, 라이선스 허용목록 {len(ALLOWED)}종)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
