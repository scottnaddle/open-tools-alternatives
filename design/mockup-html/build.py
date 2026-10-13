#!/usr/bin/env python3
# 독립 HTML 시안 생성기 (LLM 호출 없음). 데이터: ../site/src/content, 예시: ../site/src/data
import json, glob, os, html
R = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(R, '..', 'site', 'src')
L = lambda p: json.load(open(p, encoding='utf-8'))
TOOLS = {os.path.basename(p)[:-5]: L(p) for p in glob.glob(f'{S}/content/tools/*.json')}
APPS = {os.path.basename(p)[:-5]: L(p) for p in glob.glob(f'{S}/content/school-apps/*.json')}
CH = sorted([L(p) for p in glob.glob(f'{S}/content/changes/*.json')], key=lambda c: c['at'], reverse=True)
ICONS = L(f'{S}/data/icons.json'); SV = L(f'{S}/data/ui-svgs.json'); EXF = L(f'{S}/data/example-facts.json')['tools']; UX = L(f'{S}/data/ui-examples.json')
e = lambda s: html.escape(str(s), quote=True)
CAT = {'영상·오디오': ('#FCE9DE', '#9A3B12', '#F2CDB8'), '이미지·디자인': ('#F3E6F7', '#6B2C80', '#E0C8EA'), '문서·오피스': ('#E3ECF8', '#1F4E8C', '#C6D6EE'),
       '수업 도구': ('#E4EFE8', '#1E6A47', '#C4DCCD'), 'AI': ('#ECE8FB', '#4B3A9A', '#D4CCF3'), '유틸리티': ('#F1EFE6', '#5B5432', '#DDD9C8')}
tone = lambda c: '--tint:%s;--tink:%s;--tbd:%s' % CAT.get(c, CAT['유틸리티'])
PAL = ['#1E6A47', '#1F4E8C', '#9A3B12', '#6B2C80', '#4B3A9A', '#5B5432']
def col(n):
    h = 0
    for c in n: h = (h * 31 + ord(c)) & 0xffffffff
    return PAL[h % 6]
def mono(n):
    import re
    w = re.split(r'[\s.-]', n)[0]
    return w if re.fullmatch(r'[A-Z0-9]{2,3}', w) else (re.sub(r'[^A-Za-z0-9]', '', n)[:2] or n[:1])
HEALTH = {'active': '개발 활발', 'slowing': '개발 느려짐', 'stale': '개발 멈춤', 'archived': '개발 중단'}
RANK = {'쉬움': 0, '보통': 1, '어려움': 2, '서버 구축': 3}
SCOPE = {'personal': '개인 업무용', 'demo': '수업 시연용', 'offline-install': '설치형 오프라인', 'student-use-check': '학생 직접 사용'}
MOE = 'https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=105007&lev=0&m=020402'
def scopes(x):
    s = ['personal']
    if x.get('account') != 'required': s.append('demo')
    if x.get('network') in ('offline', 'first-run') and x.get('studentData') in ('none', 'local-only'): s.append('offline-install')
    if x.get('studentData') == 'sent-to-server' or x.get('account') == 'required': s.append('student-use-check')
    return s
def kdate(iso): return iso[:10] if iso else '미정'

def status(f):
    ok = f['status'] == 'verified'
    src = ''.join(f'<li><a href="{e(s["url"])}">{e(s["url"])}</a><br><small>{e(s["method"])}, {kdate(s["fetchedAt"])}</small></li>' for s in f['sources'])
    return f'<span class="st {"st-ok" if ok else "st-wait"}">{"확인됨" if ok else "확인 중"}</span><details class="src"><summary>출처 {len(f["sources"])}</summary><ul>{src}</ul></details>'
EX = '<span class="st st-ex">예시 데이터</span>'
def ic(name): return ICONS.get(name, ICONS['cloud'])
def mono_el(n, cls='mono2'): return f'<span class="{cls}" aria-hidden="true" style="background:{col(n)}">{e(mono(n))}</span>'
def plats(t):
    p = t['platforms']['value']
    rows = [('Windows', p['windows']), ('macOS', p['macos']), ('Linux', p['linux']), ('웹', 'yes' if p['web'] == 'official' else 'partial' if p['web'] == 'self-host' else p['web']), ('휴대폰 브라우저', p['mobileWeb']), ('Android', p['android']), ('iOS', p['ios'])]
    return '<div class="plats"><span>쓸 수 있는 곳</span>' + ''.join(f'<span class="plat {"on" if v=="yes" else "part" if v=="partial" else "off"}">{l}{" (일부)" if v=="partial" else ""}</span>' for l, v in rows) + status(t['platforms']) + '</div>'
