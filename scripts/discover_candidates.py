#!/usr/bin/env python3
"""GitHub Search API JSON(stdin)을 발굴 이슈 코멘트 마크다운으로 바꾼다.

워크플로 YAML의 run 블록 안에서 파이썬을 0열 heredoc으로 두면 파싱이 깨지므로,
후보 정리 로직은 이 파일에 둔다. 출력 문구는 기존 워크플로와 같다.
"""

import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        print("검색 응답 파싱 실패: 빈 응답")
        return 0
    try:
        data = json.loads(raw)
        items = data.get("items", [])
        if not items:
            print("검색 결과 0건 — 참고 후보 없음")
            return 0
        out = ["### 참고 후보 (GitHub Search — 검토용)\n"]
        for repo in items[:5]:
            desc = repo.get("description") or "(설명 없음)"
            out.append(
                f"- **{repo['full_name']}** ⭐ {repo['stargazers_count']} — {desc} — {repo['html_url']}"
            )
        print("\n".join(out))
    except Exception as exc:
        print(f"검색 응답 파싱 실패: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
