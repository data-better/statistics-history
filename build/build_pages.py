# -*- coding: utf-8 -*-
"""15개 HTML 페이지 생성 (PRD v2 §3, §6)"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from content import CHAPTERS

ROOT = "/home/claude/site"
DATA = json.loads(open(os.path.join(ROOT, "assets/data.js"), encoding="utf-8").read()
                  .split("window.__STATHIST__ = ", 1)[1].rstrip().rstrip(";"))
WORKS, FIELDS, CHAPMETA, PEOPLE, PRE = (DATA["works"], DATA["fields"], DATA["chapters"],
                                        DATA["people"], DATA["prehistory"])
FIELD_BY_KEY = {f["key"]: f for f in FIELDS}
N = len(WORKS)


def shell(title, desc, body, depth=0, scripts="", head="", main_class="wrap"):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='25' font-size='26'>&#128200;</text></svg>">
<link rel="stylesheet" href="{up}assets/site.css">
{head}</head>
<body>
<header data-header></header>
<main id="main" class="{main_class}">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p>통계학의 역사 — 1654 ~ 2015 · 저작 {N}편 · 인물 {len(PEOPLE)}종<br>
자료: 통계학사 타임라인 자료집 및 Wikipedia 『History of statistics』 ·
<a href="{up}appendix.html">출처와 제작 노트</a></p>
</div></footer>
<script src="{up}assets/data.js"></script>
<script src="{up}assets/site.js"></script>
{scripts}
</body>
</html>
"""


def write(path, html):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(html)
    return full


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def counts_by_field():
    return {f["key"]: sum(1 for w in WORKS if w["field"] == f["key"]) for f in FIELDS}


def span_by_field():
    out = {}
    for f in FIELDS:
        ys = [w["year"] for w in WORKS if w["field"] == f["key"]]
        out[f["key"]] = (min(ys), max(ys))
    return out


