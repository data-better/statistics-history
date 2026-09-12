/* 통계학의 역사 — 타임라인 렌더러 (PRD v2 §6.2)
   외부 라이브러리 없이 SVG를 직접 그린다. */
(function () {
  "use strict";
  var SH = window.SH;
  if (!SH) return;
  var stage = document.getElementById("tl-stage");
  if (!stage) return;

  var D = SH.data;
  var NS = "http://www.w3.org/2000/svg";
  var FIELDS = D.fields.map(function (f) { return f.key; });
  var SLUG = {}, COLORVAR = {};
  D.fields.forEach(function (f) { SLUG[f.key] = f.slug; COLORVAR[f.key] = "var(--f-" + f.slug + ")"; });

  var LANE_H = 104, PAD_T = 16, AXIS_H = 34, PAD_L = 108, PAD_R = 26;
  var ROWS = [-26, 0, 26];

  /* ── 상태 ───────────────────────────────────────── */
  var qs = new URLSearchParams(location.search);
  var st = {
    active: {},                 // 분야 토글
    q: qs.get("q") || "",
    linear: false,
    k: 1, tx: 0,
    sel: qs.get("id") || "",
    hoverPerson: null
  };
  FIELDS.forEach(function (f) { st.active[f] = true; });
  if (SH.state.field) FIELDS.forEach(function (f) { st.active[f] = (f === SH.state.field); });

  /* ── 축: 구간별 가변 스케일 ─────────────────────── */
  var BRK = [1650, 1700, 1760, 1810, 1860, 1900, 1925, 1945, 1965, 1985, 2000, 2016];
  var segW = [];
  (function computeSegments() {
    var counts = [];
    for (var i = 0; i < BRK.length - 1; i++) {
      var c = D.works.filter(function (w) { return w.year >= BRK[i] && w.year < BRK[i + 1]; }).length;
      counts.push(c);
    }
    var total = 0, raw = counts.map(function (c, i) {
      var years = BRK[i + 1] - BRK[i];
      var v = Math.sqrt(c + 1) * 10 + years * 0.14;   // 밀도와 기간을 함께 반영
      total += v; return v;
    });
    segW = raw.map(function (v) { return v / total; });
  })();

  function baseX(year) {
    var y = Math.max(BRK[0], Math.min(BRK[BRK.length - 1] - 0.001, year));
    if (st.linear) return (y - BRK[0]) / (BRK[BRK.length - 1] - BRK[0]);
    var acc = 0;
    for (var i = 0; i < BRK.length - 1; i++) {
      if (y < BRK[i + 1]) return acc + segW[i] * (y - BRK[i]) / (BRK[i + 1] - BRK[i]);
      acc += segW[i];
    }
    return 1;
  }

  var W = 900;
  function innerW() { return Math.max(320, W - PAD_L - PAD_R); }
  function X(year) { return PAD_L + (baseX(year) * innerW() * st.k) + st.tx; }

  function clampPan() {
    var span = innerW() * st.k;
    var min = innerW() - span;
    if (min > 0) min = 0;
    st.tx = Math.max(min, Math.min(0, st.tx));
  }

  /* ── 데이터 선별 ────────────────────────────────── */
  function visible() {
    return D.works.filter(function (w) { return st.active[w.field] && SH.matches(w, st.q); });
  }

  /* ── 레이아웃 (겹침 회피) ───────────────────────── */
  function layout(list) {
    var byLane = {};
    FIELDS.forEach(function (f) { byLane[f] = []; });
    list.slice().sort(function (a, b) { return a.year - b.year; }).forEach(function (w) {
      byLane[w.field].push(w);
    });
    var placed = [];
    FIELDS.forEach(function (f, li) {
      var rows = [-Infinity, -Infinity, -Infinity];
      var laneMid = PAD_T + li * LANE_H + LANE_H / 2;
      var perRow = [[], [], []];
      byLane[f].forEach(function (w) {
        var x = X(w.year), r = 0;
        var gap = 15;
        for (var i = 0; i < ROWS.length; i++) { if (x - rows[i] > gap) { r = i; break; } r = i; }
        if (x - rows[r] <= gap) r = (r + 1) % ROWS.length;
        rows[r] = x;
        var p = { w: w, x: x, y: laneMid + ROWS[r], lane: li, row: r, label: false };
        perRow[r].push(p);
        placed.push(p);
      });
      // 라벨은 같은 행의 다음 점까지 자리가 넉넉할 때만 표시한다 (겹침 방지)
      perRow.forEach(function (list) {
        list.sort(function (a, b) { return a.x - b.x; });
        list.forEach(function (p, i) {
          if (p.w.weight < labelThreshold()) return;
          var need = 46 + p.w.nameKo.length * 12;
          var nxt = list[i + 1];
          if (!nxt || nxt.x - p.x > need) p.label = true;
        });
      });
    });
    return placed;
  }

  function labelThreshold() {
    if (st.k >= 3.2) return 1;
    if (st.k >= 1.7) return 2;
    return 3;
  }

  /* ── 그리기 ─────────────────────────────────────── */
  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  function markPath(g, slug, x, y, r, weight) {
    var fill = "var(--f-" + slug + ")";
    var o = { fill: fill, class: "mark" };
    if (slug === "prob") { o.cx = x; o.cy = y; o.r = r; el("circle", o, g); }
    else if (slug === "infer") { o.x = x - r; o.y = y - r; o.width = r * 2; o.height = r * 2; o.rx = 1.5; el("rect", o, g); }
    else if (slug === "bayes") { o.points = [x, y - r * 1.15, x + r * 1.1, y + r * .85, x - r * 1.1, y + r * .85].join(" "); el("polygon", o, g); }
    else if (slug === "applied") { o.points = [x, y - r * 1.2, x + r * 1.2, y, x, y + r * 1.2, x - r * 1.2, y].join(" "); el("polygon", o, g); }
    else {
      var pts = [];
      for (var i = 0; i < 6; i++) {
        var a = Math.PI / 6 + i * Math.PI / 3;
        pts.push((x + r * 1.12 * Math.cos(a)).toFixed(2), (y + r * 1.12 * Math.sin(a)).toFixed(2));
      }
      o.points = pts.join(" "); el("polygon", o, g);
    }
    if (weight === 3) {
      el("circle", { cx: x, cy: y, r: r + 4.5, fill: "none", stroke: fill, "stroke-width": 1, opacity: .5 }, g);
    }
  }

  var svg, nodesG, currentNodes = [];

  function render() {
    W = stage.clientWidth || 900;
    clampPan();
    var list = visible();
    var placed = layout(list);
    currentNodes = placed;
    var H = PAD_T + FIELDS.length * LANE_H + AXIS_H;

    stage.innerHTML = "";
    svg = el("svg", {
      viewBox: "0 0 " + W + " " + H, width: W, height: H,
      role: "img", "aria-label": "1654년부터 2015년까지 통계학 주요 저작 " + list.length + "건의 연대표"
    }, stage);

    // 레인 배경 · 라벨
    FIELDS.forEach(function (f, i) {
      var top = PAD_T + i * LANE_H;
      el("rect", {
        x: 0, y: top, width: W, height: LANE_H - 6, rx: 8,
        class: "tl-lane-bg", opacity: i % 2 ? .55 : .9
      }, svg);
      var g = el("g", { class: "f-" + SLUG[f] }, svg);
      var t = el("text", { x: 14, y: top + LANE_H / 2 - 6, class: "tl-lane-label" }, g);
      t.textContent = f;
      var cnt = list.filter(function (w) { return w.field === f; }).length;
      var t2 = el("text", { x: 14, y: top + LANE_H / 2 + 12, class: "tl-axis" }, g);
      t2.setAttribute("style", "font-size:11px;fill:var(--ink-soft)");
      t2.textContent = cnt + "편";
      if (!st.active[f]) g.setAttribute("opacity", ".35");
    });

    // 눈금
    var gridG = el("g", { class: "tl-grid" }, svg);
    var axisG = el("g", { class: "tl-axis" }, svg);
    var step = st.k >= 4 ? 10 : (st.k >= 2 ? 25 : 50);
    var yTop = PAD_T, yBot = PAD_T + FIELDS.length * LANE_H - 6;
    for (var yr = 1650; yr <= 2015; yr += step) {
      var x = X(yr);
      if (x < PAD_L - 40 || x > W + 20) continue;
      el("line", { x1: x, y1: yTop, x2: x, y2: yBot }, gridG);
      var tx = el("text", { x: x, y: yBot + 20, "text-anchor": "middle" }, axisG);
      tx.textContent = yr;
    }
    el("line", { x1: PAD_L - 6, y1: yBot + 1, x2: W - 4, y2: yBot + 1 }, axisG);

    // 동일 인물 연결선
    var linkG = el("g", null, svg);
    // 노드
    nodesG = el("g", null, svg);
    placed.forEach(function (p) {
      var w = p.w, slug = SLUG[w.field];
      var g = el("g", {
        class: "tl-node f-" + slug + (st.sel === w.id ? " sel" : ""),
        tabindex: 0, role: "button",
        "data-id": w.id, "data-person": w.personId,
        "aria-label": w.year + "년 " + w.nameKo + ", " + w.workTitle
      }, nodesG);
      var r = w.weight === 3 ? 6.5 : (w.weight === 2 ? 5 : 4);
      markPath(g, slug, p.x, p.y, r, w.weight);
      el("rect", { x: p.x - 11, y: p.y - 11, width: 22, height: 22, class: "hit" }, g);
      if (p.label) {
        var lab = el("text", { x: p.x + r + 5, y: p.y + 4 }, g);
        lab.textContent = w.year + " " + w.nameKo;
      }
      g.addEventListener("click", function () { select(w.id); });
      g.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(w.id); }
      });
      g.addEventListener("mouseenter", function () { drawLinks(linkG, w.personId); });
      g.addEventListener("mouseleave", function () { linkG.innerHTML = ""; });
      g.addEventListener("focus", function () { drawLinks(linkG, w.personId); });
      g.addEventListener("blur", function () { linkG.innerHTML = ""; });
    });

    document.getElementById("tl-count").textContent =
      list.length + "편" + (list.length !== D.works.length ? " / 전체 " + D.works.length + "편" : "");
    var empty = document.getElementById("tl-empty");
    if (empty) empty.hidden = list.length > 0;
  }

  function drawLinks(g, personId) {
    g.innerHTML = "";
    var pts = currentNodes.filter(function (p) { return p.w.personId === personId; });
    if (pts.length < 2) return;
    pts.sort(function (a, b) { return a.x - b.x; });
    var d = "M" + pts.map(function (p) { return p.x + " " + p.y; }).join(" L");
    el("path", { d: d, class: "tl-link" }, g);
  }

  /* ── 선택 ───────────────────────────────────────── */
  function select(id, silent) {
    st.sel = id;
    document.querySelectorAll(".tl-node").forEach(function (n) {
      n.classList.toggle("sel", n.getAttribute("data-id") === id);
    });
    SH.openDetail(SH.byId(id), { silent: silent });
  }

  /* ── 줌·팬 ──────────────────────────────────────── */
  function zoomAt(clientX, factor) {
    var rect = stage.getBoundingClientRect();
    var px = clientX - rect.left;
    var before = (px - PAD_L - st.tx) / st.k;
    st.k = Math.max(1, Math.min(8, st.k * factor));
    st.tx = px - PAD_L - before * st.k;
    clampPan();
    render();
  }

  stage.addEventListener("wheel", function (e) {
    if (!e.ctrlKey && Math.abs(e.deltaY) < 4) return;
    e.preventDefault();
    zoomAt(e.clientX, e.deltaY < 0 ? 1.16 : 1 / 1.16);
  }, { passive: false });

  var drag = null;
  stage.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".tl-node")) return;
    drag = { x: e.clientX, tx: st.tx };
    stage.setPointerCapture(e.pointerId);
    stage.style.cursor = "grabbing";
  });
  stage.addEventListener("pointermove", function (e) {
    if (!drag) return;
    st.tx = drag.tx + (e.clientX - drag.x);
    clampPan(); render();
  });
  ["pointerup", "pointercancel"].forEach(function (ev) {
    stage.addEventListener(ev, function () { drag = null; stage.style.cursor = ""; });
  });

  /* ── 키보드 이동 ────────────────────────────────── */
  stage.addEventListener("keydown", function (e) {
    var cur = e.target.closest(".tl-node");
    if (!cur) return;
    var id = cur.getAttribute("data-id");
    var me = currentNodes.filter(function (p) { return p.w.id === id; })[0];
    if (!me) return;
    var next = null;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      var same = currentNodes.filter(function (p) { return p.lane === me.lane; })
        .sort(function (a, b) { return a.x - b.x; });
      var i = same.indexOf(me);
      next = same[i + (e.key === "ArrowRight" ? 1 : -1)];
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      var dir = e.key === "ArrowDown" ? 1 : -1;
      for (var l = me.lane + dir; l >= 0 && l < FIELDS.length; l += dir) {
        var cand = currentNodes.filter(function (p) { return p.lane === l; });
        if (cand.length) {
          next = cand.reduce(function (best, p) {
            return Math.abs(p.x - me.x) < Math.abs(best.x - me.x) ? p : best;
          });
          break;
        }
      }
    }
    if (next) {
      e.preventDefault();
      var g = nodesG.querySelector('[data-id="' + next.w.id + '"]');
      if (g) g.focus();
    }
  });

  /* ── 툴바 ───────────────────────────────────────── */
  function buildToolbar() {
    var bar = document.getElementById("tl-toolbar");
    var html = "";
    D.fields.forEach(function (f) {
      html += '<button class="filter-btn f-' + f.slug + '" data-field="' + SH.esc(f.key) + '" aria-pressed="' +
        (st.active[f.key] ? "true" : "false") + '">' + SH.esc(f.key) + "</button>";
    });
    html += '<button class="btn btn-sm" data-all>전체</button>' +
      '<input class="search-box" type="search" placeholder="인물·저작·키워드 검색" aria-label="검색" value="' +
      SH.esc(st.q) + '">' +
      '<button class="btn btn-sm" data-linear aria-pressed="false" title="구간별 가변 축과 실제 연도 비례 축 전환">실제 연도 비례</button>' +
      '<button class="btn btn-sm" data-zoom="1.4" aria-label="확대">＋</button>' +
      '<button class="btn btn-sm" data-zoom="0.71" aria-label="축소">－</button>' +
      '<button class="btn btn-sm" data-reset>전체 보기</button>' +
      '<span class="tl-count" id="tl-count"></span>';
    bar.innerHTML = html;

    bar.querySelectorAll("[data-field]").forEach(function (b) {
      b.addEventListener("click", function () {
        var f = b.getAttribute("data-field");
        st.active[f] = !st.active[f];
        b.setAttribute("aria-pressed", st.active[f] ? "true" : "false");
        syncUrl(); render();
      });
    });
    bar.querySelector("[data-all]").addEventListener("click", function () {
      FIELDS.forEach(function (f) { st.active[f] = true; });
      bar.querySelectorAll("[data-field]").forEach(function (b) { b.setAttribute("aria-pressed", "true"); });
      syncUrl(); render();
    });
    var search = bar.querySelector(".search-box");
    var timer;
    search.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () { st.q = search.value.trim(); syncUrl(); render(); }, 160);
    });
    bar.querySelector("[data-linear]").addEventListener("click", function () {
      st.linear = !st.linear;
      this.setAttribute("aria-pressed", st.linear ? "true" : "false");
      this.textContent = st.linear ? "구간별 가변 축" : "실제 연도 비례";
      render();
    });
    bar.querySelectorAll("[data-zoom]").forEach(function (b) {
      b.addEventListener("click", function () {
        var r = stage.getBoundingClientRect();
        zoomAt(r.left + r.width / 2, parseFloat(b.getAttribute("data-zoom")));
      });
    });
    bar.querySelector("[data-reset]").addEventListener("click", function () {
      st.k = 1; st.tx = 0; render();
    });
  }

  function syncUrl() {
    var p = new URLSearchParams(location.search);
    if (st.q) p.set("q", st.q); else p.delete("q");
    var on = FIELDS.filter(function (f) { return st.active[f]; });
    if (on.length === 1) p.set("field", on[0]);
    else if (on.length === FIELDS.length) p.set("field", "");
    if (!p.get("field")) p.delete("field");
    history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p.toString() : ""));
  }

  /* ── 시작 ───────────────────────────────────────── */
  buildToolbar();
  render();

  var rt;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(render, 120);
  });

  if (st.sel && SH.byId(st.sel)) {
    var w = SH.byId(st.sel);
    if (!st.active[w.field]) { st.active[w.field] = true; buildToolbar(); }
    render();
    select(st.sel, true);
  } else if (qs.get("y")) {
    var y = parseInt(qs.get("y"), 10);
    if (!isNaN(y)) {
      st.k = 2.4;
      st.tx = innerW() / 2 - baseX(y) * innerW() * st.k;
      clampPan(); render();
    }
  }
})();