def bought(a):
    pn = a.get('procurementNote')
    return pn['value'].replace('2026년 1~10월 학교 구매 ', '') if pn else None

PAGES = [('index.html', '홈'), ('app-capcut.html', 'CapCut 대신'), ('compare.html', '비교'), ('teacher.html', '담임·교과'), ('it-lead.html', '정보부장·전산'), ('suggest.html', '대안 요청')]
CSS = open(os.path.join(R, 'style.css'), encoding='utf-8').read()
JS = open(os.path.join(R, 'app.js'), encoding='utf-8').read()
SEARCH = [{'id': k, 'name': a['name'], 'alts': [TOOLS[x['tool']]['name'] for x in a['alternatives']]} for k, a in APPS.items()]

def page(fn, title, body, cur):
    nav = ''.join(f'<a href="{f}"{" aria-current=page" if f == cur else ""}>{n}</a>' for f, n in PAGES[1:])
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | 열린도구</title><style>{CSS}</style></head><body>
<div class="proto">시안입니다. 모든 값은 확인 중이며, <span class="st st-ex">예시 데이터</span> 표시는 화면을 보여 주기 위한 값입니다.</div>
<header class="top"><div class="wrap"><a class="logo" href="index.html">{SV["logo"]}<b>열린도구</b><span>Alternatives</span></a>
<nav class="main" aria-label="주 메뉴">{nav}</nav><a class="btn soft" href="index.html#news">뉴스레터 구독</a></div></header>
<main id="main">{body}</main>
<footer><div class="wrap"><span>각 프로젝트의 공개 자료로 정리한 정보입니다. 학교 적합성이나 법적 요건 충족 여부는 판정하지 않습니다.</span><span>구매 학교 수 출처: school-edtech.kr (2026년 1~10월, 확인 중)</span></div></footer>
<button class="ask-btn" id="askBtn" aria-expanded="false" aria-controls="askPanel">{SV["ask"]}질문하기</button>
<section class="ask" id="askPanel" role="dialog" aria-label="질문하기" hidden><header><div class="askh"><b>질문하기</b><button class="btn" id="askClose">닫기</button></div>
<div class="ai-note">AI 에이전트가 이 사이트의 정보만 바탕으로 답합니다. 틀릴 수 있으니 근거 페이지를 확인하세요.</div></header>
<div class="msgs"><div class="msg me">CapCut 대신 학생 웨일북에서 쓸 수 있는 거 있어요?</div><div class="msg bot"><span class="st st-ex">예시 답변</span><br>웨일북에서는 설치 없이 브라우저로 여는 OpenCut이 있어요. 템플릿·자동 효과와 휴대폰 앱은 아직 없어요. Shotcut은 컴퓨터실 PC에 설치해서 씁니다.<a class="cite" href="app-capcut.html">근거: CapCut 대신 쓸 수 있는 오픈소스</a></div></div>
<form onsubmit="return false"><label class="sr" for="askInput">질문 입력</label><div class="row"><textarea id="askInput" maxlength="1000" placeholder="예: 알집 대신 쓸 프로그램은?"></textarea><button class="btn primary">보내기</button></div><span class="hint">이름·학교·연락처는 적지 마세요.</span></form></section>
<script>const SEARCH={json.dumps(SEARCH, ensure_ascii=False)};{JS}</script></body></html>'''

# ── 홈 ──
def landing():
    order = sorted(APPS.items(), key=lambda kv: -int((__import__('re').findall(r'([\d,]+)개교', bought(kv[1]) or '') or ['0'])[-1].replace(',', '')))
    nalts = sum(len(a['alternatives']) for a in APPS.values())
    def lc(k, a):
        href = 'app-capcut.html' if k == 'capcut' else f'index.html#app-{k}'
        b = bought(a)
        return f'''<a class="lcard" id="app-{k}" href="{href}" style="{tone(a["category"])}"><span class="top"><span class="ic" aria-hidden="true">{ic(a["icon"])}</span><span><b>{e(a["name"])} 대신</b><br><span class="n">{("학교 구매 " + e(b)) if b else "현장에서 많이 쓰는 앱"}</span></span></span><span class="alts">{", ".join(e(TOOLS[x["tool"]]["name"]) for x in a["alternatives"])}</span></a>'''
    linked = {x['tool'] for a in APPS.values() for x in a['alternatives']}
    recent = sorted([t | {'id': k} for k, t in TOOLS.items() if k in linked and not t['github']['archived']], key=lambda t: t['github'].get('official', {}).get('lastActivity') or t['github']['lastPush'], reverse=True)[:6]
    anchor = lambda tid: next(a['name'] for a in APPS.values() if any(x['tool'] == tid for x in a['alternatives']))
    row = lambda t: f'<div class="row">{mono_el(t["name"])}<span class="mid"><b>{e(t["name"])}</b><span>{e(anchor(t["id"]))} 대신, {e(t["schoolUse"]["value"])}</span></span><span class="date">{kdate(t["github"].get("official",{}).get("lastActivity") or t["github"]["lastPush"])}</span></div>'
    feat = ''.join(f'<div class="row">{mono_el(TOOLS[i]["name"])}<span class="mid"><b>{e(TOOLS[i]["name"])}</b><span>{e(why)}</span></span>{EX}</div>' for i, why in UX['featured'] if i in TOOLS)
    def cc(c):
        have = [i for i in c['tools'] if i in TOOLS]
        return f'<div class="ccard"><b>{e(c["title"])}</b><p>{e(c["intro"])}</p><span class="minis" aria-hidden="true">{"".join(f"""<span style="background:{col(TOOLS[i]["name"])}">{e(mono(TOOLS[i]["name"]))}</span>""" for i in have[:5])}</span><span class="hint">1차 공개 도구 {len(have)}개 · 목록은 {EX}</span></div>'
    warned = [t for t in TOOLS.values() if t['health'] in ('stale', 'archived') or t['github']['archived']]
    wrows = ''.join(f'<div class="warnrow"><span class="tagf">{HEALTH[t["health"]]}</span><b>{e(t["name"])}</b><span class="hint">GitHub 기준, 확인 {kdate(t["github"]["fetchedAt"])}</span></div>' for t in warned) or '<div class="warnrow"><b>지금은 알림이 없어요</b><span class="hint">1차 공개 도구 14개 중 저장소 보관이나 개발 멈춤으로 확인된 도구가 없습니다. 서비스 종료·유료 전환은 공식 발표가 나오면 여기에 올립니다.</span></div>'
    cats = ''.join(f'<a href="#apps" style="{tone(c)};background:var(--tint);color:var(--tink)">{c}<span>{n}</span></a>' for c in CAT for n in [sum(1 for a in APPS.values() if a['category'] == c)] if n)
    quick = ''.join(f'<a href="{"app-capcut.html" if k=="capcut" else "#app-"+k}">{e(APPS[k]["name"])} 대신</a>' for k in ['capcut', 'alzip', 'hancom-office', 'bandicam-ocam', 'photoshop'])
    swap = ''.join(f'<li><span class="from" style="{tone(APPS[a]["category"])}">{ic(APPS[a]["icon"])}{e(APPS[a]["name"])}</span><span class="to">{e(TOOLS[t]["name"])}</span></li>' for a, t in [('capcut', 'shotcut'), ('alzip', '7-zip'), ('hancom-office', 'h2orestart'), ('photoshop', 'krita')])
    return f'''<section class="hero-land"><div class="wrap herogrid"><div>
