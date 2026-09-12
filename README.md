# 통계학의 역사 — 웹사이트

PRD v2.0에 따라 구현한 정적 사이트입니다. 빌드 도구·서버·패키지 설치가 필요 없습니다.

## 바로 쓰기

`index.html`을 브라우저에서 열면 됩니다. `file://`로 직접 열어도 모든 기능이 동작합니다.

## GitHub Pages로 배포하기

이 폴더의 내용을 **저장소 최상위에 그대로** 올리면 됩니다. 빌드 과정이 없으므로
GitHub Actions 설정도 필요 없습니다.

### 방법 A — 웹에서 드래그 앤 드롭 (가장 간단)

1. github.com에서 **New repository** → 이름을 정합니다(예: `statistics-history`).
   Public으로 만들어야 무료 계정에서 Pages를 쓸 수 있습니다.
2. 저장소 첫 화면의 **uploading an existing file** 링크를 누릅니다.
3. 이 폴더 안의 항목을 **폴더째 끌어다 놓습니다**
   (`index.html`, `timeline.html`, `works.html`, `people.html`, `appendix.html`,
   `README.md`, `.nojekyll`, `assets/` 폴더, `story/` 폴더).
   ※ `statistics-history-site` 폴더 자체가 아니라 **그 안의 내용물**을 올려야 합니다.
   한 단계 더 깊어지면 주소가 `/statistics-history-site/index.html`이 됩니다.
4. **Commit changes**를 누릅니다.
5. 저장소 **Settings → Pages**로 갑니다.
6. Source에서 **Deploy from a branch**를 고르고, Branch는 `main` / `/ (root)` →
   **Save**.
7. 1~2분 뒤 같은 화면 위쪽에 주소가 뜹니다:
   `https://<사용자이름>.github.io/<저장소이름>/`

### 방법 B — git 명령으로

```bash
cd statistics-history-site
git init -b main
git add -A
git commit -m "통계학의 역사 사이트"
git remote add origin https://github.com/<사용자이름>/<저장소이름>.git
git push -u origin main
```

이후 Settings → Pages에서 위 5~7번과 동일하게 설정합니다.
다음부터는 파일을 고치고 `git add -A && git commit -m "수정" && git push` 하면
1분 내에 반영됩니다.

### 알아두면 좋은 점

- **`.nojekyll`이 있어야 합니다.** GitHub Pages는 기본적으로 Jekyll로 한 번 처리하는데,
  이 파일이 있으면 그 단계를 건너뛰고 파일을 그대로 서빙합니다. 이 폴더에 이미 포함돼 있고,
  숨김 파일이라 드래그할 때 빠지기 쉬우니 확인하세요(맥 Finder는 `⌘⇧.`로 숨김 파일 표시).
- **하위 경로에서도 동작합니다.** 모든 링크가 상대경로라서
  `https://아이디.github.io/저장소/` 처럼 한 단계 아래에 놓여도 그대로 작동합니다.
  `<base>` 태그를 넣거나 경로를 고칠 필요가 없습니다.
- **주소 공유가 됩니다.** `?field=베이즈`, `?id=1763-bayes` 같은 쿼리스트링이 그대로 살아 있어
  특정 분야나 특정 저작을 열어둔 화면의 링크를 그대로 보낼 수 있습니다.
- **수정 후 화면이 그대로면** 브라우저 강력 새로고침(`Ctrl/⌘ + Shift + R`)을 해보세요.
  `assets/data.js`가 캐시에 남아 있는 경우가 있습니다.
- **비공개로 쓰려면** Private 저장소 + Pages는 유료 플랜(GitHub Pro/Team 이상)이 필요합니다.
  무료로 하려면 Public 저장소를 쓰거나, Netlify Drop 같은 곳에 폴더를 끌어다 놓는 방법도 있습니다.
- **사용자 지정 도메인**은 Settings → Pages → Custom domain에서 설정하고,
  도메인 쪽 DNS에 CNAME을 추가하면 됩니다.

## 구조

```
index.html          입구 — 분야 선택 게이트 + 한눈에 보기
timeline.html       인터랙티브 타임라인 (SVG 직접 렌더)
works.html          저작 데이터베이스 86편 (정렬·검색·CSV 내려받기)
people.html         인물 색인 72종
appendix.html       용어집 · 데이터 집계 · 용어 치환 대조표 · 제작 노트 · 출처
story/index.html    이야기 목차 (요약만 훑기 모드 포함)
story/00-prehistory.html   0장 세기를 센 사람들 (고대~1653)
story/01-probability.html  1장 확률의 탄생 (1654~1763)
story/02-errors.html       2장 오차와 최소제곱 (1755~1840년대)
story/03-society.html      3장 사회를 측정하다 (1786~1880년대)
story/04-three-waves.html  4장 현대 통계학의 3파 (1880년대~1950년대)
story/05-computation.html  5장 계산·비모수·베이즈의 부흥 (1950~1990년대)
story/06-data-science.html 6장 통계적 학습과 데이터과학 (1984~2015)
story/07-epilogue.html     7장 에필로그 — 2015년 이후
assets/data.js      전체 데이터 (window.__STATHIST__)
assets/site.css     공통 스타일 (라이트/다크 · 인쇄)
assets/site.js      헤더 · 분야 상태 전파 · 상세 패널 · 진행바 · 목차
assets/timeline.js  타임라인 렌더러
```

## 동작 원리 몇 가지

- **데이터**: `fetch`가 아니라 `assets/data.js`의 전역 변수로 제공합니다. `file://`에서 `fetch`가
  CORS로 차단되기 때문입니다. 외부 CDN·웹폰트·이미지 요청은 0건이라 오프라인에서도 완전히 동작합니다.
- **분야 상태**: 쿼리스트링 `?field=`가 정본입니다. `site.js`가 내부 링크 클릭 시점에 파라미터를
  덧붙입니다. `sessionStorage`는 보조 수단이며 없거나 실패해도 모든 기능이 동작합니다.
  잘못된 `field` 값은 조용히 전체 보기로 처리합니다.
- **타임라인**: 라이브러리 없이 SVG를 직접 그립니다. 가로축은 구간별 가변 스케일이 기본이고
  「실제 연도 비례」로 전환할 수 있습니다. 라벨은 같은 행의 다음 점까지 자리가 있을 때만 표시해
  겹침을 피합니다.
- **용어**: likelihood 계열을 모두 '가능도'로 통일했습니다. 원본 자료 파일은 수정하지 않고
  데이터 생성 단계에서 치환했으며, 대조표는 `appendix.html`에 있습니다.

## 데이터 다시 만들기

원본 xlsx가 갱신되면 `build/build_data.py`와 `build/build_pages.py`를 차례로 실행합니다.
용어 치환 규칙은 `build_data.py`의 `TERM_MAP`에, 서사 본문은 `build/content.py`에 있습니다.

```
python3 build/build_data.py     # xlsx -> assets/data.js (용어 치환 포함)
python3 build/build_pages.py    # data.js + content.py -> 14개 HTML
node    build/verify.js         # 브라우저 검증 (playwright 필요)
```

## 출처

- 저작 데이터: 「통계학의 역사를 바꾼 인물 및 주요 저작 타임라인 (1654~2015)」 자료집, 86건
- 서사·전사: Wikipedia, *History of statistics* (2026-09-12 열람, CC BY-SA 4.0)
