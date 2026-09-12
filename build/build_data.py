# -*- coding: utf-8 -*-
"""xlsx -> site/assets/data.js  (PRD v2 §7.1, §7.2, §9.1)"""
import json, re, unicodedata, os
import openpyxl

SRC = "/root/.claude/uploads/99368727-9637-55ea-906c-670e95048319/4c40d411-statistics-history-timeline-revised.xlsx"
OUT = "/home/claude/site/assets/data.js"

# ── §9.1 용어 치환: 우도 → 가능도 (전면 통일) ────────────────────────────
TERM_MAP = [("우도", "가능도")]
_subst_log = []

def subst(text, ctx=""):
    if not text:
        return ""
    out = text
    for a, b in TERM_MAP:
        if a in out:
            _subst_log.append({"ctx": ctx, "before": out})
            out = out.replace(a, b)
            _subst_log[-1]["after"] = out
    return out

# ── id 생성용 성(姓) 슬러그 ─────────────────────────────────────────────
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s

def person_key(name_en):
    """'Jerzy Neyman & Egon Pearson' -> 'neyman-pearson' 형태의 안정적 키"""
    parts = re.split(r"\s*(?:&|,| and )\s*", name_en)
    surs = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        toks = [t for t in re.split(r"\s+", p) if t and not re.fullmatch(r"[A-Z]\.", t)]
        if toks:
            surs.append(slug(toks[-1]))
    surs = [s for s in surs if s]
    return "-".join(surs[:3]) or slug(name_en)

STOP = set("및 등 통한 통해 위한 이용한 기반 정립 도입 제시 창안 개척 수립 체계화 발전 최초로 모델링 분석 이론".split())

def keywords(contribution, title, desc):
    ks = []
    for chunk in re.split(r"[,·]", contribution or ""):
        c = chunk.strip()
        c = re.sub(r"^(그리고|또한)\s+", "", c)
        if 2 <= len(c) <= 28 and c not in STOP:
            ks.append(c)
    for m in re.findall(r"\b[A-Z]{2,6}\b", f"{contribution} {title} {desc}"):
        if m not in ks:
            ks.append(m)
    for m in re.findall(r"\(([^)]{2,20})\)", contribution or ""):
        if m not in ks:
            ks.append(m)
    seen, out = set(), []
    for k in ks:
        if k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out[:8]

# ── 서사 장 배정 규칙 (PRD §10, 목표 건수 6/3/4/23/32/17) ────────────────
def chapter_of(year, field):
    if year <= 1763:
        return 1
    if year <= 1812:
        return 2
    if year <= 1885:
        return 3
    if field == "베이즈" and year < 1950:
        return 5          # 주관/객관 베이즈 계보는 5장에서 함께 다룸
    if year <= 1949:
        return 4
    if field == "데이터과학" and year >= 1984:
        return 6
    return 5

