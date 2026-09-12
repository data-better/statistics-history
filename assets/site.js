/* 통계학의 역사 — 공통 스크립트 (PRD v2 §7.3)
   · 쿼리스트링이 상태의 정본. sessionStorage는 보조이며 실패해도 사이트는 완전히 동작한다.
   · 내부 링크에는 클릭 위임으로 현재 파라미터를 덧붙인다. */
(function () {
  "use strict";

  var D = window.__STATHIST__ || { works: [], fields: [], chapters: [], people: [], prehistory: [] };
  var FIELD_BY_KEY = {};
  D.fields.forEach(function (f) { FIELD_BY_KEY[f.key] = f; });
  var VALID = D.fields.map(function (f) { return f.key; });
  var PARAMS = ["field", "id", "y", "q", "sort", "theme"];

  /* ── 세션 보조 기억 (실패해도 무시) ───────────────── */
  function ss(key, val) {
    try {
      if (val === undefined) return window.sessionStorage.getItem(key);
      if (val === null) window.sessionStorage.removeItem(key);
      else window.sessionStorage.setItem(key, val);
    } catch (e) { /* 사생활 보호 모드 등 — 무시 */ }
    return null;
  }

  /* ── 현재 상태 ──────────────────────────────────── */
  var qs = new URLSearchParams(location.search);
  var rawField = qs.get("field");
  var field = VALID.indexOf(rawField) >= 0 ? rawField : null;   // 잘못된 값은 조용히 전체 보기
  if (!field && !qs.has("field")) {
    var remembered = ss("field");
    if (VALID.indexOf(remembered) >= 0) field = remembered;
  }
  if (field) ss("field", field); else if (qs.has("field")) ss("field", null);

  var state = {
    field: field,
    q: qs.get("q") || "",
    id: qs.get("id") || "",
    y: qs.get("y") || "",
    sort: qs.get("sort") || ""
  };

  /* ── 경로 보정 (페이지가 story/ 하위에 있을 수 있음) ─ */
  var depth = (location.pathname.indexOf("/story/") >= 0) ? "../" : "";
  function rel(p) { return depth + p; }

  /* ── 링크 파라미터 전파 ──────────────────────────── */
  function decorate(href) {
    if (!href) return href;
    if (/^(https?:|mailto:|tel:|#|javascript:)/i.test(href)) return href;
    var hash = "", q = "";
    var h = href.indexOf("#");
    if (h >= 0) { hash = href.slice(h); href = href.slice(0, h); }
    var qm = href.indexOf("?");
    if (qm >= 0) { q = href.slice(qm + 1); href = href.slice(0, qm); }
    var p = new URLSearchParams(q);
    if (state.field && !p.has("field")) p.set("field", state.field);
    var theme = qs.get("theme");
    if (theme && !p.has("theme")) p.set("theme", theme);
    var s = p.toString();
    return href + (s ? "?" + s : "") + hash;
  }

  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a[href]");
    if (!a || a.target === "_blank" || a.hasAttribute("data-nodecorate")) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
    var href = a.getAttribute("href");
    var next = decorate(href);
    if (next !== href) { ev.preventDefault(); location.href = next; }
  });

  /* ── 테마 ───────────────────────────────────────── */
  var themeParam = qs.get("theme");
  if (themeParam !== "dark" && themeParam !== "light") themeParam = ss("theme");
  if (themeParam === "dark" || themeParam === "light") {
    document.documentElement.setAttribute("data-theme", themeParam);
  }
  function toggleTheme() {
    var cur = document.documentElement.getAttribute("data-theme");
    var next = cur === "dark" ? "light" : (cur === "light" ? "dark" :
      (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "light" : "dark"));
    document.documentElement.setAttribute("data-theme", next);
    ss("theme", next);
  }

  /* ── 헤더 조립 ──────────────────────────────────── */
  var NAV = [
    { href: "index.html", label: "처음" },
    { href: "timeline.html", label: "타임라인" },
    { href: "story/index.html", label: "이야기" },
    { href: "works.html", label: "저작" },
    { href: "people.html", label: "인물" },
    { href: "appendix.html", label: "부록" }
  ];

  function currentPage() {
    var p = location.pathname.split("/").pop() || "index.html";
    if (location.pathname.indexOf("/story/") >= 0) return "story/index.html";
    return p;
  }

  function buildHeader() {
    var host = document.querySelector("[data-header]");
    if (!host) return;
    var cur = currentPage();
    var html = '<a class="skip" href="#main">본문으로 건너뛰기</a><div class="header-in">' +
      '<a class="brand" href="' + rel("index.html") + '">통계학의 역사 <span>1654–2015</span></a>' +
      '<nav class="site-nav" aria-label="주요 메뉴">';
    NAV.forEach(function (n) {
      var isCur = (n.href === cur) || (cur === "index.html" && n.href === "index.html");
      html += '<a href="' + rel(n.href) + '"' + (isCur ? ' aria-current="page"' : "") + '>' + n.label + "</a>";
    });
    html += "</nav>" + fieldBadgeHTML() +
      '<button class="icon-btn" data-theme-toggle aria-label="밝은 화면과 어두운 화면 전환">◐</button></div>';
    host.className = "site-header";
    host.innerHTML = html;
    var tb = host.querySelector("[data-theme-toggle]");
    if (tb) tb.addEventListener("click", toggleTheme);
    var clear = host.querySelector("[data-field-clear]");
    if (clear) clear.addEventListener("click", function (e) { e.stopPropagation(); setField(null); });
    var badge = host.querySelector("[data-field-badge]");
    if (badge) badge.addEventListener("click", function () { location.href = rel("index.html") + "#fields"; });
  }

  function fieldBadgeHTML() {
    if (!state.field) {
      return '<button class="field-badge" data-field-badge title="관심 분야를 고르면 사이트 전체가 그 분야 중심으로 열립니다">' +
        '<span class="dot"></span>전체 보기</button>';
    }
    var f = FIELD_BY_KEY[state.field];
    return '<span class="field-badge f-' + f.slug + '" style="color:var(--fc)">' +
      '<button data-field-badge style="all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:7px">' +
      '<span class="dot" style="background:var(--fc)"></span>' + f.key + "</button>" +
      '<button class="x" data-field-clear aria-label="분야 선택 해제" title="분야 선택 해제">×</button></span>';
  }

  function setField(next) {
    var p = new URLSearchParams(location.search);
    if (next) { p.set("field", next); ss("field", next); }
    else { p.set("field", ""); p.delete("field"); ss("field", null); }
    // 분야를 끄면 세션 기억도 지운다: "" 를 명시해 재주입을 막는다
    if (!next) p.set("field", "");
    location.search = p.toString();
  }

  /* ── 유틸 ───────────────────────────────────────── */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fieldSlug(key) { return (FIELD_BY_KEY[key] || {}).slug || "prob"; }
  var SHAPE = { prob: "", infer: "sq", bayes: "tri", applied: "dia", ds: "hex" };
  function chipHTML(key) {
    var s = fieldSlug(key);
    return '<span class="chip f-' + s + " " + SHAPE[s] + '">' + esc(key) + "</span>";
  }
  function byId(id) {
    for (var i = 0; i < D.works.length; i++) if (D.works[i].id === id) return D.works[i];
    return null;
  }
  function chapterOf(n) {
    for (var i = 0; i < D.chapters.length; i++) if (D.chapters[i].n === n) return D.chapters[i];
    return null;
  }
  function matches(w, q) {
    if (!q) return true;
    var t = (w.year + " " + w.field + " " + w.nameKo + " " + w.nameEn + " " + w.workTitle + " " +
      w.contribution + " " + w.workDesc + " " + w.keywords.join(" ")).toLowerCase();
    return q.toLowerCase().split(/\s+/).filter(Boolean).every(function (tok) { return t.indexOf(tok) >= 0; });
  }

  /* ── 상세 패널 (타임라인·저작표 공용) ─────────────── */
  var detailEl = null, backdropEl = null, lastFocus = null;

  function ensureDetail() {
    if (detailEl) return detailEl;
    detailEl = document.createElement("aside");
    detailEl.className = "tl-detail";
    detailEl.setAttribute("role", "dialog");
    detailEl.setAttribute("aria-modal", "false");
    detailEl.setAttribute("aria-label", "저작 상세");
    detailEl.hidden = true;
    document.body.appendChild(detailEl);
    return detailEl;
  }

  function closeDetail() {
    if (!detailEl) return;
    detailEl.classList.remove("open");
    detailEl.hidden = true;
    if (backdropEl) { backdropEl.remove(); backdropEl = null; }
    document.querySelectorAll(".tl-node.sel").forEach(function (n) { n.classList.remove("sel"); });
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    var p = new URLSearchParams(location.search);
    if (p.has("id")) { p.delete("id"); history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p : "")); }
  }

  function openDetail(w, opts) {
    if (!w) return;
    opts = opts || {};
    lastFocus = document.activeElement;
    var el = ensureDetail();
    var siblings = D.works.filter(function (x) { return x.personId === w.personId && x.id !== w.id; });
    var ch = chapterOf(w.chapter);
    var s = fieldSlug(w.field);
    var html = '<button class="icon-btn close" data-close aria-label="닫기">✕</button>' +
      '<div class="f-' + s + '">' + chipHTML(w.field) +
      ' <span class="small muted" style="margin-left:6px">' + w.year + "년</span></div>" +
      "<h2>" + esc(w.workTitle) + "</h2>" +
      '<p class="small muted" style="margin:0">' + esc(w.nameKo) + " (" + esc(w.nameEn) + ")</p>" +
      '<p class="lbl">이 저작이 한 일</p><p style="margin:0;font-size:15.5px">' + esc(w.workDesc) + "</p>" +
      '<p class="lbl">이 인물의 핵심 기여</p><p style="margin:0;font-size:15px" class="muted">' + esc(w.contribution) + "</p>";
    if (w.keywords && w.keywords.length) {
      html += '<p class="lbl">키워드</p><p class="small muted" style="margin:0">' +
        w.keywords.map(esc).join(" · ") + "</p>";
    }
    html += '<div class="links">';
    if (w.sourceUrl) html += '<a class="btn btn-sm" href="' + esc(w.sourceUrl) + '" target="_blank" rel="noopener">원문 보기 ↗</a>';
    if (w.wikiUrl) html += '<a class="btn btn-sm" href="' + esc(w.wikiUrl) + '" target="_blank" rel="noopener">위키백과: 인물/주제 ↗</a>';
    html += "</div>";
    if (ch) {
      html += '<div class="links"><a class="btn btn-sm btn-primary" href="' +
        rel("story/" + ch.file) + '">' + ch.n + "장 「" + esc(ch.title) + "」 읽기 →</a></div>";
    }
    if (siblings.length) {
      html += '<p class="lbl">이 인물의 다른 저작 ' + siblings.length + "편</p><ul class='work-list'>";
      siblings.sort(function (a, b) { return a.year - b.year; }).forEach(function (x) {
        html += '<li><a class="work-item f-' + fieldSlug(x.field) + '" href="#" data-open="' + esc(x.id) + '">' +
          '<span class="yr">' + x.year + '</span><span><span class="ti">' + esc(x.workTitle) + "</span></span></a></li>";
      });
      html += "</ul>";
    }
    el.innerHTML = html;
    el.hidden = false;
    requestAnimationFrame(function () { el.classList.add("open"); });

    if (window.innerWidth <= 620 && !backdropEl) {
      backdropEl = document.createElement("div");
      backdropEl.className = "backdrop";
      backdropEl.addEventListener("click", closeDetail);
      document.body.appendChild(backdropEl);
    }
    el.querySelector("[data-close]").addEventListener("click", closeDetail);
    el.querySelectorAll("[data-open]").forEach(function (a) {
      a.addEventListener("click", function (e) { e.preventDefault(); openDetail(byId(a.getAttribute("data-open"))); });
    });
    el.querySelector("[data-close]").focus();

    if (!opts.silent) {
      var p = new URLSearchParams(location.search);
      p.set("id", w.id);
      history.replaceState(null, "", location.pathname + "?" + p.toString());
    }
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && detailEl && !detailEl.hidden) closeDetail();
  });

  /* ── 읽기 진행 바 ───────────────────────────────── */
  function initProgress() {
    var bar = document.querySelector("[data-progress]");
    if (!bar) return;
    function upd() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    }
    document.addEventListener("scroll", upd, { passive: true });
    upd();
  }

  /* ── 장 목차 활성 표시 ──────────────────────────── */
  function initToc() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    links.forEach(function (a) {
      var t = document.getElementById(a.getAttribute("href").slice(1));
      if (t) map[t.id] = a;
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          links.forEach(function (a) { a.classList.remove("on"); });
          if (map[en.target.id]) map[en.target.id].classList.add("on");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    Object.keys(map).forEach(function (id) { io.observe(document.getElementById(id)); });
  }

  /* ── 서사 페이지: 선택 분야를 앞으로 정렬 ─────────── */
  function initChapterWorks() {
    var host = document.querySelector("[data-chapter-works]");
    if (!host) return;
    var n = parseInt(host.getAttribute("data-chapter-works"), 10);
    var list = D.works.filter(function (w) { return w.chapter === n; });
    list.sort(function (a, b) {
      if (state.field) {
        var af = a.field === state.field ? 0 : 1, bf = b.field === state.field ? 0 : 1;
        if (af !== bf) return af - bf;
      }
      return a.year - b.year || a.workTitle.localeCompare(b.workTitle);
    });
    var head = document.querySelector("[data-chapter-works-count]");
    if (head) head.textContent = list.length;
    host.innerHTML = list.map(function (w) {
      var dim = state.field && w.field !== state.field ? " dim" : "";
      return '<li><a class="work-item f-' + fieldSlug(w.field) + dim + '" href="' + rel("timeline.html") +
        "?id=" + encodeURIComponent(w.id) + '">' +
        '<span class="yr">' + w.year + "</span><span>" +
        '<span class="ti">' + esc(w.workTitle) + "</span>" +
        '<span class="de">' + esc(w.workDesc) + "</span>" +
        '<span class="wh">' + esc(w.nameKo) + " (" + esc(w.nameEn) + ") · " + esc(w.field) + "</span>" +
        "</span></a></li>";
    }).join("");
  }

  /* ── 공개 API ───────────────────────────────────── */
  window.SH = {
    data: D, state: state, rel: rel, esc: esc, chipHTML: chipHTML, fieldSlug: fieldSlug,
    byId: byId, chapterOf: chapterOf, matches: matches, openDetail: openDetail,
    closeDetail: closeDetail, setField: setField, fieldByKey: FIELD_BY_KEY, ss: ss,
    decorate: decorate
  };

  function boot() {
    buildHeader();
    initProgress();
    initToc();
    initChapterWorks();
    document.querySelectorAll("[data-year]").forEach(function (el) {
      el.textContent = new Date().getFullYear();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