# ══════════════════════════════════════════════════════════ index (분야 게이트)
def page_index():
    cnt, spans = counts_by_field(), span_by_field()
    cards = ""
    for f in FIELDS:
        lo, hi = spans[f["key"]]
        cards += f"""
      <button class="field-card f-{f['slug']}" data-field="{esc(f['key'])}" aria-pressed="false">
        <h3>{esc(f['key'])}</h3>
        <p class="tagline">{esc(f['tag'])}</p>
        <div class="meta"><span>저작 {cnt[f['key']]}편</span><span>{lo} ~ {hi}</span></div>
        <div class="leads">{esc(' · '.join(f['leads']))}</div>
      </button>"""

    body = f"""<div class="wrap">
  <div class="prose" style="max-width:none">
    <p class="small muted" style="margin-bottom:6px">A History of Statistics</p>
    <h1 style="font-size:36px">확률에서 데이터과학까지,<br>통계학의 370년</h1>
    <p class="lede" style="max-width:56ch">도박판의 분배 문제에서 시작해 딥러닝에 이르기까지.
    {N}편의 논문과 저서로 따라가는 통계학의 역사입니다.</p>
    <div class="stat-row">
      <div class="stat"><b>370년</b><span>1654 ~ 2015</span></div>
      <div class="stat"><b>{N}편</b><span>주요 논문·저서</span></div>
      <div class="stat"><b>{len(PEOPLE)}명</b><span>인물·연구팀</span></div>
      <div class="stat"><b>5개</b><span>분야</span></div>
    </div>
  </div>

  <section id="fields" style="margin-top:38px">
    <h2 style="margin-top:0">어디서부터 볼까요?</h2>
    <p class="muted" style="max-width:60ch;margin-top:-4px">관심 분야를 고르면 타임라인과 이야기가 그 분야를 중심으로 열립니다.
    고르지 않아도 모든 기능을 쓸 수 있습니다.</p>
    <div class="grid grid-fields" style="margin-top:18px">{cards}
    </div>
    <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap">
      <a class="btn btn-primary" href="timeline.html" data-nodecorate id="btn-all">전체 보기 — 5개 분야를 모두</a>
      <a class="btn" href="story/index.html">처음부터 읽기</a>
    </div>
    <div id="field-panel" hidden></div>
  </section>

  <section style="margin-top:56px">
    <h2>한눈에 보기 — 무게중심의 이동</h2>
    <p class="muted small" style="max-width:60ch;margin-top:-6px">25년 구간마다 분야별 저작 수입니다.
    확률에서 추정·검정으로, 다시 데이터과학으로 옮겨가는 흐름이 보입니다.</p>
    <div class="card" style="padding:14px"><div id="density"></div></div>
  </section>
</div>"""

    script = """<script>
(function(){
 var SH=window.SH, D=SH.data, panel=document.getElementById('field-panel');
 var cnt={}; D.works.forEach(function(w){cnt[w.field]=(cnt[w.field]||0)+1;});

 document.querySelectorAll('.field-card').forEach(function(card){
   var key=card.getAttribute('data-field');
   if(SH.state.field===key){card.setAttribute('aria-pressed','true');show(key);}
   card.addEventListener('click',function(){
     var on=card.getAttribute('aria-pressed')==='true';
     document.querySelectorAll('.field-card').forEach(function(c){c.setAttribute('aria-pressed','false');});
     if(on){panel.hidden=true;panel.innerHTML='';SH.setField(null);return;}
     card.setAttribute('aria-pressed','true');
     show(key);
     var p=new URLSearchParams(location.search); p.set('field',key);
     history.replaceState(null,'',location.pathname+'?'+p.toString());
     SH.state.field=key; SH.ss('field',key);
     panel.scrollIntoView({behavior:'smooth',block:'nearest'});
   });
 });

 function show(key){
   var f=SH.fieldByKey[key];
   var list=D.works.filter(function(w){return w.field===key;}).sort(function(a,b){
     return (b.weight-a.weight)||(a.year-b.year);}).slice(0,5)
     .sort(function(a,b){return a.year-b.year;});
   var chaps=f.chapters.map(function(n){
     var c=SH.chapterOf(n);
     return '<a class="btn btn-sm" href="story/'+c.file+'">'+n+'장 '+SH.esc(c.title)+' →</a>';}).join('');
   panel.className='panel f-'+f.slug;
   panel.innerHTML='<h3 style="margin-top:0;color:var(--fc)">'+SH.esc(f.key)+' — '+SH.esc(f.tag)+'</h3>'
     +'<p style="max-width:62ch">'+SH.esc(f.blurb)+'</p>'
     +'<p class="small muted">이 분야 저작 '+cnt[key]+'편 · 대표 인물 '+SH.esc(f.leads.join(', '))+'</p>'
     +'<div class="links" style="display:flex;gap:8px;flex-wrap:wrap;margin:14px 0">'+chaps
     +'<a class="btn btn-sm btn-primary" href="timeline.html?field='+encodeURIComponent(key)+'">이 분야로 타임라인 열기 →</a></div>'
     +'<p class="lbl small muted" style="margin-bottom:6px">대표 저작</p><ul class="work-list">'
     +list.map(function(w){return '<li><a class="work-item f-'+f.slug+'" href="timeline.html?id='+encodeURIComponent(w.id)+'">'
       +'<span class="yr">'+w.year+'</span><span><span class="ti">'+SH.esc(w.workTitle)+'</span>'
       +'<span class="wh">'+SH.esc(w.nameKo)+' · '+SH.esc(w.contribution)+'</span></span></a></li>';}).join('')
     +'</ul>';
   panel.hidden=false;
 }

 document.getElementById('btn-all').addEventListener('click',function(e){
   e.preventDefault(); SH.ss('field',null); location.href='timeline.html?field=';
 });

 // 밀도 그래프 (적층 막대, 25년 구간)
 (function(){
   var host=document.getElementById('density');
   var bins=[],start=1650;
   for(var y=start;y<2025;y+=25) bins.push({y0:y,y1:y+25,v:{}});
   D.works.forEach(function(w){
     var b=bins[Math.floor((w.year-start)/25)]; if(b) b.v[w.field]=(b.v[w.field]||0)+1;});
   var max=Math.max.apply(null,bins.map(function(b){
     return D.fields.reduce(function(s,f){return s+(b.v[f.key]||0);},0);}));
   var W=920,H=190,padB=26,padT=8,bw=W/bins.length;
   var svg='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="'+H+'" role="img" aria-label="25년 구간별 분야별 저작 수 막대그래프">';
   bins.forEach(function(b,i){
     var yy=H-padB, x=i*bw+3, w=bw-6;
     D.fields.forEach(function(f){
       var c=b.v[f.key]||0; if(!c)return;
       var h=(c/max)*(H-padB-padT);
       yy-=h;
       svg+='<rect x="'+x+'" y="'+yy+'" width="'+w+'" height="'+h+'" fill="var(--f-'+f.slug+')" opacity=".88"><title>'
         +b.y0+'–'+(b.y1-1)+' '+f.key+' '+c+'편</title></rect>';
     });
     if(i%2===0) svg+='<text x="'+(x+w/2)+'" y="'+(H-8)+'" text-anchor="middle" font-size="11" fill="var(--ink-soft)">'+b.y0+'</text>';
   });
   svg+='</svg><p class="small muted" style="margin:8px 0 0;display:flex;gap:12px;flex-wrap:wrap">'
     +D.fields.map(function(f){return '<span class="chip f-'+f.slug+' '+({prob:'',infer:'sq',bayes:'tri',applied:'dia',ds:'hex'}[f.slug])+'">'+f.key+'</span>';}).join('')+'</p>';
   host.innerHTML=svg;
 })();
})();
</script>"""
    return shell("통계학의 역사 — 확률에서 데이터과학까지",
                 f"1654년부터 2015년까지 {N}편의 논문과 저서로 따라가는 통계학의 역사. 분야를 골라 타임라인과 이야기로 탐색하세요.",
                 body, 0, script)


