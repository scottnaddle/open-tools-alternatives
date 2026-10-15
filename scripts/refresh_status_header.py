#!/usr/bin/env python3
"""STATUS.md의 '마지막 갱신' 한 줄만 고친다.

기능 PR에서는 실행하지 않는다. 병합 뒤에만 실행한다.
ops/status-log 의 `머리글:` 한 줄을 그 자리에 넣는다. 다른 줄은 바꾸지 않는다.

사용법:
  python3 scripts/refresh_status_header.py [--dry-run] [ops/status-log/파일.md]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "STATUS.md"
LOG_DIR = ROOT / "ops" / "status-log"
MARKER = "> 마지막 갱신:"


def log_files():
    return sorted(p for p in LOG_DIR.glob("*.md") if p.name != "README.md")


def header_from(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("머리글:"):
            text = line.split(":", 1)[1].strip()
            if not text:
                raise SystemExit(f"머리글이 비었습니다: {path}")
            return text
    raise SystemExit(f"머리글: 줄이 없습니다: {path}")


def main():
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 1:
        raise SystemExit("인자는 로그 파일 하나뿐입니다")
    if args:
        path = Path(args[0])
        if not path.is_absolute():
            path = ROOT / path
    else:
        files = log_files()
        if not files:
            raise SystemExit("ops/status-log 에 기록이 없습니다")
        path = files[-1]
    text = header_from(path)
    new_line = f"{MARKER} {text}"
    raw = STATUS.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    found = 0
    out = []
    for line in lines:
        if line.startswith(MARKER):
            found += 1
            if found == 1:
                out.append(new_line)
                continue
        out.append(line)
    if found != 1:
        raise SystemExit(f"마지막 갱신 줄이 {found}개입니다. 한 줄만 있어야 합니다.")
    rendered = newline.join(out)
    if raw.endswith(("\n", "\r\n")):
        rendered += newline
    if dry:
        print(new_line)
        return
    if rendered != raw:
        STATUS.write_text(rendered, encoding="utf-8")
    print(new_line)


if __name__ == "__main__":
    main()