# ── weight: 3=분기점, 2=주요, 1=보통 ────────────────────────────────────
W3 = {
    (1654, "Blaise Pascal"), (1662, "John Graunt"), (1713, "Jacob Bernoulli"),
    (1763, "Thomas Bayes"), (1809, "Carl Friedrich Gauss"), (1812, "Pierre-Simon Laplace"),
    (1858, "Florence Nightingale"), (1886, "Francis Galton"), (1900, "Karl Pearson"),
    (1908, "William Sealy Gosset"), (1933, "Andrey Kolmogorov"),
    (1970, "George E. P. Box & Gwilym M. Jenkins"),
    (2012, "Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton"),
}
W3_TITLES = {
    "Statistical Methods for Research Workers", "The Design of Experiments",
    "On the Problem of the Most Efficient Tests of Statistical Hypotheses",
    "Bootstrap Methods: Another Look at the Jackknife",
    "Regression Shrinkage and Selection via the Lasso",
    "Statistical Modeling: The Two Cultures", "Exploratory Data Analysis",
    "Regression Models and Life-Tables", "Theory of Probability",
    "Random Forests", "Generalized Linear Models",
}
W2_TITLES = {
    "The Doctrine of Chances", "Approximatio ad Summam Terminorum Binomii",
    "Nouvelles méthodes pour la détermination des orbites des comètes",
    "Sur l'homme et le développement de ses facultés",
    "On the Mode of Communication of Cholera",
    "On the Mathematical Foundations of Theoretical Statistics",
    "The Probable Error of a Mean", "Economic Control of Quality of Manufactured Product",
    "Analysis of a Complex of Statistical Variables into Principal Components",
    "La prévision: ses lois logiques, ses sources subjectives",
    "Outline of a Theory of Statistical Estimation Based on the Classical Theory of Probability",
    "Information and Accuracy Attainable in the Estimation of Statistical Parameters",
    "Individual Comparisons by Ranking Methods", "Sequential Analysis",
    "Smoking and Carcinoma of the Lung", "The Foundations of Statistics",
    "Inadmissibility of the Usual Estimator for the Mean of a Multivariate Normal Distribution",
    "An Empirical Bayes Approach to Statistics",
    "Nonparametric Estimation from Incomplete Observations",
    "The Future of Data Analysis",
    "An Algorithm for the Machine Calculation of Complex Fourier Series",
    "Monte Carlo Sampling Methods Using Markov Chains and Their Applications",
    "Inference and Missing Data", "Classification and Regression Trees",
    "Learning representations by back-propagating errors",
    "Sampling-Based Approaches to Calculating Marginal Densities",
    "Support-Vector Networks", "The Elements of Statistical Learning",
    "Compressed Sensing", "A Fast Learning Algorithm for Deep Belief Nets",
    "Tidy Data", "Bayesian Data Analysis", "Truth and Probability",
    "The Environment and Disease: Association or Causation?",
    "Conditional Expectation and Unbiased Estimates", "Out of the Crisis",
}

FIELDS = [
    {"key": "확률", "slug": "prob", "color": "#5b6ee1", "label": "확률",
     "tag": "우연을 수로 바꾼 사람들",
     "blurb": "도박판의 분배 문제에서 출발한 확률론은 300년 만에 측도론 위에 세워진 엄밀한 수학이 되었다. 통계학이 딛고 선 바닥이다.",
     "leads": ["파스칼", "베르누이", "라플라스", "콜모고로프"], "chapters": [1, 2]},
    {"key": "추정·검정", "slug": "infer", "color": "#1f9e8f", "label": "추정·검정",
     "tag": "데이터에서 모수를 캐내는 기술",
     "blurb": "관측에는 언제나 오차가 있다. 그 오차를 뚫고 참값을 추정하고 가설을 판정하는 절차가 20세기 통계학의 본체를 이룬다.",
     "leads": ["가우스", "골턴", "피어슨", "피셔", "네이만"], "chapters": [2, 4]},
    {"key": "베이즈", "slug": "bayes", "color": "#d99326", "label": "베이즈",
     "tag": "믿음을 갱신하는 통계학",
     "blurb": "1763년의 유고에서 시작해 두 세기 동안 주변부에 머물다, 계산의 힘을 얻어 주류로 복귀한 추론의 또 다른 갈래다.",
     "leads": ["베이즈", "제프리스", "새비지", "겔먼"], "chapters": [1, 5]},
    {"key": "응용", "slug": "applied", "color": "#d2557a", "label": "응용",
     "tag": "통계가 세상을 바꾼 현장",
     "blurb": "생명표, 콜레라 지도, 로즈 다이어그램, 흡연-폐암 연구. 통계학이 실제로 사람을 살린 장면들이 여기 있다.",
     "leads": ["그랜트", "나이팅게일", "스노", "데밍"], "chapters": [1, 3, 5]},
    {"key": "데이터과학", "slug": "ds", "color": "#8b5cd6", "label": "데이터과학",
     "tag": "계산이 통계를 다시 쓰다",
     "blurb": "컴퓨터가 이론의 제약을 걷어내자 탐색적 분석, 재표본추출, 기계학습이 차례로 등장했다. 통계학과 기계학습이 만나는 지대다.",
     "leads": ["튜키", "에프론", "브라이먼", "힌턴"], "chapters": [5, 6]},
]