# ══════════════════════════════════════════════════════════ timeline
def page_timeline():
    body = """<div class="wrap">
  <h1>타임라인</h1>
  <p class="muted" style="max-width:64ch;margin-top:-4px">분야별 다섯 개 줄 위에 저작을 연도순으로 놓았습니다.
  점을 누르면 상세가 열리고, 휠이나 ＋/－ 로 확대하면 더 많은 이름이 나타납니다.</p>
  <div class="tl-toolbar" id="tl-toolbar"></div>
  <div class="tl-stage" id="tl-stage"></div>
  <div id="tl-empty" class="empty-state" hidden>
    조건에 맞는 저작이 없습니다. 검색어를 지우거나 분야를 다시 켜 보세요.
  </div>
  <p class="small muted" style="margin-top:14px">
    가로축은 기본적으로 구간별 가변 축입니다 — 저작이 희박한 18세기와 밀집한 20세기를 함께 보기 위해서입니다.
    실제 연도 간격이 필요하면 「실제 연도 비례」를 누르세요.
    키보드로는 Tab 으로 점 사이를 이동하고 ←→ 로 같은 줄, ↑↓ 로 다른 줄로 옮깁니다.
  </p>
</div>"""
    return shell("타임라인 — 통계학의 역사",
                 "1654~2015년 통계학 주요 저작을 분야별 다섯 줄로 배치한 인터랙티브 연대표.",
                 body, 0, '<script src="assets/timeline.js"></script>')


# ══════════════════════════════════════════════════════════ story index
def page_story_index():
    cards = ""
    for c in CHAPMETA:
        n = c["n"]
        cnt = sum(1 for w in WORKS if w["chapter"] == n)
        s = CHAPTERS[n]["summary"]
        cards += f"""
    <a class="card" href="{c['file']}" data-chapter="{n}" style="text-decoration:none;color:inherit;display:block">
      <p class="small muted" style="margin:0 0 4px">{n}장 · {esc(c['spanLabel'])} · 약 {c['minutes']}분</p>
      <h3 style="margin:0 0 6px">{esc(c['title'])}</h3>
      <p class="small" style="margin:0;color:var(--ink-mid)">{esc(s['한 문장 결론'])}</p>
      <p class="small muted" style="margin:10px 0 0">연결된 저작 {cnt}편<span data-rec hidden></span></p>
    </a>"""

    summary_rows = ""
    for c in CHAPMETA:
        s = CHAPTERS[c["n"]]["summary"]
        summary_rows += f"""<div style="padding:14px 0;border-bottom:1px solid var(--line)">
      <p class="small muted" style="margin:0 0 3px">{c['n']}장 · {esc(c['spanLabel'])}</p>
      <p style="margin:0 0 4px;font-weight:700">{esc(c['title'])}</p>
      <p style="margin:0;color:var(--ink-mid)">{esc(s['한 문장 결론'])}</p></div>"""

    body = f"""<div class="wrap">
  <h1>이야기</h1>
  <p class="lede" style="max-width:60ch">고대의 인구조사부터 딥러닝까지, 여덟 개 장으로 나누어 읽습니다.
  각 장은 4~7분 분량이고 전공 수준의 내용은 접어 두었습니다.</p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 30px">
    <a class="btn btn-primary" href="00-prehistory.html">처음부터 읽기</a>
    <button class="btn" id="btn-summary" aria-expanded="false">요약만 훑기</button>
  </div>
  <section id="summary-mode" hidden class="card" style="margin-bottom:30px">
    <h2 style="margin-top:0;font-size:18px">여덟 장 요약</h2>{summary_rows}
  </section>
  <div class="grid grid-2">{cards}
  </div>
</div>"""
    script = """<script>
(function(){
 var SH=window.SH;
 var btn=document.getElementById('btn-summary'), box=document.getElementById('summary-mode');
 btn.addEventListener('click',function(){
   var on=box.hidden; box.hidden=!on; btn.setAttribute('aria-expanded',on?'true':'false');
   btn.textContent=on?'요약 접기':'요약만 훑기';
 });
 if(SH.state.field){
   var f=SH.fieldByKey[SH.state.field];
   document.querySelectorAll('[data-chapter]').forEach(function(card){
     var n=parseInt(card.getAttribute('data-chapter'),10);
     if(f.chapters.indexOf(n)>=0){
       var tag=card.querySelector('[data-rec]');
       tag.hidden=false;
       tag.innerHTML=' · <b style="color:var(--f-'+f.slug+')">'+SH.esc(f.key)+' 추천</b>';
       card.style.borderColor='var(--f-'+f.slug+')';
     }
   });
 }
})();
</script>"""
    return shell("이야기 — 통계학의 역사",
                 "통계학 370년을 여덟 개 장으로 나눈 읽기. 각 장 4~7분.",
                 body, 1, script)