<h1>학교에서 쓰는 앱, 무료 오픈소스로 바꿔 쓸 수 있을까?</h1>
<p class="stat">학교 앱 <b>{len(APPS)}개</b>에 대한 오픈소스 대안 <b>{nalts}건</b>. 기기 지원과 설치 난이도까지 출처와 함께 정리하고, AI 에이전트가 매일 다시 확인합니다.</p>
<form class="hsearch" role="search" onsubmit="return false"><label class="sr" for="hq">프로그램 이름 검색</label><input id="hq" type="search" autocomplete="off" placeholder="지금 쓰는 프로그램 이름 (예: CapCut, 알집, 한글)"><button>대안 찾기</button></form><ul class="ac" id="ac" hidden></ul>
<div class="quick"><span class="hint">많이 찾는 대체</span>{quick}</div></div>
<ol class="swap" aria-label="바꿔 쓰기 예">{swap}</ol></div></section>
<div class="wrap">
<div class="sh" id="apps"><h2>학교들이 많이 산 앱의 대안</h2><span class="hint">2026년 1~10월 공공 조달 기록(school-edtech.kr) <span class="st st-wait">확인 중</span></span></div>
<div class="lgrid">{"".join(lc(k, a) for k, a in order)}</div>
<div class="two"><section><div class="sh"><h2>최근 개발이 활발한 대안</h2><span class="hint">공식 저장소의 마지막 개발일, 2026-10-13 조회</span></div><div class="list">{"".join(row(t) for t in recent)}</div></section>
<section><div class="sh"><h2>이달에 소개하는 도구</h2><span class="hint">선정 이유를 밝힙니다. 추천이 아닙니다.</span></div><div class="list">{feat}</div></section></div>
<div class="sh"><h2>학교 모음집</h2><span class="hint">어떤 도구를 묶을지는 아직 정하는 중이에요</span></div>
<div class="cgrid">{"".join(cc(c) for c in UX["collections"])}</div>
<div class="two"><section><div class="sh"><h2>개발 중단·종료 알림</h2><span class="hint">공식 정보로 확인된 것만</span></div><div class="list">{wrows}</div></section>
<section><div class="sh"><h2>분야별로 둘러보기</h2></div><div class="cats">{cats}</div>
<p class="hint" style="margin-top:18px">많이 찾는 앱 순위는 만들지 않습니다. 검색어는 새 대안을 찾는 데만 씁니다.</p></section></div>
<div class="cta" id="news"><div class="cta-warn"><h2>아직 좋은 대안이 없는 앱</h2><p>{e(UX["noAlternative"])} {EX}</p><a class="btn" href="suggest.html">대안 요청하기</a></div>
<div class="cta-brand"><h2>매주 바뀐 정보를 메일로</h2><p>새 대안, 선생님께 영향 있는 업데이트, 종료·유료 전환 소식을 한 번에 받아 보세요.</p><form onsubmit="return false" class="nl"><label class="sr" for="nl">이메일</label><input id="nl" type="email" placeholder="학교 이메일"><button class="btn primary">구독하기</button></form></div></div></div>'''

# ── 앱 상세 (CapCut) ──
def detail(k='capcut'):
    a = APPS[k]; alts = [(x, TOOLS[x['tool']] | {'id': x['tool']}) for x in a['alternatives']]
    pick = lambda f: ', '.join(t['name'] for x, t in alts if f(t['platforms']['value'], t))
    scene = [('웨일북·크롬북', pick(lambda p, t: p['web'] == 'official'), '설치 없이 브라우저로'), ('컴퓨터실 PC', pick(lambda p, t: 'yes' in (p['windows'], p['macos'], p['linux'])), '설치해서 사용'), ('휴대폰', pick(lambda p, t: 'yes' in (p['android'], p['ios'])), '앱으로 사용')]
    sc = ''.join(f'<dt>{n}</dt><dd>{"<b>"+e(v)+"</b> <span class=hint>"+h+"</span>" if v else "<span class=hint>아직 마땅한 오픈소스가 없어요</span>"}</dd>' for n, v, h in scene)
    def card(x, t):
        ex = EXF.get(t['id'], {}); sc = scopes(ex)
        warn = f'<p class="warnbox">학생이 직접 쓰면 학생 정보가 처리될 수 있어요. 학교 절차를 확인하세요. <a href="{MOE}">교육부 학습지원 소프트웨어 선정 기준 안내</a></p>' if 'student-use-check' in sc else ''
        gh = t['github']; act = gh.get('official', {}).get('lastActivity') or gh['lastPush']
        return f'''<article class="alt" data-lv="{0 if x["level"]["value"]=="거의 대체" else 1}" data-df="{RANK[x["installDifficulty"]]}" data-act="{e(act)}"><div class="ahead"><div class="amain">{mono_el(t["name"], "amono")}<div><h2>{e(t["name"])}</h2><p>{e(x["summary"])}</p></div></div>