CHAPTERS = [
    {"n": 0, "file": "00-prehistory.html", "title": "세기를 센 사람들",
     "span": [-500, 1653], "spanLabel": "고대 ~ 1653", "minutes": 6},
    {"n": 1, "file": "01-probability.html", "title": "확률의 탄생",
     "span": [1654, 1763], "spanLabel": "1654 ~ 1763", "minutes": 4},
    {"n": 2, "file": "02-errors.html", "title": "오차와 최소제곱",
     "span": [1755, 1840], "spanLabel": "1755 ~ 1840년대", "minutes": 4},
    {"n": 3, "file": "03-society.html", "title": "사회를 측정하다",
     "span": [1786, 1885], "spanLabel": "1786 ~ 1880년대", "minutes": 4},
    {"n": 4, "file": "04-three-waves.html", "title": "현대 통계학의 3파",
     "span": [1880, 1955], "spanLabel": "1880년대 ~ 1950년대", "minutes": 5},
    {"n": 5, "file": "05-computation.html", "title": "계산·비모수·베이즈의 부흥",
     "span": [1950, 1999], "spanLabel": "1950년대 ~ 1990년대", "minutes": 6},
    {"n": 6, "file": "06-data-science.html", "title": "통계적 학습과 데이터과학",
     "span": [1984, 2015], "spanLabel": "1984 ~ 2015", "minutes": 6},
    {"n": 7, "file": "07-epilogue.html", "title": "에필로그 — 2015년 이후, 남은 질문",
     "span": [2015, 2026], "spanLabel": "2015 ~", "minutes": 3},
]