# ══════════════════════════════════════════════════════════ 장 페이지
def page_chapter(n):
    c = next(x for x in CHAPMETA if x["n"] == n)
    ch = CHAPTERS[n]
    prev_c = next((x for x in CHAPMETA if x["n"] == n - 1), None)
    next_c = next((x for x in CHAPMETA if x["n"] == n + 1), None)
    cnt = sum(1 for w in WORKS if w["chapter"] == n)

    dots = "".join(f'<i class="{"on" if i <= n else ""}"></i>' for i in range(len(CHAPMETA)))
    s = ch["summary"]
    sum_html = "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in s.items())

    sections, toc = "", ""
    for i, (head, paras) in enumerate(ch["body"]):
        sid = f"s{i+1}"
        toc += f'<li><a href="#{sid}">{esc(head)}</a></li>'
        sections += f'<h2 id="{sid}">{esc(head)}</h2>\n'
        sections += "".join(f"<p>{p}</p>\n" for p in paras)

    deep = ""
    for title, paras in ch.get("deep", []):
        deep_body = "".join(f"<p>{p}</p>" for p in paras)
        deep += f'<details class="deep"><summary>{esc(title)}</summary><div>{deep_body}</div></details>\n'
    # 심화 블록은 본문 뒤, 핵심 정리 앞에 배치
    take = "".join(f"<li>{esc(t)}</li>" for t in ch["takeaways"])
    fns = ch.get("footnotes", [])
    fn_html = ""
    if fns:
        fn_html = ('<div class="footnotes"><ol>' +
                   "".join(f"<li>{esc(f)}</li>" for f in fns) + "</ol></div>")

    works_block = ""
    if cnt:
        works_block = f"""
  <h2 id="works">이 장의 저작 <span data-chapter-works-count>{cnt}</span>편</h2>
  <p class="small muted" style="margin-top:-6px">항목을 누르면 타임라인에서 상세가 열립니다.
  분야를 선택해 두면 그 분야가 먼저 표시됩니다.</p>
  <ul class="work-list" data-chapter-works="{n}"></ul>"""
    elif n == 0:
        rows = "".join(
            f'<li><a class="work-item" href="#" onclick="return false" style="cursor:default">'
            f'<span class="yr" style="font-size:13px">{esc(p["yearDisplay"])}</span>'
            f'<span><span class="ti">{esc(p["title"])}</span>'
            f'<span class="de">{esc(p["desc"])}</span>'
            f'<span class="wh">{esc(p["who"])}</span></span></a></li>' for p in PRE)
        works_block = f"""
  <h2 id="works">이 장의 항목 {len(PRE)}건</h2>
  <p class="small muted" style="margin-top:-6px">전사(前史) 항목은 첨부 데이터에 없으며 Wikipedia 『History of statistics』에 근거합니다.</p>
  <ul class="work-list">{rows}</ul>"""
    else:
        works_block = """
  <h2 id="works">이 장의 저작</h2>
  <p class="muted">이 장은 전망을 다루므로 연결된 저작 항목이 없습니다.</p>"""

    teaser = f'<p class="next-teaser">{esc(ch["teaser"])}</p>' if ch.get("teaser") else ""

    nav = '<div class="chapter-nav">'
    nav += (f'<a href="{prev_c["file"]}">← {prev_c["n"]}장 {esc(prev_c["title"])}</a>'
            if prev_c else '<a href="index.html">← 목차</a>')
    nav += '<a href="index.html">목차</a>'
    nav += (f'<a href="{next_c["file"]}">{next_c["n"]}장 {esc(next_c["title"])} →</a>'
            if next_c else '<a href="../appendix.html">부록 →</a>')
    nav += "</div>"

    body = f"""<div class="progress-bar" data-progress></div>
<div class="wrap">
 <div class="story-layout">
  <article class="prose">
    <div class="chapter-meta">
      <span class="chapter-dots" aria-hidden="true">{dots}</span>
      <span>{n}장 / 전체 {len(CHAPMETA)}장</span>
      <span>{esc(c['spanLabel'])}</span>
      <span>약 {c['minutes']}분</span>
    </div>
    <h1>{esc(c['title'])}</h1>
    <div class="summary-box"><dl>{sum_html}</dl></div>
{sections}
{deep}
    <div class="takeaways"><h2 style="margin-top:0">핵심 정리</h2><ol>{take}</ol></div>
{works_block}
{fn_html}
{teaser}
{nav}
  </article>
  <nav class="toc" aria-label="이 장의 목차">
    <p class="toc-title">이 장의 차례</p>
    <ul>{toc}<li><a href="#works">이 장의 저작</a></li></ul>
  </nav>
 </div>
</div>"""
    return shell(f"{n}장 {c['title']} — 통계학의 역사",
                 esc(s["한 문장 결론"]), body, 1)


