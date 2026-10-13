import example from '../data/example-facts.json';
export const MOE_URL = 'https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=105007&lev=0&m=020402';
export const EXAMPLE_LABEL = example._label;
export type Scope = 'personal' | 'demo' | 'offline-install' | 'student-use-check';
export const SCOPE_NAME: Record<Scope, string> = {
  personal: '개인 업무용', demo: '수업 시연용', 'offline-install': '설치형 오프라인', 'student-use-check': '학생 직접 사용',
};
export function exampleFor(id: string) { return (example.tools as Record<string, any>)[id]; }
// PLAN v4 7.4 파생 규칙 (공개 규칙). 입력이 예시 데이터면 결과도 예시.
export function deriveScope(x: any): Scope[] {
  const s: Scope[] = ['personal'];
  if (x.account !== 'required') s.push('demo');
  if (['offline', 'first-run'].includes(x.network) && ['none', 'local-only'].includes(x.studentData)) s.push('offline-install');
  if (x.studentData === 'sent-to-server' || x.account === 'required') s.push('student-use-check');
  return s;
}
export function devices(p: any) {
  return {
    pc: [p.windows, p.macos, p.linux].includes('yes'),
    chromebook: p.web === 'official',
    tablet: p.android === 'yes' || p.ios === 'yes',
    web: p.web === 'official',
  };
}
export const KO: Record<string, string> = { yes: '지원', partial: '일부', no: '미지원', official: '공식 웹', 'self-host': '자체 호스팅', none: '없음', 'local-only': '기기 안에만', 'sent-to-server': '서버로 전송', offline: '인터넷 없이', 'first-run': '첫 실행만 인터넷', online: '인터넷 필요', optional: '선택', required: '필요', 'portable-available': '포터블판 있음' };
// 홈 카테고리(앱 id 기준, 1차 공개 묶음)
export const CATEGORIES: [string, string, string[]][] = [
  ['video', '영상 편집', ['capcut', 'bandicam-ocam']], ['image', '이미지', ['photoshop', 'illustrator']],
  ['archive', '압축', ['alzip']], ['capture', '화면 캡처', ['alcapture', 'bandicam-ocam']],
  ['doc', '문서·HWP', ['hancom-office']], ['diagram', '다이어그램', ['visio-almind']], ['transfer', '파일 전송', ['file-transfer']],
];
// 검색 동의어 (앱 id → 다른 이름)
export const SYNONYMS: Record<string, string[]> = {
  capcut: ['캡컷', 'CapCut', '영상 편집'], alzip: ['알집', 'ALZip', '압축'], alcapture: ['알캡처', 'ALCapture', '캡처'],
  photoshop: ['포토샵', 'Photoshop', 'Adobe', '어도비'], illustrator: ['일러스트레이터', '일러', 'Illustrator', 'Adobe', '어도비'],
  'bandicam-ocam': ['반디캠', '오캠', 'Bandicam', 'oCam', '화면 녹화'], 'visio-almind': ['비지오', 'Visio', '알마인드', 'ALMind', '마인드맵', '순서도'],
  'file-transfer': ['에어드롭', 'AirDrop', '카톡 파일', '메신저', '파일 전송'], 'hancom-office': ['한글', '한컴', 'HWP', '한컴오피스'],
};
export function mono(name: string) {
  const w = name.split(/[\s.-]/)[0];
  return /^[A-Z0-9]{2,3}$/.test(w) ? w : name.replace(/[^A-Za-z0-9]/g, '').slice(0, 2) || name.slice(0, 1);
}
const PAL = ['#1E6A47', '#1F4E8C', '#9A3B12', '#6B2C80', '#4B3A9A', '#5B5432'];
export function col(name: string) { let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0; return PAL[h % PAL.length]; }
export const PLAT: [string, string, (p: any) => boolean][] = [
  ['win', 'Win', (p) => p.windows === 'yes'], ['mac', 'Mac', (p) => p.macos === 'yes'], ['linux', 'Linux', (p) => p.linux === 'yes'],
  ['web', '웹', (p) => p.web === 'official'], ['and', 'Android', (p) => p.android === 'yes'], ['ios', 'iOS', (p) => p.ios === 'yes'],
];

// ── v3: 사용자 시안(2026-10-13) 디자인 토큰 ──
export const CAT: Record<string, [string, string, string]> = {
  '영상·오디오': ['#FCE9DE', '#9A3B12', '#F2CDB8'], '이미지·디자인': ['#F3E6F7', '#6B2C80', '#E0C8EA'],
  '문서·오피스': ['#E3ECF8', '#1F4E8C', '#C6D6EE'], '수업 도구': ['#E4EFE8', '#1E6A47', '#C4DCCD'],
  'AI': ['#ECE8FB', '#4B3A9A', '#D4CCF3'], '유틸리티': ['#F1EFE6', '#5B5432', '#DDD9C8'],
};
export const CAT_ORDER = ['영상·오디오', '이미지·디자인', '문서·오피스', '수업 도구', 'AI', '유틸리티'];
export function tone(c: string) { const t = CAT[c] || CAT['유틸리티']; return `--tint:${t[0]};--tink:${t[1]};--tbd:${t[2]}`; }
export const RANK: Record<string, number> = { '쉬움': 0, '보통': 1, '어려움': 2, '서버 구축': 3 };
export const HEALTH: Record<string, string> = { active: '개발 활발', slowing: '개발 느려짐', stale: '개발 멈춤', archived: '개발 중단' };
export const dfClass = (d: string) => 'df-' + d.split(' ')[0];
// 시안의 "학교 사용 편의 점수" 공개 공식. 입력이 전부 확인 전(씨앗) 값이므로 결과는 예시로만 표시.
// 학교 조건(15)은 아직 확인된 값이 없어 0으로 계산.
export function score(level: string, diff: string, p: any, health: string) {
  const lv = level === '거의 대체' ? 1 : 0.5;
  const df = ({ '쉬움': 1, '보통': 0.6, '어려움': 0.3, '서버 구축': 0.1 } as any)[diff] ?? 0;
  const dev = ([p.windows === 'yes', p.web === 'official', p.android === 'yes' || p.ios === 'yes' || p.mobileWeb === 'yes'].filter(Boolean).length) / 3;
  const h = ({ active: 1, slowing: 0.6, stale: 0.2, archived: 0 } as any)[health] ?? 0.6;
  return Math.round(lv * 30 + df * 25 + dev * 20 + 0 * 15 + h * 10);
}
