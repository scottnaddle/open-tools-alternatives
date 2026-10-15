"""카탈로그 라이선스를 GitHub SPDX로 덮어쓰지 않는 목록.

GitHub license API는 비어 있거나(NOASSERTION) 공식 문서와 다른 SPDX만
돌려주는 저장소가 있다. verify.py와 daily_verifier.py가 같은 목록을 본다.
"""

# 도구 id → 유지할 SPDX. 값을 바꿀 때는 원문 출처를 도구 JSON에 먼저 넣는다.
LICENSE_KEEP = {
    # LibreOffice/core API는 GPL-3.0. 공식 페이지는 MPL-2.0.
    "libreoffice": "MPL-2.0",
    # 아래 넷은 GitHub가 NOASSERTION/없음이라 라이선스 원문으로 확정했다.
    "7-zip": "LGPL-2.1-or-later AND BSD-3-Clause AND BSD-2-Clause AND LicenseRef-unRAR-restriction",
    "gimp": "GPL-3.0-or-later",
    "nanazip": "MIT AND LicenseRef-7-Zip",
    "inkscape": "GPL-3.0-or-later",
}


def should_apply_github_spdx(tool_id, current, api_spdx):
    """GitHub spdx_id로 카탈로그 라이선스를 바꿔도 되면 True.

    고정 목록에 있는 도구는 API 값과 달라도 바꾸지 않는다.
    NOASSERTION·빈 값은 자동 판별로 쓰지 않는다.
    """
    if tool_id in LICENSE_KEEP:
        return False
    if not api_spdx or api_spdx == "NOASSERTION":
        return False
    return current != api_spdx