# ══════════════════════════════════════════════════════════ works
def page_works():
    body = """<div class="wrap">
  <h1>저작 데이터베이스</h1>
  <p class="muted" style="max-width:64ch;margin-top:-4px">전체 목록입니다. 머리글을 눌러 정렬하고, 행을 눌러 상세를 엽니다.</p>
  <div class="tl-toolbar" id="w-toolbar"></div>
  <div class="table-scroll">
    <table class="data" id="w-table">
      <thead><tr>
        <th data-sort="year" aria-sort="ascending" scope="col">연도</th>
        <th data-sort="field" scope="col">분야</th>
        <th data-sort="nameKo" scope="col">인물</th>
        <th data-sort="workTitle" scope="col">저작</th>
        <th scope="col">요약</th>
        <th scope="col">링크</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>
  <div id="w-empty" class="empty-state" hidden>조건에 맞는 저작이 없습니다.</div>
</div>"""
    script = """<script>
(function(){
 var SH=window.SH,D=SH.data;
 var qs=new URLSearchParams(location.search);
 var st={q:qs.get('q')||'',sort:qs.get('sort')||'year',dir:1,active:{}};
 D.fields.forEach(function(f){st.active[f.key]=!SH.state.field||SH.state.field===f.key;});

 var bar=document.getElementById('w-toolbar');
 bar.innerHTML=D.fields.map(function(f){
   return '<button class="filter-btn f-'+f.slug+'" data-field="'+SH.esc(f.key)+'" aria-pressed="'
     +(st.active[f.key]?'true':'false')+'">'+SH.esc(f.key)+'</button>';}).join('')
   +'<button class="btn btn-sm" data-all>전체</button>'
   +'<input class="search-box" type="search" placeholder="인물·저작·키워드 검색" aria-label="검색" value="'+SH.esc(st.q)+'">'
   +'<button class="btn btn-sm" data-csv>CSV 내려받기</button>'
   +'<span class="tl-count" id="w-count"></span>';

 function rows(){
   return D.works.filter(function(w){return st.active[w.field]&&SH.matches(w,st.q);})
     .sort(function(a,b){
       var k=st.sort,av=a[k],bv=b[k];
       if(k==='year') return (av-bv)*st.dir;
       return String(av).localeCompare(String(bv),'ko')*st.dir;
     });
 }
 function render(){
   var list=rows(),tb=document.querySelector('#w-table tbody');
   tb.innerHTML=list.map(function(w){
     var links=[];
     if(w.sourceUrl) links.push('<a href="'+SH.esc(w.sourceUrl)+'" target="_blank" rel="noopener" data-nodecorate>원문↗</a>');
     if(w.wikiUrl) links.push('<a href="'+SH.esc(w.wikiUrl)+'" target="_blank" rel="noopener" data-nodecorate>위키↗</a>');
     return '<tr data-id="'+SH.esc(w.id)+'" tabindex="0"><td class="yr">'+w.year+'</td><td>'+SH.chipHTML(w.field)
       +'</td><td>'+SH.esc(w.nameKo)+'<br><span class="small muted">'+SH.esc(w.nameEn)+'</span></td><td><b>'
       +SH.esc(w.workTitle)+'</b></td><td class="small">'+SH.esc(w.workDesc)+'</td><td class="small">'
       +links.join(' ')+'</td></tr>';}).join('');
   document.getElementById('w-count').textContent=list.length+'편 / 전체 '+D.works.length+'편';
   document.getElementById('w-empty').hidden=list.length>0;
   tb.querySelectorAll('tr').forEach(function(tr){
     function open(){SH.openDetail(SH.byId(tr.getAttribute('data-id')));}
     tr.addEventListener('click',function(e){if(!e.target.closest('a'))open();});
     tr.addEventListener('keydown',function(e){if(e.key==='Enter')open();});
   });
 }
 bar.querySelectorAll('[data-field]').forEach(function(b){
   b.addEventListener('click',function(){
     var f=b.getAttribute('data-field'); st.active[f]=!st.active[f];
     b.setAttribute('aria-pressed',st.active[f]?'true':'false'); render();});
 });
 bar.querySelector('[data-all]').addEventListener('click',function(){
   D.fields.forEach(function(f){st.active[f.key]=true;});
   bar.querySelectorAll('[data-field]').forEach(function(b){b.setAttribute('aria-pressed','true');});
   render();});
 var s=bar.querySelector('.search-box'),t;
 s.addEventListener('input',function(){clearTimeout(t);t=setTimeout(function(){st.q=s.value.trim();render();},160);});
 document.querySelectorAll('#w-table th[data-sort]').forEach(function(th){
   th.addEventListener('click',function(){
     var k=th.getAttribute('data-sort');
     st.dir=(st.sort===k)?-st.dir:1; st.sort=k;
     document.querySelectorAll('#w-table th').forEach(function(o){o.removeAttribute('aria-sort');});
     th.setAttribute('aria-sort',st.dir>0?'ascending':'descending');
     render();});
 });
 bar.querySelector('[data-csv]').addEventListener('click',function(){
   var cols=['year','field','nameKo','nameEn','workTitle','workDesc','contribution','sourceUrl','wikiUrl'];
   var head=['연도','분야','한글 이름','영문 이름','저작명','저작 설명','핵심 기여','원문 URL','위키백과 URL'];
   function q(v){return '"'+String(v==null?'':v).replace(/"/g,'""')+'"';}
   var csv='\\uFEFF'+head.map(q).join(',')+'\\n'
     +rows().map(function(w){return cols.map(function(c){return q(w[c]);}).join(',');}).join('\\n');
   var a=document.createElement('a');
   a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
   a.download='statistics-history-works.csv'; a.click(); URL.revokeObjectURL(a.href);
 });
 render();
 if(qs.get('id')&&SH.byId(qs.get('id'))) SH.openDetail(SH.byId(qs.get('id')),{silent:true});
})();
</script>"""
    return shell("저작 데이터베이스 — 통계학의 역사",
                 f"통계학사 주요 저작 {N}편 전체 목록. 분야·인물·연도로 검색하고 CSV로 내려받으세요.",
                 body, 0, script)


