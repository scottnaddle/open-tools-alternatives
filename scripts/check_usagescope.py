"""빌드 시 usageScope 규칙 검증 (PLAN 7.4, Task 3).
학교에서 학생과 쓸 수 있는 도구로 표시하려면 studentData, account, minAge가 verified여야 함.
그렇지 않으면 빌드 실패."""

import json, glob, sys

NOW_ISO = "2026-10-13T08:00:00+00:00"
errors = []

for f in sorted(glob.glob("src/content/tools/*.json")):
    with open(f) as fp:
        tool = json.load(fp)
    
    tid = f.split("/")[-1][:-5]
    scope = tool.get("usageScope", ["personal"])
    
    # student-use-check 태그가 있으면 검증
    if "student-use-check" in scope:
        student_data = tool.get("studentData")
        account = tool.get("account")
        min_age = tool.get("minAge")
        
        verified_fields = []
        if student_data and student_data.get("status") == "verified":
            verified_fields.append("studentData")
        if account and account.get("status") == "verified":
            verified_fields.append("account")
        if min_age and min_age.get("status") == "verified":
            verified_fields.append("minAge")
        
        if not verified_fields:
            errors.append(
                f"{tid}: usageScope에 'student-use-check'가 있지만 "
                f"studentData, account, minAge 중 어느 것도 verified 상태가 아닙니다. "
                f"학교 사용 가능 표시를 하려면 이 필드들이 공식 문서에서 확인되어야 합니다."
            )

if errors:
    print("❌ usageScope 규칙 위반:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
else:
    print("✓ usageScope 규칙 검증 통과")