<div class="badges"><span class="badge lv-{x["level"]["value"].split()[0]}">{x["level"]["value"]}</span>{status(x["level"])}<span class="badge df-{x["installDifficulty"]}">설치 {x["installDifficulty"]}</span></div></div>
{plats(t)}<div class="meta-row"><span class="tagh">{HEALTH[t["health"]]}, 최근 개발 {kdate(act)}</span><span class="tagh">라이선스 {e(t["license"]["value"] or "미정")} {status(t["license"])}</span></div>
<div class="schips"><span class="hint">쓰임 범위</span>{"".join(f'<span class="schip s-{s}">{SCOPE[s]}</span>' for s in sc)}{EX}</div>{warn}
<div class="actions"><a class="btn primary" href="compare.html">다른 대안과 비교</a><a class="btn" href="https://github.com/{e(gh["repo"])}">원 프로젝트 보기</a><a class="btn ghost" href="suggest.html#report">정보가 틀렸나요?</a></div></article>'''
    fm = next((f for f in UX['featureMatrix'] if f['schoolAppId'] == k), None); table = ''
    if fm:
        ids = [i for i in fm['features'][0]['alternatives'] if i in TOOLS]
        cell = lambda v: f'<td><span class="v {v or "null"}">{ {"yes":"지원","no":"미지원","partial":"일부"}.get(v,"확인 중")}</span></td>'
        rows = ''.join(f'<tr><th scope="row">{e(f["feature"])}</th>{cell(None)}' + ''.join(cell(None) for i in ids) + '</tr>' for f in fm['features'])
        table = f'<section class="cmp"><div class="cmph"><h2>기능 비교: {e(fm["scenario"])}</h2><p class="hint">공식 문서로 확인한 칸부터 채웁니다. 기능 목록은 {EX}</p></div><div class="tscroll"><table><thead><tr><th scope="col">기능</th><th scope="col">{e(a["name"])}</th>{"".join(f"<th scope=col>{e(TOOLS[i]['name'])}</th>" for i in ids)}</tr></thead><tbody>{rows}</tbody></table></div></section>'
    alts.sort(key=lambda p: (0 if p[0]['level']['value'] == '거의 대체' else 1, RANK[p[0]['installDifficulty']]))
    return f'''<div class="detail" style="{tone(a["category"])}"><a class="back" href="index.html">홈으로</a>