# ══════════════════════════════════════════════════════════ people
def page_people():
    body = """<div class="wrap">
  <h1>인물 색인</h1>
  <p class="muted" style="max-width:64ch;margin-top:-4px">공저 항목은 원본 표기를 그대로 두었습니다.
  검색에서는 개별 이름으로도 찾을 수 있습니다.</p>
  <div class="tl-toolbar" id="p-toolbar"></div>
  <div id="p-list" class="grid grid-3"></div>
  <div id="p-empty" class="empty-state" hidden>조건에 맞는 인물이 없습니다.</div>
</div>"""
    script = """<script>
(function(){
 var SH=window.SH,D=SH.data,st={q:'',sort:'year'};
 var bar=document.getElementById('p-toolbar');
 bar.innerHTML='<button class="btn btn-sm" data-sort="year" aria-pressed="true">연도순</button>'
  +'<button class="btn btn-sm" data-sort="name" aria-pressed="false">가나다순</button>'
  +'<input class="search-box" type="search" placeholder="이름 검색" aria-label="인물 검색">'
  +'<span class="tl-count" id="p-count"></span>';
 function render(){
   var list=D.people.filter(function(p){
     if(!st.q) return true;
     var t=(p.nameKo+' '+p.nameEn).toLowerCase();
     return t.indexOf(st.q.toLowerCase())>=0;
   });
   if(SH.state.field) list=list.filter(function(p){return p.fields.indexOf(SH.state.field)>=0;});
   list=list.slice().sort(function(a,b){
     return st.sort==='year' ? (a.from-b.from)||a.nameEn.localeCompare(b.nameEn)
                             : a.nameKo.localeCompare(b.nameKo,'ko');});
   document.getElementById('p-list').innerHTML=list.map(function(p){
     var chips=p.fields.map(function(f){return SH.chipHTML(f);}).join(' ');
     var span=p.from===p.to?p.from:(p.from+'–'+p.to);
     return '<div class="card"><p style="margin:0 0 2px;font-weight:700">'+SH.esc(p.nameKo)+'</p>'
      +'<p class="small muted" style="margin:0 0 8px">'+SH.esc(p.nameEn)+'</p>'
      +'<p style="margin:0 0 8px">'+chips+'</p>'
      +'<p class="small muted" style="margin:0">'+span+' · 저작 '+p.count+'편</p>'
      +'<p style="margin:10px 0 0"><a class="btn btn-sm" href="timeline.html?id='+encodeURIComponent(p.works[0])+'">타임라인에서 보기 →</a></p></div>';
   }).join('');
   document.getElementById('p-count').textContent=list.length+'명 / 전체 '+D.people.length+'명';
   document.getElementById('p-empty').hidden=list.length>0;
 }
 bar.querySelectorAll('[data-sort]').forEach(function(b){
   b.addEventListener('click',function(){
     st.sort=b.getAttribute('data-sort');
     bar.querySelectorAll('[data-sort]').forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false');});
     render();});
 });
 var s=bar.querySelector('.search-box'),t;
 s.addEventListener('input',function(){clearTimeout(t);t=setTimeout(function(){st.q=s.value.trim();render();},150);});
 render();
})();
</script>"""
    return shell("인물 색인 — 통계학의 역사",
                 f"통계학사에 등장하는 인물·연구팀 {len(PEOPLE)}종의 색인.", body, 0, script)


# ══════════════════════════════════════════════════════════ appendix
GLOSSARY = [
    ("가능도 (尤度, likelihood)", "자료를 고정하고 모수를 변수로 보았을 때의 함수. 확률과 같은 식을 반대 방향에서 읽는다. 문헌에 따라 '우도'로도 표기하며, 이 사이트는 '가능도'로 통일한다."),
    ("최대가능도추정법 (MLE)", "관측된 자료가 가장 그럴듯해지도록 모수를 정하는 추정 방법. 피셔가 1922년 체계화했다."),
    ("부분가능도 (partial likelihood)", "전체 가능도 가운데 관심 모수에 관한 부분만 떼어내 추론하는 방법. 콕스 비례위험모형의 핵심 도구다."),
    ("대수의 법칙", "시행을 충분히 반복하면 관측된 상대빈도가 참된 확률에 가까워진다는 정리. 베르누이(1713)."),
    ("중심극한정리", "독립적인 확률변수의 합이 개별 분포와 무관하게 정규분포에 가까워진다는 정리. 라플라스(1812)."),
    ("정규분포", "종 모양의 연속분포. 드무아브르가 이항분포의 근사로 발견하고 가우스가 오차법칙으로 채택했다."),
    ("최소제곱법", "관측과 모형의 차이를 제곱해 더한 값을 최소화하는 추정법. 르장드르(1805)·가우스(1809)."),
    ("회귀", "한 변수로 다른 변수를 설명·예측하는 관계의 추정. 골턴의 '평균으로의 회귀' 관찰에서 이름이 유래했다."),
    ("상관계수", "두 변수가 함께 움직이는 정도를 −1에서 1 사이 값으로 나타낸 척도. 칼 피어슨이 정식화했다."),
    ("중앙값", "자료를 크기순으로 늘어놓았을 때 한가운데 오는 값. 극단값에 덜 흔들린다."),
    ("최빈값", "자료에서 가장 자주 나타나는 값."),
    ("분산분석 (ANOVA)", "전체 변동을 요인별 변동으로 분해해 집단 간 차이를 검정하는 방법. 피셔."),
    ("유의수준", "귀무가설이 참인데도 기각할 확률의 상한. 피셔가 편의적으로 언급한 5%가 관례로 굳었다."),
    ("p-값", "귀무가설이 참일 때 관측된 것만큼 극단적인 결과가 나올 확률."),
    ("검정력", "대립가설이 참일 때 귀무가설을 올바르게 기각할 확률. 네이만-피어슨 이론의 중심 개념."),
    ("신뢰구간", "반복 표집에서 정해진 비율만큼 참값을 포함하도록 구성한 구간. 네이만(1937)."),
    ("충분통계량", "자료가 가진 모수에 관한 정보를 남김없이 담고 있는 통계량."),
    ("사전분포 / 사후분포", "자료를 보기 전 모수에 대한 믿음의 분포와, 자료를 반영해 갱신한 분포. 베이즈 추론의 두 축."),
    ("베이즈 인자", "두 가설의 상대적 지지도를 비교하는 양. 제프리스가 체계화했다."),
    ("MCMC", "마르코프 연쇄를 설계해 목표 분포에서 표본을 뽑는 계산 기법. 베이즈 추론의 계산 병목을 풀었다."),
    ("비모수 방법", "분포의 형태를 특정하지 않고 추론하는 방법. 순위 기반 검정과 카플란-마이어 추정량이 대표적이다."),
    ("중도절단 (censoring)", "관측이 끝나기 전에 연구가 종료되어 정확한 값을 모르는 상태. 생존분석의 기본 상황."),
    ("부트스트랩", "관측 표본에서 복원추출을 반복해 추정량의 분포를 경험적으로 구하는 방법. 에프론(1979)."),
    ("정규화 (regularization)", "모형의 복잡도에 벌점을 주어 과적합을 막는 기법. 릿지·라쏘가 대표적이다."),
    ("희소성 (sparsity)", "많은 계수가 0이라는 가정. 고차원 자료에서 추정을 가능하게 하는 핵심 구조."),
    ("과적합", "훈련 자료에는 잘 맞지만 새 자료에는 성능이 떨어지는 상태."),
    ("앙상블", "여러 모형의 예측을 결합해 성능을 높이는 방법. 배깅·랜덤 포레스트·부스팅."),
    ("생존 편향", "살아남은 사례만 관찰해 잘못된 결론을 내리는 편향. 왈드의 폭격기 분석이 고전적 사례다."),
]


