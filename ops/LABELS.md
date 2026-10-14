# 이슈 라벨 (기준 목록)

워크플로가 `gh issue create --label` 로 라벨을 붙이기 **전에** `bash scripts/ensure_labels.sh`를 실행한다.
스크립트가 `gh label create <이름> --force --color <6자리> --description <설명>`으로 없으면 만들고, 있으면 색과 설명을 맞춘다.

권한: 해당 job의 `permissions`에 `issues: write`가 있어야 한다. `contents: write`만으로는 라벨을 만들지 못한다.

실패한 실행: Discover run [38580319310](https://github.com/scottnaddle/open-tools-alternatives/actions/runs/38580319310) — `could not add label: 'software' not found`.

## 에이전트 단계 (AGENTS.md)

| 라벨 | 색 | 설명 |
|---|---|---|
| `agent/discovery` | `d93f0b` | 1번 에이전트(발굴) 처리 중 |
| `agent/research` | `fbca04` | 2번 에이전트(연구) 처리 중 |
| `agent/build` | `0e8a16` | 3번 에이전트(제조) 처리 중 |
| `agent/verify` | `5319e7` | 4번 에이전트(검수) 처리 중 |
| `agent/published` | `0e8a16` | 5번 에이전트(게시) 완료 |
| `agent/verifier` | `0a3069` | 일일 검증 PR. CI 통과 후 스쿼시 자동 병합 |

`agent/verifier` 는 이슈 단계가 아니라 **일일 검증 PR**에만 붙입니다. 브랜치가 `daily-verifier/` 일 때 `scripts/daily_verifier_pr.sh` 가 붙입니다. 콘텐츠·디자인·발굴 PR에는 붙이지 않습니다.

## 큐·상태 (AGENTS.md)

| 라벨 | 색 | 설명 |
|---|---|---|
| `queue/research` | `1d76db` | 조사 필요 (새 대안·스킬 후보 또는 정정) |
| `queue/verify` | `1d76db` | 기존 팩트 재확인 |
| `queue/deploy` | `1d76db` | 배포 대기 |
| `status/blocked-human` | `e99695` | 사람 개입 필요 (로그인·승인) |
| `priority/urgent` | `b60205` | 긴급 (운영 장애, 유료 전환 공식 발표, 데이터 손상) |

`priority/urgent`는 주간 검증이 운영 장애·유료 전환 공식 발표·데이터 손상을 표시할 때 쓰는 라벨이다. weekly-audit도 실행 전에 이 목록 전체를 만든다.

## 발굴 슬롯 종류 (discover.yml)

| 라벨 | 색 | 설명 |
|---|---|---|
| `software` | `0052cc` | 발굴 슬롯 종류: 소프트웨어(도구) |
| `skill` | `6f42c1` | 발굴 슬롯 종류: AI 스킬 |

이슈 템플릿이 미리 붙이는 `queue/research`, `queue/verify`도 위 목록에 있다.

목록을 바꿀 때는 `scripts/ensure_labels.sh`와 이 파일을 같이 고친다.