<p class="kick">{e(a["category"])}, 학교 구매 {e(bought(a) or "미정")} {status(a["procurementNote"])}</p>
<div class="dhead"><span class="tile" aria-hidden="true">{ic(a["icon"])}</span><h1>{e(a["name"])} 대신 쓸 수 있는 오픈소스</h1></div>
<div class="scene"><b>어디서 쓰나요?</b><dl>{sc}</dl><span class="by">각 대안의 기기 지원 정보로 만든 요약입니다. 기기 지원은 확인 중이에요.</span></div>
<div class="gap"><strong>미리 알아두세요.</strong><span>{e(a["gap"]["value"])} {status(a["gap"])}</span></div>
<div class="toolbar"><span class="hint">대안 {len(alts)}개. 점수나 인기로 줄 세우지 않습니다.</span><label class="hint">정렬 <select id="sortSel"><option value="lv">대체 정도, 설치 쉬운 순</option><option value="df">설치 쉬운 순</option><option value="act">최근 개발일 순</option></select></label></div>
<div id="alts">{"".join(card(x, t) for x, t in alts)}</div>{table}
<section class="notify"><div><h2>설치 없이 학교에서 바로 쓰고 싶으신가요?</h2><p>학교 기기에서 바로 열리는 버전이 생기면 알려 드릴게요.</p></div><form onsubmit="return false"><label class="sr" for="em">학교 이메일</label><input id="em" type="email" placeholder="학교 이메일"><button class="btn primary">알림 받기</button></form></section></div>'''

def facts_dl(t, k):
    ex = EXF.get(k, {}); p = t['platforms']['value']; gh = t['github']
    K = {'yes': '지원', 'partial': '일부', 'no': '미지원', 'official': '공식 웹', 'self-host': '자체 호스팅', 'none': '없음', 'local-only': '기기 안에만', 'sent-to-server': '서버로 전송', 'offline': '인터넷 없이', 'first-run': '첫 실행만 인터넷', 'online': '인터넷 필요', 'required': '필요', 'portable-available': '포터블판 있음', 'optional': '선택'}
    rows = [('설치 난이도', e(t['installDifficulty']['value']) + status(t['installDifficulty'])),
            ('라이선스', e(t['license']['value'] or '미정') + status(t['license']) + (f'<div class="hint">{e(t["pendingLicense"]["note"])} (변경 제안, 검토 대기)</div>' if t.get('pendingLicense') else '')),
            ('Windows / Mac / 웹', f'{K[p["windows"]]} / {K[p["macos"]]} / {K[p["web"]]}' + status(t['platforms'])),
            ('최근 개발', kdate(gh.get('official', {}).get('lastActivity') or gh['lastPush']) + f' <span class="hint">GitHub API, {kdate(gh["fetchedAt"])} 조회</span>'),
            ('최신 버전', e(gh['latestRelease']['tag']) if gh.get('latestRelease') else '미정'),
            ('한국어 화면', K.get(ex.get('koreanUI'), '미정') + ' ' + EX), ('인터넷', K.get(ex.get('network'), '미정') + ' ' + EX),
            ('학생 데이터', K.get(ex.get('studentData'), '미정') + ' ' + EX), ('관리자 권한', K.get(ex.get('adminRequired'), '미정') + ' ' + EX)]
    return '<table class="ftable">' + ''.join(f'<tr><th scope="row">{a}</th><td>{b}</td></tr>' for a, b in rows) + '</table>'

def compare(a='shotcut', b='opencut'):
    ta, tb = TOOLS[a], TOOLS[b]
    col_ = lambda t, k: f'<section class="panel"><div class="amain">{mono_el(t["name"], "amono")}<h2>{e(t["name"])}</h2></div>{plats(t)}{facts_dl(t, k)}</section>'
    return f'''<div class="detail wide"><a class="back" href="app-capcut.html">CapCut 대신 쓸 수 있는 오픈소스</a>