def page_appendix():
    gl = "".join(f"<div><dt>{esc(t)}</dt><dd>{esc(d)}</dd></div>" for t, d in GLOSSARY)

    subst_rows = [
        ("1922", "Ronald A. Fisher (수리적 기초)", "우도 · 최대우도법", "가능도 · 최대가능도법"),
        ("1922", "Ronald A. Fisher (분할표 χ²)", "최대우도법", "최대가능도법"),
        ("1925", "Ronald A. Fisher (SMRW)", "최대우도법", "최대가능도법"),
        ("1935", "Ronald A. Fisher (실험계획)", "최대우도법", "최대가능도법"),
        ("1936", "Ronald A. Fisher (판별분석)", "최대우도법", "최대가능도법"),
        ("1946", "Harald Cramér", "최대우도추정", "최대가능도추정"),
        ("1972", "David Cox", "부분우도 · 편우도", "부분가능도 · 편가능도"),
        ("1976", "Donald B. Rubin", "우도", "가능도"),
        ("1998", "Aad van der Vaart", "최대우도추정량", "최대가능도추정량"),
    ]
    srows = "".join(f"<tr><td class='yr'>{y}</td><td>{esc(w)}</td><td class='small muted'>{esc(a)}</td>"
                    f"<td class='small'><b>{esc(b)}</b></td></tr>" for y, w, a, b in subst_rows)

    cnt = counts_by_field()
    crows = "".join(
        f"<tr><td>{esc(f['key'])}</td><td class='yr'>{cnt[f['key']]}</td>"
        f"<td class='yr'>{cnt[f['key']]/N*100:.1f}%</td>"
        f"<td class='yr'>{span_by_field()[f['key']][0]} ~ {span_by_field()[f['key']][1]}</td></tr>"
        for f in FIELDS)

    body = f"""<div class="wrap">
  <h1>부록</h1>

  <section class="prose" style="max-width:none">
    <h2 id="glossary">용어집</h2>
    <p class="muted small" style="margin-top:-6px">본문에서 점선 밑줄이 그어진 용어를 여기서 설명합니다.</p>
    <dl class="glossary" style="max-width:70ch">{gl}</dl>
  </section>

  <section style="margin-top:56px">
    <h2 id="data">데이터</h2>
    <div class="table-scroll" style="max-width:640px">
      <table class="data">
        <thead><tr><th>분야</th><th>저작 수</th><th>비율</th><th>연도 범위</th></tr></thead>
        <tbody>{crows}
          <tr><td><b>합계</b></td><td class="yr"><b>{N}</b></td><td class="yr">100%</td>
          <td class="yr">1654 ~ 2015</td></tr>
        </tbody>
      </table>
    </div>
    <p class="small muted" style="margin-top:10px">위 수치는 원본 요약 시트의 값을 쓰지 않고 실제 데이터에서 그때그때 집계한 것입니다.</p>
    <p style="margin-top:14px"><a class="btn btn-sm" href="works.html">저작 데이터베이스에서 CSV 내려받기 →</a></p>
  </section>

  <section style="margin-top:56px" class="prose" style="max-width:none">
    <h2 id="terms">용어 치환 대조표</h2>
    <p class="muted" style="margin-top:-6px;max-width:64ch">이 사이트는 likelihood 계열 용어를 '가능도'로 통일합니다.
    원본 자료 파일은 수정하지 않았으며, 데이터 생성 단계에서 아래와 같이 치환했습니다.</p>
    <div class="table-scroll" style="max-width:760px">
      <table class="data">
        <thead><tr><th>연도</th><th>항목</th><th>원본 표기</th><th>사이트 표기</th></tr></thead>
        <tbody>{srows}</tbody>
      </table>
    </div>
  </section>

  <section style="margin-top:56px" class="prose">
    <h2 id="notes">제작 노트</h2>
    <h3>데이터 검증에서 확인한 것</h3>
    <ol>
      <li><b>항목 수</b> — 원본 타임라인 시트의 데이터는 4행이 머리글, 5행부터 본문이며 총 <b>{N}건</b>입니다.
      요약 시트에 적힌 86편과 일치합니다.</li>
      <li><b>요약 시트 공란</b> — 원본 요약 시트의 '항목 수'·'비율' 열이 비어 있어, 이 사이트는 모든 집계를 데이터에서 직접 계산합니다.</li>
      <li><b>전사(前史)</b> — 0장의 9개 항목은 첨부 데이터에 없으며 Wikipedia 『History of statistics』에 근거합니다.</li>
      <li><b>원문 링크</b> — 서지·원문 URL은 {sum(1 for w in WORKS if w['sourceUrl'])}건에만 있습니다.
      없는 항목은 빈 버튼을 만들지 않고 위키백과 링크만 노출합니다.</li>
      <li><b>위키백과 링크 대상</b> — 일부 항목은 저작이 아니라 인물 문서로 연결됩니다.
      그래서 링크 라벨을 '위키백과: 인물/주제'로 일반화했습니다.</li>
      <li><b>동일 인물 복수 저작</b> — {sum(1 for p in PEOPLE if p['count'] > 1)}명이 2편 이상을 남겼습니다.
      원본의 '핵심 내용' 열은 인물 단위로 중복되므로, 상세 패널에서는 저작 설명을 주로, 인물 기여를 부로 배치했습니다.</li>
      <li><b>분야 경계</b> — 1965년 FFT나 2012년 AlexNet의 '데이터과학' 분류처럼 경계가 모호한 항목이 있습니다.
      원본 분류를 바꾸지 않고, 6장 본문에서 경계의 모호함 자체를 다룹니다.</li>
      <li><b>대표성</b> — 데이터에 등장하는 여성 연구자는 나이팅게일과 코르테스 둘뿐입니다.
      3장과 7장에서 이 한계를 명시했습니다.</li>
      <li><b>연도 기준</b> — 모두 출판 연도입니다. 베르누이(1713)와 베이즈(1763)는 사후 출판입니다.</li>
    </ol>

    <h3>서술 원칙</h3>
    <ul>
      <li>우선권 논쟁(르장드르/가우스, 피셔/네이만)은 어느 한쪽 편을 들지 않고 양측 입장을 함께 적었습니다.</li>
      <li>골턴·칼 피어슨·피셔의 우생학 관여는 사실만 명시하고 평가는 독자에게 맡겼습니다.</li>
      <li>서사는 Wikipedia 『History of statistics』의 서술 범위를 벗어나지 않도록 했습니다.</li>
    </ul>

    <h2 id="sources" style="margin-top:44px">출처</h2>
    <ul>
      <li><b>저작 데이터</b> — 「통계학의 역사를 바꾼 인물 및 주요 저작 타임라인 (1654~2015)」 자료집.
      연도·분야·인물·저작명·설명·원문 URL·위키백과 URL의 9개 항목으로 구성된 {N}건.</li>
      <li><b>서사 및 전사</b> — Wikipedia,
      <a href="https://en.wikipedia.org/wiki/History_of_statistics" target="_blank" rel="noopener" data-nodecorate>History of statistics</a>
      (2026년 9월 12일 열람). 이 문서의 내용은 CC BY-SA 4.0 라이선스로 제공되며, 이를 참고한 서술 부분에도 동일 조건이 적용됩니다.</li>
      <li>각 저작의 원문 및 위키백과 링크는 상세 패널과 저작 데이터베이스에 개별 표시했습니다.</li>
    </ul>

    <h2 id="tech" style="margin-top:44px">기술 사양</h2>
    <ul>
      <li>빌드 도구 없는 정적 사이트. 외부 CDN·웹폰트·이미지 요청이 없어 오프라인에서도 완전히 동작합니다.</li>
      <li>데이터는 <code>assets/data.js</code>의 전역 변수로 제공됩니다.
      <code>file://</code>로 직접 열 때 <code>fetch</code>가 차단되기 때문입니다.</li>
      <li>선택한 분야는 쿼리스트링(<code>?field=</code>)으로 전파됩니다.
      세션 저장소는 보조 수단이며 없어도 모든 기능이 동작합니다.</li>
      <li>타임라인은 외부 라이브러리 없이 SVG를 직접 그립니다.</li>
    </ul>
  </section>
</div>"""
    return shell("부록 — 통계학의 역사", "용어집, 데이터 집계, 용어 치환 대조표, 제작 노트와 출처.", body, 0)


def main():
    written = []
    written.append(write("index.html", page_index()))
    written.append(write("timeline.html", page_timeline()))
    written.append(write("works.html", page_works()))
    written.append(write("people.html", page_people()))
    written.append(write("appendix.html", page_appendix()))
    written.append(write("story/index.html", page_story_index()))
    for c in CHAPMETA:
        written.append(write("story/" + c["file"], page_chapter(c["n"])))
    for p in written:
        print(os.path.relpath(p, ROOT), os.path.getsize(p))
    print("total pages:", len(written))


if __name__ == "__main__":
    main()