# ── 0장 전사(前史): xlsx에 없음. 전적으로 Wikipedia "History of statistics" 기반 ──
PREHISTORY = [
    {"id": "pre-thucydides", "yearSort": -430, "yearDisplay": "기원전 5세기",
     "title": "투키디데스와 벽돌 세기", "who": "투키디데스 (Thucydides)",
     "desc": "플라타이아이 공성전에서 아테네군은 적 성벽의 벽돌 층수를 여러 사람이 따로 세게 한 뒤 가장 많이 나온 값을 채택해 사다리 길이를 정했다. 최빈값을 쓴 가장 이른 기록으로 꼽힌다."},
    {"id": "pre-census", "yearSort": -200, "yearDisplay": "기원전 2세기 ~",
     "title": "한(漢)과 로마의 국가 조사", "who": "한 제국 · 로마 제국",
     "desc": "인구, 토지, 재산을 대규모로 집계한 국가 기록. 오랫동안 '통계'는 국가가 스스로를 헤아리는 행위를 뜻했다."},
    {"id": "pre-pyx", "yearSort": 1150, "yearDisplay": "12세기 ~",
     "title": "Trial of the Pyx", "who": "잉글랜드 왕립 조폐국",
     "desc": "주조한 동전 전량이 아니라 무작위로 뽑은 일부의 순도를 검사해 전체를 판정한 제도. 표본으로 모집단을 판단한 초기 사례다."},
    {"id": "pre-villani", "yearSort": 1340, "yearDisplay": "14세기",
     "title": "빌라니의 도시 연대기", "who": "조반니 빌라니 (Giovanni Villani)",
     "desc": "피렌체의 인구·상거래·식량 소비량 같은 수치를 역사 서술 안에 본격적으로 끌어들였다."},
    {"id": "pre-stevin", "yearSort": 1585, "yearDisplay": "1585",
     "title": "십진법의 보급", "who": "시몬 스테빈 (Simon Stevin)",
     "desc": "소수 표기를 대중화해 긴 수치 계산의 문턱을 낮췄다. 계산이 쉬워지자 헤아릴 수 있는 것의 범위가 넓어졌다."},
    {"id": "pre-ghilini", "yearSort": 1589, "yearDisplay": "1589",
     "title": "'statistic'이라는 말", "who": "지롤라모 길리니 (Girolamo Ghilini)",
     "desc": "'국가에 관한 사실'을 뜻하는 말로 statistic이 등장했다. 어원은 state, 곧 국가다."},
    {"id": "pre-wright", "yearSort": 1599, "yearDisplay": "1599",
     "title": "중앙값의 착상", "who": "에드워드 라이트 (Edward Wright)",
     "desc": "항해술 저술에서 여러 번 측정한 값 가운데 한가운데 값을 택하는 방식을 제안했다. 중앙값 개념의 이른 형태다."},
    {"id": "pre-achenwall", "yearSort": 1749, "yearDisplay": "1749",
     "title": "Statistik의 성립", "who": "고트프리트 아헨발 (Gottfried Achenwall)",
     "desc": "독일어 Statistik을 학문 명칭으로 확립했다. 이때의 통계학은 수치 분석이 아니라 국가 현황을 서술하는 학문이었다."},
    {"id": "pre-sinclair", "yearSort": 1791, "yearDisplay": "1791",
     "title": "영어 'statistics'의 도입", "who": "존 싱클레어 (Sir John Sinclair)",
     "desc": "『스코틀랜드 통계 보고』에서 이 말을 영어권에 들여오며, 국민의 형편을 헤아린다는 뜻을 덧붙였다."},
]


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["통계학사 타임라인"]
    works, seen_ids = [], {}
    # 헤더는 4행, 데이터는 5행부터 시작한다 (총 86건 — 요약 시트 기재와 일치)
    for row in ws.iter_rows(min_row=5, values_only=True):
        if not row[0]:
            continue
        year, field, name_ko, name_en, contribution, title, desc, src_url, wiki_url = row[:9]
        year = int(year)
        ctx = f"{year} {name_en}"
        contribution = subst((contribution or "").strip(), ctx)
        desc = subst((desc or "").strip(), ctx)
        title = (title or "").strip()
        pid = person_key(name_en)
        base = f"{year}-{pid.split('-')[0]}"
        n = seen_ids.get(base, 0) + 1
        seen_ids[base] = n
        wid = base if n == 1 else f"{base}-{n}"
        w = 1
        if (year, name_en) in W3 or title in W3_TITLES:
            w = 3
        elif title in W2_TITLES:
            w = 2
        works.append({
            "id": wid, "year": year, "field": field.strip(),
            "nameKo": (name_ko or "").strip(), "nameEn": (name_en or "").strip(),
            "contribution": contribution, "workTitle": title, "workDesc": desc,
            "sourceUrl": (src_url or "").strip(), "wikiUrl": (wiki_url or "").strip(),
            "personId": pid, "chapter": chapter_of(year, field.strip()), "weight": w,
            "keywords": keywords(contribution, title, desc),
        })

    works.sort(key=lambda w: (w["year"], w["field"], w["workTitle"]))

    # 인물 집계
    people = {}
    for w in works:
        p = people.setdefault(w["personId"], {
            "personId": w["personId"], "nameKo": w["nameKo"], "nameEn": w["nameEn"],
            "works": [], "fields": [], "years": []})
        p["works"].append(w["id"])
        p["years"].append(w["year"])
        if w["field"] not in p["fields"]:
            p["fields"].append(w["field"])
    people = sorted(people.values(), key=lambda p: (min(p["years"]), p["nameEn"]))
    for p in people:
        p["from"], p["to"], p["count"] = min(p["years"]), max(p["years"]), len(p["works"])
        del p["years"]

    data = {"works": works, "prehistory": PREHISTORY, "people": people,
            "chapters": CHAPTERS, "fields": FIELDS,
            "meta": {"source": "statistics-history-timeline-revised.xlsx",
                     "count": len(works), "generated": "2026-09-12"}}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 자동 생성 파일 — build/build_data.py 로 재생성. 직접 수정하지 말 것. */\n")
        f.write("/* 원본: statistics-history-timeline-revised.xlsx · 용어 치환: 우도 → 가능도 (PRD v2 §9.1) */\n")
        f.write("window.__STATHIST__ = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    # 검증 리포트
    from collections import Counter
    print("works:", len(works))
    print("field :", dict(Counter(w["field"] for w in works)))
    print("chapter:", dict(sorted(Counter(w["chapter"] for w in works).items())))
    print("weight:", dict(sorted(Counter(w["weight"] for w in works).items())))
    print("people:", len(people))
    print("dup ids:", [k for k, v in Counter(w["id"] for w in works).items() if v > 1])
    print("substitutions:", len(_subst_log))
    blob = json.dumps(data, ensure_ascii=False)
    print("'우도' remaining in data:", blob.count("우도"))
    with open("/home/claude/build/subst_log.json", "w", encoding="utf-8") as f:
        json.dump(_subst_log, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