<h1 class="ph">{e(ta["name"])}와 {e(tb["name"])} 나란히 보기</h1><p class="lead">CapCut 대안 두 개의 사실만 나란히 놓았어요. 더 나은 쪽을 고르거나 점수를 매기지 않습니다.</p>
<div class="cmpgrid">{col_(ta, a)}{col_(tb, b)}</div></div>'''

def teacher():
    easy = [(k, x, TOOLS[x['tool']]) for k, a in APPS.items() for x in a['alternatives'] if x['installDifficulty'] == '쉬움' and TOOLS[x['tool']]['platforms']['value']['web'] == 'official']
    rows = ''.join(f'<div class="row">{mono_el(t["name"])}<span class="mid"><b>{e(t["name"])}</b><span>{e(APPS[k]["name"])} 대신, {e(x["summary"])}</span></span></div>' for k, x, t in easy)
    return f'''<div class="detail"><h1 class="ph">담임·교과 선생님</h1><p class="lead">수업 준비와 수업 시간에 바로 쓰는 경우를 먼저 모았어요. 학생이 직접 쓰게 하려면 학교 절차를 먼저 확인하세요.</p>
<section class="panel"><h2>설치 없이 브라우저로 여는 대안</h2><div class="list">{rows or '<p class="hint">아직 없어요.</p>'}</div><p class="hint">공식 웹 지원과 설치 난이도는 확인 중이에요.</p></section>
<section class="panel"><h2>쓰임 범위 읽는 법</h2><div class="schips">{"".join(f'<span class="schip s-{s}">{n}</span>' for s, n in SCOPE.items())}</div>
<p>개인 업무용과 수업 시연용은 선생님 기기에서 쓰는 경우예요. 학생 직접 사용이 붙은 도구는 학생 정보가 처리될 수 있어 <a href="{MOE}">교육부 학습지원 소프트웨어 선정 기준 안내</a>에 따라 학교 절차를 확인해야 합니다. 이 사이트는 심의 대상 여부를 판정하지 않습니다.</p></section>
<section class="panel"><h2>수업 장면별 안내</h2><div class="teams">{"".join(f'<div><b>{e(n)}</b><p>{e(d)}</p></div>' for n, d in UX["guides"]["obs-studio"]["uses"])}</div><p class="hint">OBS Studio 사용 장면 {EX}</p></section></div>'''

def itlead():
    rows = ''.join(f'<tr><th scope="row">{e(t["name"])}</th><td>{e(t["installDifficulty"]["value"])}</td><td>{e(t["license"]["value"] or "미정")} {status(t["license"])}</td><td>{ {"yes":"필요","portable-available":"포터블판 있음","none":"불필요"}.get(EXF.get(k,{}).get("adminRequired"),"미정")} {EX}</td></tr>' for k, t in sorted(TOOLS.items()))
    nv = sum(1 for t in TOOLS.values() if t['license']['status'] == 'verified')
    return f'''<div class="detail wide"><h1 class="ph">정보부장·전산 담당 선생님</h1><p class="lead">컴퓨터실 일괄 설치에 필요한 사실을 표 하나로 모았어요. 학교 PC 보안 프로그램이나 복원 솔루션을 우회하는 방법은 안내하지 않습니다.</p>
