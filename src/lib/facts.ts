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