<section class="cmp"><div class="cmph"><h2>도구 14개 설치 정보</h2><p class="hint">라이선스 확인됨 {nv}개, 확인 중 {14-nv}개</p></div><div class="tscroll"><table><thead><tr><th scope="col">도구</th><th scope="col">설치 난이도</th><th scope="col">라이선스</th><th scope="col">관리자 권한</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="panel"><h2>준비 중인 자료</h2><ul class="changes"><li><b>7-Zip 컴퓨터실 일괄 배포</b><div class="meta">MSI, winget, 조용한 설치. 공식 문서로 확인한 뒤 올립니다.</div></li><li><b>무상 사용 근거 1쪽 서류</b><div class="meta">도구별 라이선스 이름, 원문 주소, 확인 날짜를 담은 서식. 법적 검토를 대신하지 않습니다.</div></li></ul></section>
<section class="panel"><h2>최근 변경 기록</h2><ul class="changes">{"".join(f'<li><b>{e(c["target"])}</b><div class="meta">{kdate(c["at"])}, {e(c["agent"])}, {c["tier"]}등급 {"(검토 대기)" if c["tier"]=="C" else ""}</div></li>' for c in CH[:8])}</ul></section></div>'''

def suggest():
    return f'''<div class="detail"><h1 class="ph">대안 요청하기</h1><p class="lead">대신할 오픈소스를 찾고 싶은 앱이나, 알고 있는 오픈소스를 알려 주세요. 에이전트가 공식 자료로 확인한 뒤 올립니다.</p>
<form class="panel fform" onsubmit="return false"><label for="s1">지금 쓰는 앱</label><input id="s1" placeholder="예: 띵커벨">
<label for="s2">아는 오픈소스가 있다면</label><input id="s2" placeholder="이름이나 공식 주소">
<label for="s3">어떤 수업에서 쓰나요?</label><textarea id="s3" rows="4"></textarea>
<p class="hint">이름·학교·학생 정보는 적지 마세요. 요청은 공개 목록에 올라가며, 인기 투표로 순서를 정하지 않습니다.</p><button class="btn primary">요청 보내기</button></form>
<form class="panel fform" id="report" onsubmit="return false"><h2>정보가 틀렸나요?</h2><label for="r1">페이지나 도구 이름</label><input id="r1"><label for="r2">무엇이 틀렸나요? 근거 주소가 있으면 함께 적어 주세요</label><textarea id="r2" rows="4"></textarea><button class="btn primary">신고 보내기</button></form></div>'''

out = {'index.html': ('학교 앱 대신 쓰는 오픈소스', landing()), 'app-capcut.html': ('CapCut 대신 쓸 수 있는 오픈소스', detail()), 'compare.html': ('Shotcut과 OpenCut 비교', compare()),
       'teacher.html': ('담임·교과 선생님', teacher()), 'it-lead.html': ('정보부장·전산 담당', itlead()), 'suggest.html': ('대안 요청하기', suggest())}
for fn, (t, b) in out.items():
    open(os.path.join(R, fn), 'w', encoding='utf-8').write(page(fn, t, b, fn))
print('ok', list(out))
