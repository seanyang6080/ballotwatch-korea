import streamlit as st
import pandas as pd
import altair as alt
import folium
import branca.colormap as bcm
from folium import CircleMarker
from streamlit_folium import st_folium
from pathlib import Path
import html as _html
import json
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# 상수 / 데이터 출처
# ─────────────────────────────────────────────────────────────────────────────
# 출처: 중앙선거관리위원회 2026-06-05 공식 발표 (구 단위 집계)
TOTAL_STATIONS = 14288   # 6·3 지방선거 전국 투표소 총수 (선관위 발표)
DATA_AS_OF = "2026-06-05"  # 데이터 기준일

# 선관위 발표 기대치 — 데이터 합계 검증용
EXPECTED_SHORTAGE = 50   # 용지 부족 투표소
EXPECTED_WAIT = 22       # 투표 일시 중단 투표소

# ── 색상 토큰 ────────────────────────────────────────────────────────────────
# 정당 연상색 사용 금지: 빨강(#FF0000, 국민의힘)·파랑/남색(#0000FF, 민주당)·
# 주황(개혁신당) 계열을 모두 배제하고, 중립적인 틸(teal) 단색을 액센트로 사용.
# 앱 테마는 config.toml에서 '다크'로 고정 → 다크 배경에서 잘 보이는 밝은 teal 사용.
ACCENT = "#2DD4BF"        # teal-400 (밝은 액센트 / 차트 수치 라벨색)
WAIT_OUTLINE = "#F8FAFC"  # 밝은 색 — 다크 지도 타일 위에서 '투표 일시 중단' 테두리가 보이도록

# shortage 색 스케일(저값 → 고값). 다크 배경 기준으로 '고값일수록 밝게' 하여
# 부족 규모가 큰 곳이 눈에 띄게 한다(어두운 teal은 다크 배경에 묻힘).
# 차트와 지도가 '동일 도메인·동일 색 스톱'을 공유하도록 한 곳에서 정의.
SHORTAGE_COLORS = ["#0F766E", "#14B8A6", "#2DD4BF", "#5EEAD4", "#99F6E4"]

# 색 스케일 도메인을 0 ~ SHORTAGE_SCALE_MAX 로 명시적으로 고정한다.
# 자동 스케일에 맡기면 데이터가 갱신될 때 최댓값이 바뀌어 '같은 색=같은 의미'가
# 흔들리므로 상수로 못박는다. 현재 최댓값은 송파구의 14.
# → 향후 14보다 큰 값이 유입되면 이 상수를 수동으로 상향 조정할 것.
SHORTAGE_SCALE_MAX = 14

# ── 공유/SNS 메타 설정 ────────────────────────────────────────────────────────
# 배포 후 채우면 더 정확해진다(미설정이어도 동작):
#  · SITE_URL    : 공개 https URL → og:url, 공유 버튼의 기본 URL
#  · OG_IMAGE_URL: 1200×630 절대 URL → 채우면 twitter:card가 summary_large_image로 자동 전환
SITE_URL = "https://bw-korea.streamlit.app"
OG_IMAGE_URL = ""
OG_TITLE = "BallotWatch Korea — 6·3 지방선거 투표용지 부족 현황"
OG_DESCRIPTION = (
    "전국 14,288개 투표소 중 50개소 용지 부족, 22개소 투표 일시 중단. "
    "공개 데이터로 분석한 비당파적 오픈소스 대시보드."
)

BASE_DIR = Path(__file__).parent

# ─────────────────────────────────────────────────────────────────────────────
# i18n
# ─────────────────────────────────────────────────────────────────────────────
TEXTS = {
    "ko": {
        "language_label": "Language",
        "lang_ko": "한국어",
        "lang_en": "English",
        "title": "BallotWatch Korea — 6·3 지방선거 투표용지 부족 현황",
        "badge_nonpartisan": "비당파적 분석",
        "hero_tagline": "공개 데이터로 2026년 6·3 지방선거 투표용지 부족 사태를 분석하는 비영리·오픈소스 프로젝트",
        "hero_summary": "전체 {total}개 투표소 중 <strong>{s}개소({s_pct}%)</strong>에서 투표용지가 부족했고, 그중 <strong>{w}개소</strong>에서 투표가 일시 중단되었습니다.",
        "verifiable": "공개 데이터와 공개 소스코드로 누구나 직접 검증할 수 있습니다.",
        "disclaimer": "이 프로젝트는 부정선거, 선거의 정당성, 정당 간 유불리에 대해 어떤 주장도 하지 않습니다. 공식 데이터로 공개 보도된 사실만 기록합니다.",
        "as_of_label": "데이터 기준일",
        "tab_overview": "현황 대시보드",
        "tab_map": "지도",
        "tab_timeline": "타임라인 & 출처",
        "metric_total_stations": "전체 투표소",
        "metric_shortage": "용지 부족 투표소",
        "metric_wait": "투표 일시 중단 투표소",
        "cap_total": "6·3 지방선거 전국 투표소 (선관위 발표)",
        "of_total": "전체의 {pct}%",
        "chart_title": "구별 용지 부족 투표소 수",
        "chart_caption": "구·군별 용지 부족 투표소 수 (내림차순) · 단위: 개소 · 출처: 중앙선관위 {as_of} 발표",
        "axis_district": "구·군",
        "axis_shortage": "용지 부족 투표소 (개소)",
        "raw_data": "원본 데이터",
        "map_title": "구별 용지 부족·투표 일시 중단 지도",
        "map_legend": "원 크기·색 농도 = 용지 부족 규모 · 굵은 테두리 = 투표 일시 중단 발생 · 출처: 중앙선관위 {as_of} 발표",
        "popup_shortage": "부족",
        "popup_wait": "중단",
        "popup_unit": "곳",
        "col_region": "광역시·도",
        "col_district": "구·군",
        "col_shortage": "부족 투표소",
        "col_wait": "투표 일시 중단",
        "validation_error": "데이터 합계 불일치: {details}. 출처 확인 필요.",
        "validation_shortage": "shortage 기대 {expected}, 실제 {actual}",
        "validation_wait": "wait 기대 {expected}, 실제 {actual}",
        "footer": "출처: 중앙선거관리위원회 {as_of} 발표 (구 단위 집계) · 비당파적 분석으로 부정선거를 주장하지 않습니다.",
        "faq_title": "❓ 자주 묻는 질문 (FAQ)",
        "faq_q1": "부정선거를 주장하는 프로젝트인가요?",
        "faq_a1": "아니요. 부정선거나 선거의 정당성에 대해 어떤 주장도 하지 않습니다. 행정상 용지 배분 문제로 공개 보도된 사실만 기록합니다.",
        "faq_q2": "특정 정당에 유리하거나 불리한 분석인가요?",
        "faq_a2": "아니요. 정당 간 유불리를 평가하지 않으며, 투표소 접근성이라는 행정 지표만 다룹니다.",
        "faq_q3": "데이터 출처는 어디인가요?",
        "faq_a3": "중앙선거관리위원회의 2026년 6월 5일 공식 발표(구 단위 집계)입니다.",
        "timeline_notice": "외부 기사는 각 언론사에 저작권이 있어 링크와 짧은 요약만 제공합니다. 게재된 기사가 이 프로젝트의 입장을 의미하지 않습니다.",
        "timeline_title": "사건 타임라인",
        "cause_title": "원인 요약",
        "cause_summary": "선관위는 폐기·보관·탈취 위험 등을 이유로 지방선거 투표용지를 선거인 수 50% 기준으로 감축 인쇄했고, 투표소별 사전투표율 편차와 부족 시 이송 절차를 충분히 반영하지 못해 부족이 발생했다고 설명했습니다.",
        "sources_title": "검증된 출처",
        "src_cat_domestic": "국내 보도",
        "src_cat_international": "국제 보도",
        "src_cat_primary": "1차 출처",
        "src_url_pending": "URL 확인 예정",
        "nav_where": "어디서",
        "nav_scale": "규모",
        "nav_how": "전개",
        "nav_evidence": "근거",
        "nav_data": "데이터",
        "nav_about": "소개",
        "kicker_glance": "한눈에",
        "kicker_where": "어디서",
        "kicker_scale": "규모",
        "kicker_how": "전개",
        "kicker_evidence": "근거",
        "map_desc": "용지 부족·투표 일시 중단이 발생한 구를 지도에 표시했습니다. 원이 클수록·밝을수록 부족 규모가 크고, 흰 굵은 테두리는 투표가 일시 중단된 구입니다.",
        "chart_desc": "구·군별 용지 부족 투표소 수를 많은 순으로 정렬했습니다. 서울 송파구가 가장 많았습니다.",
        "how_title": "어떻게 전개됐나",
        "how_desc": "본투표일부터 선관위 사과·진상규명위 구성까지의 경과와, 선관위가 밝힌 부족 발생 원인입니다.",
        "sources_desc": "위 내용을 뒷받침하는 국내·국제 보도와 1차 출처입니다. 외부 기사는 링크와 짧은 요약만 제공합니다.",
        "share_title": "공유하기",
        "share_copy": "링크 복사",
        "share_copied": "복사됨!",
        "share_x": "X(트위터)",
        "share_fb": "페이스북",
        "share_text": "BallotWatch Korea — 6·3 지방선거 투표용지 부족 현황",
        "about": """이 프로젝트는 부정선거, 선거의 정당성, 정당 간 유불리에 대해 어떤 주장도 하지 않으며,
공식 데이터로 공개 보도된 사실만 기록합니다.

BallotWatch Korea는 2026년 6·3 지방선거 당일 발생한 투표용지 부족 사태를
공개 데이터로 분석하는 비영리·오픈소스 프로젝트입니다.
선거관리위원회 공식 발표 자료를 바탕으로 행정상의 용지 배분 실패가
유권자 접근성에 미친 영향을 정량화하는 것을 목표로 합니다.

· 데이터 출처: 중앙선거관리위원회 2026년 6월 5일 공식 발표 (구 단위 집계)
· 규모: 전체 14,288개 투표소 중 50개소 용지 부족, 22개소 투표 일시 중단 (선관위 발표상 '투표 중지 후 재개')
· 검증: 공개 데이터와 공개 소스코드로 누구나 재현·검증할 수 있습니다.
· 한계: 선관위가 구 단위까지만 공개해 개별 투표소 분석은 불가능하며,
  투표소별 지연 시간과 투표를 포기한 유권자 수에 대한 공식 집계는 존재하지 않습니다.""",
        "nav_learn": "알아보기",
        "learn_kicker": "알아보기 / LEARN",
        "learn_title": "참정권 알아보기",
        "learn_intro": "아래는 선거권에 대한 교육 목적의 일반 정보로, 헌법·법령 등 공식 자료에 근거합니다. 특정 정당이나 이번 사건에 대한 평가가 아닙니다.",
        "learn_sources": "출처: 대한민국 헌법 · 국가법령정보센터 · 국가기록원",
        # (제목, 본문) — 본문은 그대로, 불릿은 한 줄씩 보이도록 마크다운 하드 개행 사용
        "learn_items": [
            (
                "참정권과 선거권",
                "참정권은 국민이 국가 정치에 참여할 권리이고, 그 핵심이 선거권입니다. "
                "헌법 제24조는 \"모든 국민은 법률이 정하는 바에 의하여 선거권을 가진다\"고 "
                "규정합니다. 헌법 제41조 제1항과 제67조 제1항은 국회의원·대통령 선거에서 "
                "보통·평등·직접·비밀선거의 원칙을 보장합니다.\n\n"
                "· 보통선거: 일정 연령 이상이면 재산·성별·학력과 무관하게 누구나  \n"
                "· 평등선거: 모든 유권자에게 1인 1표, 표의 가치가 평등  \n"
                "· 직접선거: 유권자가 대표자를 직접 선출  \n"
                "· 비밀선거: 누구에게 투표했는지 공개되지 않음",
            ),
            (
                "선거권 연령의 변천",
                "· 1948년 제헌 국회의원 선거: 만 21세  \n"
                "· 1960년: 만 20세로 하향  \n"
                "· 2005년: 만 19세로 하향  \n"
                "· 2019년 공직선거법 개정 → 2020년 제21대 총선부터 만 18세 적용",
            ),
            (
                "투표는 어떻게 진행되나",
                "유권자는 사전투표와 선거일 본투표 중 선택해 투표할 수 있습니다. 투표용지는 "
                "선거 전에 인쇄되어 각 투표소로 배부되며, 투표소별로 필요한 수량을 적절히 "
                "준비·배분하는 것이 원활한 투표 진행의 전제입니다.",
            ),
        ],
    },
    "en": {
        "language_label": "Language",
        "lang_ko": "한국어",
        "lang_en": "English",
        "title": "BallotWatch Korea — Jun 3 Local Election Ballot Shortage",
        "badge_nonpartisan": "Non-partisan analysis",
        "hero_tagline": "A non-profit, open-source project analyzing the ballot-paper shortage during South Korea's June 3, 2026 local elections, using public data.",
        "hero_summary": "Of {total} polling stations, <strong>{s} ({s_pct}%)</strong> ran short of ballots — and <strong>{w} of those</strong> had voting temporarily suspended.",
        "verifiable": "Anyone can independently verify this using public data and open-source code.",
        "disclaimer": "This project makes no claim about election fraud, the legitimacy of the election, or partisan advantage. It records only facts publicly reported from official data.",
        "as_of_label": "Data as of",
        "tab_overview": "Overview",
        "tab_map": "Map",
        "tab_timeline": "Timeline & Sources",
        "metric_total_stations": "Total Polling Stations",
        "metric_shortage": "Stations with Ballot Shortage",
        "metric_wait": "Stations Temporarily Suspended",
        "cap_total": "Polling stations nationwide (NEC release)",
        "of_total": "{pct}% of all stations",
        "chart_title": "Ballot Shortage by District",
        "chart_caption": "Stations with ballot shortage by district (descending) · Source: NEC release, {as_of}",
        "axis_district": "District",
        "axis_shortage": "Stations with ballot shortage",
        "raw_data": "Source Data",
        "map_title": "District Ballot Shortage & Suspension Status",
        "map_legend": "Circle size & shade = shortage magnitude · Thick outline = voting temporarily suspended · Source: NEC release, {as_of}",
        "popup_shortage": "Shortage",
        "popup_wait": "Suspended",
        "popup_unit": "",
        "col_region": "Region",
        "col_district": "District",
        "col_shortage": "Shortage Stations",
        "col_wait": "Temporarily Suspended",
        "validation_error": "Data total mismatch: {details}. Please verify the source.",
        "validation_shortage": "shortage expected {expected}, got {actual}",
        "validation_wait": "wait expected {expected}, got {actual}",
        "footer": "Source: National Election Commission release, {as_of} (district-level) · A non-partisan analysis; it does not allege election fraud.",
        "faq_title": "❓ Frequently Asked Questions (FAQ)",
        "faq_q1": "Is this a project alleging election fraud?",
        "faq_a1": "No. It makes no claim about fraud or the legitimacy of the election. It records only publicly reported facts about an administrative ballot-allocation problem.",
        "faq_q2": "Is this analysis favorable or unfavorable to a particular party?",
        "faq_a2": "No. It does not assess partisan advantage; it covers only an administrative measure — polling-station access.",
        "faq_q3": "Where does the data come from?",
        "faq_a3": "The National Election Commission's official release of June 5, 2026 (district-level aggregation).",
        "timeline_notice": "External articles are owned by their publishers; only links and short summaries are provided. Their inclusion does not imply this project's stance.",
        "timeline_title": "Event timeline",
        "cause_title": "What caused it",
        "cause_summary": "The NEC said it printed local-election ballots at a reduced 50% baseline of registered voters (citing disposal/storage/theft risks), and that it failed to account for per-station early-voting variation and lacked clear procedures to redistribute ballots when shortages occurred.",
        "sources_title": "Verified sources",
        "src_cat_domestic": "Domestic coverage",
        "src_cat_international": "International coverage",
        "src_cat_primary": "Primary source",
        "src_url_pending": "URL pending",
        "nav_where": "Where",
        "nav_scale": "Scale",
        "nav_how": "Timeline",
        "nav_evidence": "Sources",
        "nav_data": "Data",
        "nav_about": "About",
        "kicker_glance": "At a glance",
        "kicker_where": "Where",
        "kicker_scale": "Scale",
        "kicker_how": "How",
        "kicker_evidence": "Evidence",
        "map_desc": "Districts where ballots ran short or voting was temporarily suspended. Larger, brighter circles mean a bigger shortage; a thick white outline marks districts where voting was suspended.",
        "chart_desc": "Stations with ballot shortages per district, sorted high to low. Seoul's Songpa-gu had the most.",
        "how_title": "How it unfolded",
        "how_desc": "From election day to the NEC's apology and fact-finding committee — and the cause the NEC gave for the shortage.",
        "sources_desc": "Domestic and international coverage and the primary source behind the above. External articles are provided as links with short summaries only.",
        "share_title": "Share",
        "share_copy": "Copy link",
        "share_copied": "Copied!",
        "share_x": "X (Twitter)",
        "share_fb": "Facebook",
        "share_text": "BallotWatch Korea — Jun 3 local election ballot shortage",
        "about": """This project makes no claim about election fraud, the legitimacy of the
election, or partisan advantage. It records only facts publicly reported from
official data.

BallotWatch Korea is a non-profit, open-source project analyzing the
ballot-paper shortage during South Korea's June 3, 2026 local elections,
using public data. Based on official National Election Commission data,
it quantifies how an administrative ballot-allocation failure affected
voter access.

· Source: National Election Commission, official release of June 5, 2026 (district-level)
· Scale: 50 of 14,288 polling stations had shortages; 22 had voting temporarily suspended (the NEC's official wording: 'voting suspended, then resumed')
· Verifiability: reproducible and verifiable by anyone from public data and open-source code
· Limitations: Data is only public at the district level; there is no official
  count of per-station delay times or of voters who gave up without voting.""",
        "nav_learn": "Learn",
        "learn_kicker": "알아보기 / LEARN",
        "learn_title": "Understanding the Right to Vote",
        "learn_intro": "The following is general, educational information about the right to vote, based on official sources such as the Constitution and statutes. It is not an assessment of any political party or of this incident.",
        "learn_sources": "Sources: Constitution of the Republic of Korea · Korea Law Information Center · National Archives of Korea",
        # (title, body) — faithful, neutral translation; no added interpretation
        "learn_items": [
            (
                "Suffrage and the right to vote",
                "Suffrage is the right of citizens to participate in the politics of the "
                "state, and its core is the right to vote. Article 24 of the Constitution "
                "provides that \"All citizens shall have the right to vote under the "
                "conditions as prescribed by Act.\" Article 41(1) and Article 67(1) of the "
                "Constitution guarantee the principles of universal, equal, direct, and "
                "secret elections for National Assembly and presidential elections.\n\n"
                "· Universal suffrage: anyone above a certain age, regardless of property, sex, or education  \n"
                "· Equal suffrage: one vote per voter, with each vote of equal weight  \n"
                "· Direct election: voters elect their representatives directly  \n"
                "· Secret ballot: whom a person voted for is not disclosed",
            ),
            (
                "Changes in the voting age",
                "· 1948 first National Assembly election: age 21  \n"
                "· 1960: lowered to age 20  \n"
                "· 2005: lowered to age 19  \n"
                "· 2019 amendment to the Public Official Election Act → age 18 applied from the 21st general election in 2020",
            ),
            (
                "How voting is conducted",
                "Voters may choose to vote either during early voting or in the main vote "
                "on election day. Ballots are printed before the election and distributed to "
                "each polling station, and appropriately preparing and allocating the "
                "quantity needed at each station is a prerequisite for voting to proceed smoothly.",
            ),
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# OG/Twitter 메타태그 주입
# ─────────────────────────────────────────────────────────────────────────────
# [한계] SNS 크롤러(카톡/트위터/페북)는 JS를 실행하지 않고 서버가 내려주는 정적
# index.html의 <head>만 읽는다. st.markdown/components.html 주입은 미리보기에 잡히지
# 않으므로, streamlit 패키지의 static/index.html <head>에 직접 메타태그를 끼워 넣는다.
#  · idempotent(마커로 중복 방지), 쓰기 권한 없으면 조용히 통과.
#  · site-packages 파일을 수정 → 재배포/재설치 시 사라지며, 크롤러가 오기 전에 실제
#    방문 1회(warm-up)가 있어야 반영된다. 플랫폼별 OG 캐시는 각 디버거로 갱신.
def inject_og_tags():
    idx = Path(st.__file__).parent / "static" / "index.html"
    try:
        doc = idx.read_text(encoding="utf-8")
    except OSError:
        return
    if "<!-- bw-og -->" in doc:  # 이미 주입됨
        return

    def esc(s: str) -> str:
        return _html.escape(s, quote=True)

    # 이미지가 있으면 큰 카드, 없으면 텍스트 카드(summary)
    twitter_card = "summary_large_image" if OG_IMAGE_URL else "summary"
    tags = [
        "<!-- bw-og -->",
        '<meta property="og:type" content="website" />',
        '<meta property="og:locale" content="ko_KR" />',
        f'<meta property="og:title" content="{esc(OG_TITLE)}" />',
        f'<meta property="og:description" content="{esc(OG_DESCRIPTION)}" />',
        f'<meta name="twitter:card" content="{twitter_card}" />',
        f'<meta name="twitter:title" content="{esc(OG_TITLE)}" />',
        f'<meta name="twitter:description" content="{esc(OG_DESCRIPTION)}" />',
    ]
    if SITE_URL:
        tags.append(f'<meta property="og:url" content="{esc(SITE_URL)}" />')
    if OG_IMAGE_URL:
        tags.append(f'<meta property="og:image" content="{esc(OG_IMAGE_URL)}" />')
        tags.append(f'<meta name="twitter:image" content="{esc(OG_IMAGE_URL)}" />')

    block = "\n    " + "\n    ".join(tags) + "\n  "
    doc = doc.replace("</head>", block + "</head>", 1)
    # 크롤러가 og:title 외에 <title>도 보므로 함께 교체
    doc = doc.replace("<title>Streamlit</title>", f"<title>{esc(OG_TITLE)}</title>", 1)
    try:
        idx.write_text(doc, encoding="utf-8")
    except OSError:
        pass


inject_og_tags()

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정 — 반드시 첫 Streamlit 호출이어야 함
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BallotWatch Korea",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 디자인 시스템 (CSS 변수 + 다크모드 대응) ──────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

    /*
     * 테마 주의: 앱 테마를 config.toml의 [theme] base="dark" 로 '다크 고정'했다.
     * 라이트/`@media (prefers-color-scheme)` 분기를 다시 추가하지 말 것
     * (OS 테마와 무관하게 항상 다크로 동작해야 함).
     * 글자색은 계속 하드코딩하지 않고 Streamlit 본문색(textColor)을 '상속'시킨다.
     * 카드 배경/보더는 테마 무관 반투명 중립값을 유지한다.
     */
    :root {
        --space-1: 4px;
        --space-2: 8px;
        --space-3: 16px;
        --space-4: 24px;
        --accent: #2DD4BF;          /* teal-400 — 다크에서 잘 보이는 UI 액센트(탭/포커스/링크/뱃지 배경) */
        /* 카드 chrome: 라이트 위엔 살짝 어둡게, 다크 위엔 살짝 밝게 깔리는 중립 반투명 */
        --bg-card: rgba(128, 128, 128, 0.08);
        --border: rgba(128, 128, 128, 0.28);
        --shadow: 0 1px 2px rgba(0, 0, 0, .10), 0 1px 3px rgba(0, 0, 0, .06);
        /* 텍스트 토큰: 값은 Streamlit 본문색 '상속'에 매핑(테마 무관 안전).
           나중에 가독성 미세조정이 필요하면 여기 값만 바꾸면 된다. */
        --text-strong: inherit;     /* 제목·숫자용 */
        --text-base: inherit;       /* 본문용 */
    }

    html, body, [class*="css"], [data-testid="stMarkdownContainer"] {
        font-family: 'Pretendard', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
    }

    /* 카드형 메트릭 */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: var(--space-3);
        box-shadow: var(--shadow);
    }
    /* 메트릭 라벨/값: Streamlit 기본 색에 덮이지 않게 본문색을 끌어와 양 테마에서 또렷하게 */
    [data-testid="stMetricValue"] { color: inherit !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: inherit !important; opacity: 0.85; }

    /* 히어로 */
    .bw-hero {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: var(--space-4);
        margin-bottom: var(--space-4);
        background: var(--bg-card);
        box-shadow: var(--shadow);
    }
    /* 뱃지: 자체 완결형(solid 밝은 teal + 어두운 글자) → 카드/테마와 무관하게 AA 대비 확보 */
    .bw-badge {
        display: inline-block;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: .01em;
        color: #0F172A;
        background: var(--accent);
        border-radius: 999px;
        padding: var(--space-1) calc(var(--space-2) + 2px);
        margin-bottom: var(--space-3);
    }
    .bw-title {
        color: var(--text-strong);          /* = 상속(Streamlit 본문색) */
        font-size: clamp(1.4rem, 2.6vw, 2.1rem);
        font-weight: 700;
        line-height: 1.25;
        margin: 0 0 var(--space-2) 0;
    }
    .bw-tagline {
        color: var(--text-base);            /* = 상속 */
        opacity: 0.75;                      /* 고정 회색 대신 불투명도로 muted (테마 무관) */
        font-size: 1rem;
        margin: 0 0 var(--space-3) 0;
    }
    .bw-summary {
        color: var(--text-base);            /* = 상속 */
        font-size: clamp(1rem, 1.6vw, 1.15rem);
        margin: 0 0 var(--space-2) 0;
    }
    /* 강조 숫자: 어느 배경에서도 AA 보장 위해 teal 대신 굵은 본문색(상속) 사용 */
    .bw-summary strong { color: var(--text-strong); font-weight: 700; }
    .bw-asof {
        color: var(--text-base);            /* = 상속 */
        opacity: 0.7;
        font-size: 0.85rem;
        margin: 0;
    }

    /* 히어로: 검증 가능 안내 한 줄 */
    .bw-verify { color: var(--text-base); opacity: 0.75; font-size: 0.85rem; margin: 0 0 var(--space-1) 0; }

    /* 일반 카드(원인 요약 등) */
    .bw-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: var(--space-3);
        box-shadow: var(--shadow);
        line-height: 1.6;
    }

    /* 타임라인 항목 */
    .bw-tl {
        display: flex;
        gap: var(--space-3);
        padding: var(--space-2) 0;
        border-bottom: 1px solid var(--border);
    }
    .bw-tl-date {
        flex: 0 0 7.5rem;
        font-weight: 700;
        color: var(--accent);
        white-space: nowrap;
    }
    .bw-tl-text { color: var(--text-base); line-height: 1.55; }

    /* 출처 항목 */
    .bw-src {
        padding: var(--space-2) 0;
        border-bottom: 1px solid var(--border);
    }
    .bw-src-meta { color: var(--text-base); opacity: 0.7; font-size: 0.8rem; }
    .bw-src-title a { color: var(--accent); font-weight: 600; text-decoration: none; }
    .bw-src-title a:hover { text-decoration: underline; }
    .bw-src-sum { color: var(--text-base); opacity: 0.9; font-size: 0.9rem; }
    .bw-pending {
        font-size: 0.72rem;
        opacity: 0.7;
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1px 6px;
        margin-left: var(--space-1);
    }

    /* 앵커 점프 시 상단 잘림 방지 */
    [id] { scroll-margin-top: 3.5rem; }

    /* 목차(TOC) — 히어로 아래 컴팩트 앵커 내비 */
    .bw-toc {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
        margin: var(--space-3) 0 var(--space-4);
    }
    .bw-toc a {
        font-size: 0.82rem;
        color: var(--text-base);
        opacity: 0.85;
        text-decoration: none;
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 4px 12px;
    }
    .bw-toc a:hover { color: var(--accent); border-color: var(--accent); opacity: 1; }

    /* 섹션 헤더 — 작은 kicker 라벨 + 제목 + 설명 (일관 리듬) */
    .bw-sec { margin: 0 0 var(--space-3); }
    .bw-kicker {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: var(--space-1);
    }
    .bw-sec-title {
        color: var(--text-strong);
        font-size: clamp(1.15rem, 2vw, 1.5rem);
        font-weight: 700;
        line-height: 1.3;
        margin: 0 0 var(--space-1);
    }
    .bw-sec-desc {
        color: var(--text-base);
        opacity: 0.8;
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0;
    }

    /* 접근성: 키보드 포커스 가시화 */
    a:focus-visible, button:focus-visible, [tabindex]:focus-visible,
    [data-baseweb] :focus-visible {
        outline: 2px solid var(--accent) !important;
        outline-offset: 2px;
    }
</style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 데이터 로딩 (캐싱) + 합계 검증
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "ballot_shortage_2026.csv", encoding="utf-8")
    df_geo = pd.read_csv(BASE_DIR / "ballot_shortage_geo.csv", encoding="utf-8")
    return df, df_geo


# 타임라인/출처는 코드와 분리한 CSV에서 로드 — 비개발자도 파일만 갱신하면 됨.
# 파일이 없으면 빈 표를 돌려줘 앱이 죽지 않게 한다.
# (작은 파일이라 캐시 미사용: CSV를 고치면 다음 rerun에 바로 반영된다.)
def load_timeline():
    try:
        return pd.read_csv(BASE_DIR / "timeline.csv", encoding="utf-8")
    except FileNotFoundError:
        return pd.DataFrame(columns=["date_ko", "date_en", "text_ko", "text_en"])


def load_sources():
    cols = ["category", "outlet", "date", "url", "title", "summary_ko", "summary_en"]
    try:
        s = pd.read_csv(BASE_DIR / "sources.csv", encoding="utf-8")
        s["url"] = s["url"].fillna("")  # 1차 출처 등 URL 미정 행은 빈칸으로
        return s
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)


df, df_geo = load_data()
df_timeline = load_timeline()
df_sources = load_sources()

# 데이터 합계는 코드로 계산(하드코딩 금지)
shortage_total = int(df["shortage_stations"].sum())
wait_total = int(df["wait_stations"].sum())
shortage_pct = shortage_total / TOTAL_STATIONS * 100
wait_pct = wait_total / TOTAL_STATIONS * 100

# ─────────────────────────────────────────────────────────────────────────────
# 사이드바 / 언어
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    lang_choice = st.radio(
        TEXTS["ko"]["language_label"],
        options=[TEXTS["ko"]["lang_ko"], TEXTS["ko"]["lang_en"]],
    )

lang = "ko" if lang_choice == TEXTS["ko"]["lang_ko"] else "en"
t = TEXTS[lang]

# 합계가 선관위 발표치와 어긋나면 기대값·실제값을 함께 경고로 노출
_validation = []
if shortage_total != EXPECTED_SHORTAGE:
    _validation.append(
        t["validation_shortage"].format(expected=EXPECTED_SHORTAGE, actual=shortage_total)
    )
if wait_total != EXPECTED_WAIT:
    _validation.append(
        t["validation_wait"].format(expected=EXPECTED_WAIT, actual=wait_total)
    )
if _validation:
    st.warning(t["validation_error"].format(details="; ".join(_validation)))

COLUMN_RENAME = {
    "region": t["col_region"],
    "district": t["col_district"],
    "shortage_stations": t["col_shortage"],
    "wait_stations": t["col_wait"],
}


def format_popup(district: str, shortage: int, wait: int) -> str:
    if lang == "ko":
        text = f"{district} / {t['popup_shortage']} {shortage}{t['popup_unit']} / {t['popup_wait']} {wait}{t['popup_unit']}"
    else:
        text = f"{district} / {t['popup_shortage']}: {shortage} / {t['popup_wait']}: {wait}"
    # white-space:nowrap 로 감싸 folium 팝업의 한 글자씩 세로 쪼개짐을 방지
    return (
        "<div style=\"white-space:nowrap; "
        "font-family:'Pretendard','Noto Sans KR',system-ui,sans-serif; "
        f"font-size:0.9rem;\">{text}</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 섹션 렌더 함수 (탭 제거 → 단일 스크롤 내러티브)
# ─────────────────────────────────────────────────────────────────────────────
def section_header(anchor: str, kicker: str, title: str, desc: str | None = None):
    """작은 kicker 라벨 + 제목 + 설명을 일관 스타일로 출력하고 앵커 id를 부여."""
    desc_html = f'<p class="bw-sec-desc">{desc}</p>' if desc else ""
    st.markdown(
        f'<div class="bw-sec" id="{anchor}">'
        f'<div class="bw-kicker">{kicker}</div>'
        f'<h2 class="bw-sec-title">{title}</h2>'
        f"{desc_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        f"""
        <div class="bw-hero">
            <span class="bw-badge">● {t['badge_nonpartisan']}</span>
            <h1 class="bw-title">{t['title']}</h1>
            <p class="bw-tagline">{t['hero_tagline']}</p>
            <p class="bw-summary">{t['hero_summary'].format(
                total=f"{TOTAL_STATIONS:,}",
                s=f"{shortage_total:,}", s_pct=f"{shortage_pct:.2f}",
                w=f"{wait_total:,}", w_pct=f"{wait_pct:.2f}",
            )}</p>
            <p class="bw-verify">✓ {t['verifiable']}</p>
            <p class="bw-asof">{t['as_of_label']}: {DATA_AS_OF}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_toc():
    items = [
        ("where", t["nav_where"]),
        ("scale", t["nav_scale"]),
        ("how", t["nav_how"]),
        ("evidence", t["nav_evidence"]),
        ("data", t["nav_data"]),
        ("about", t["nav_about"]),
        ("learn", t["nav_learn"]),
    ]
    links = " ".join(f'<a href="#{a}">{label}</a>' for a, label in items)
    st.markdown(f'<nav class="bw-toc">{links}</nav>', unsafe_allow_html=True)


def render_share():
    """공유 영역 — 링크 복사 / X(트위터) / 페이스북. teal 통일.
    iframe(components.html)이라 앱 CSS 변수를 못 쓰므로 teal 색을 인라인으로 둔다.
    URL은 SITE_URL(설정 시) → 부모창 위치 → referrer 순으로 결정한다."""
    site_url = json.dumps(SITE_URL)
    share_text = json.dumps(t["share_text"])
    label_copy = json.dumps(t["share_copy"])
    label_copied = json.dumps(t["share_copied"])
    btn_base = (
        "padding:6px 14px;border-radius:999px;font-size:0.85rem;font-weight:600;"
        "font-family:'Pretendard','Noto Sans KR',system-ui,sans-serif;"
        "cursor:pointer;text-decoration:none;display:inline-block;line-height:1.4;"
    )
    solid = f"{btn_base}background:#2DD4BF;color:#0F172A;border:none;"
    outline = f"{btn_base}background:transparent;color:#2DD4BF;border:1px solid #2DD4BF;"
    components.html(
        f"""
        <div style="font-family:'Pretendard','Noto Sans KR',system-ui,sans-serif;">
          <div style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;
                      text-transform:uppercase;color:#2DD4BF;margin-bottom:8px;">
            {_html.escape(t['share_title'])}
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;">
            <button id="bwCopy" style="{solid}"></button>
            <a id="bwX" href="#" target="_blank" rel="noopener" style="{outline}">{_html.escape(t['share_x'])}</a>
            <a id="bwFb" href="#" target="_blank" rel="noopener" style="{outline}">{_html.escape(t['share_fb'])}</a>
          </div>
        </div>
        <script>
          let url = {site_url};
          if (!url) {{ try {{ url = window.parent.location.href; }} catch (e) {{ url = document.referrer || ""; }} }}
          if (!url) url = window.location.href;
          const text = {share_text};
          const enc = encodeURIComponent;
          document.getElementById("bwX").href =
            "https://twitter.com/intent/tweet?text=" + enc(text) + "&url=" + enc(url);
          document.getElementById("bwFb").href =
            "https://www.facebook.com/sharer/sharer.php?u=" + enc(url);
          const btn = document.getElementById("bwCopy");
          btn.textContent = {label_copy};
          btn.addEventListener("click", async () => {{
            try {{
              await navigator.clipboard.writeText(url);
              btn.textContent = {label_copied};
              setTimeout(() => {{ btn.textContent = {label_copy}; }}, 1500);
            }} catch (e) {{ window.prompt("URL", url); }}
          }});
        </script>
        """,
        height=78,
    )


def render_metrics():
    st.markdown(f'<div class="bw-kicker">{t["kicker_glance"]}</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t["metric_total_stations"], f"{TOTAL_STATIONS:,}")
        st.caption(t["cap_total"])
    with col2:
        st.metric(t["metric_shortage"], f"{shortage_total:,}")
        st.caption(t["of_total"].format(pct=f"{shortage_pct:.2f}"))
    with col3:
        st.metric(t["metric_wait"], f"{wait_total:,}")
        st.caption(t["of_total"].format(pct=f"{wait_pct:.2f}"))


def render_map():
    section_header("where", t["kicker_where"], t["map_title"], t["map_desc"])
    # shortage 규모를 색 농도(0~SHORTAGE_SCALE_MAX 고정 도메인)로 인코딩 — 차트와 동일 스톱
    shortage_cmap = bcm.LinearColormap(colors=SHORTAGE_COLORS, vmin=0, vmax=SHORTAGE_SCALE_MAX)
    # 다크 UI에 맞춰 어두운 타일 사용 → 그 위에서 teal 마커가 잘 보인다.
    m = folium.Map(location=[36.5, 127.8], zoom_start=7, tiles="CartoDB dark_matter")
    for _, row in df_geo.iterrows():
        shortage = int(row["shortage_stations"])
        wait = int(row["wait_stations"])
        has_wait = wait >= 1
        fill = shortage_cmap(min(shortage, SHORTAGE_SCALE_MAX))
        popup_text = format_popup(row["district"], shortage, wait)
        CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5 + shortage * 1.3,
            # 색에는 shortage 한 변수만 인코딩. wait는 테두리 굵기로 별도 인코딩.
            color=WAIT_OUTLINE if has_wait else fill,
            weight=4 if has_wait else 1,
            fill=True,
            fill_color=fill,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, min_width=200, max_width=260),
        ).add_to(m)
    # 높이 고정으로 스크롤 피로 감소
    st_folium(m, height=380, use_container_width=True)
    st.caption(t["map_legend"].format(as_of=DATA_AS_OF))


def render_chart():
    section_header("scale", t["kicker_scale"], t["chart_title"], t["chart_desc"])
    # 지도 colormap과 동일한 도메인(0~SHORTAGE_SCALE_MAX)·동일 teal 스톱으로 색 의미 일치
    chart_base = alt.Chart(df).encode(
        y=alt.Y("district:N", sort="-x", title=t["axis_district"]),
        # 막대 끝 수치 라벨이 잘리지 않도록 x축에 헤드룸 확보
        x=alt.X(
            "shortage_stations:Q",
            title=t["axis_shortage"],
            scale=alt.Scale(domain=[0, SHORTAGE_SCALE_MAX + 1]),
        ),
    )
    bars = chart_base.mark_bar(cornerRadius=2).encode(
        color=alt.Color(
            "shortage_stations:Q",
            scale=alt.Scale(
                domain=[0, SHORTAGE_SCALE_MAX],
                range=SHORTAGE_COLORS,  # 지도와 동일 색 스톱 (고값일수록 밝게)
                clamp=True,
            ),
            legend=None,  # x축과 중복되므로 색 범례는 숨김
        ),
        tooltip=[
            alt.Tooltip("region:N", title=t["col_region"]),
            alt.Tooltip("district:N", title=t["col_district"]),
            alt.Tooltip("shortage_stations:Q", title=t["col_shortage"]),
            alt.Tooltip("wait_stations:Q", title=t["col_wait"]),
        ],
    )
    labels = chart_base.mark_text(
        align="left", baseline="middle", dx=3, color=ACCENT
    ).encode(text=alt.Text("shortage_stations:Q"))
    # 막대 높이 축소(Step 28 → 22)로 세로 길이 절감
    chart = (bars + labels).properties(height=alt.Step(22))
    st.altair_chart(chart, use_container_width=True)
    st.caption(t["chart_caption"].format(as_of=DATA_AS_OF))


def render_timeline():
    section_header("how", t["kicker_how"], t["how_title"], t["how_desc"])
    st.caption(t["timeline_notice"])

    # 1) 사건 타임라인 — CSV의 ko/en 컬럼을 현재 언어로 렌더 (사실만, 중립)
    st.markdown(f"**{t['timeline_title']}**")
    date_col = "date_ko" if lang == "ko" else "date_en"
    text_col = "text_ko" if lang == "ko" else "text_en"
    for _, r in df_timeline.iterrows():
        st.markdown(
            f'<div class="bw-tl">'
            f'<span class="bw-tl-date">{r[date_col]}</span>'
            f'<span class="bw-tl-text">{r[text_col]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # 2) 원인 요약 박스
    st.markdown(f"**{t['cause_title']}**")
    st.markdown(f'<div class="bw-card">{t["cause_summary"]}</div>', unsafe_allow_html=True)


def render_sources():
    section_header("evidence", t["kicker_evidence"], t["sources_title"], t["sources_desc"])
    # 카테고리별. 외부 링크는 새 탭(target=_blank, rel=noopener).
    sum_col = "summary_ko" if lang == "ko" else "summary_en"
    cat_labels = {
        "domestic": t["src_cat_domestic"],
        "international": t["src_cat_international"],
        "primary": t["src_cat_primary"],
    }
    for cat in ["domestic", "international", "primary"]:
        rows = df_sources[df_sources["category"] == cat]
        if rows.empty:
            continue
        st.markdown(f"**{cat_labels[cat]}**")
        for _, s in rows.iterrows():
            url = str(s["url"]).strip()
            if url:  # 링크 있음 → 새 탭으로
                title_html = (
                    f'<a href="{url}" target="_blank" rel="noopener">{s["title"]}</a>'
                )
            else:  # 링크 없음(1차 출처 등) → 임의 링크 만들지 말고 비활성 표기
                title_html = (
                    f'{s["title"]} <span class="bw-pending">{t["src_url_pending"]}</span>'
                )
            st.markdown(
                f'<div class="bw-src">'
                f'<span class="bw-src-meta">{s["outlet"]} · {s["date"]}</span><br>'
                f'<span class="bw-src-title">{title_html}</span><br>'
                f'<span class="bw-src-sum">{s[sum_col]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )


def render_raw_data():
    st.markdown('<div id="data"></div>', unsafe_allow_html=True)
    with st.expander(t["raw_data"]):
        st.dataframe(df.rename(columns=COLUMN_RENAME), use_container_width=True)


def render_about_faq():
    st.markdown('<div id="about"></div>', unsafe_allow_html=True)
    with st.expander("ℹ️ About this project"):
        st.markdown(t["about"])
    with st.expander(t["faq_title"]):
        for _q, _a in [
            (t["faq_q1"], t["faq_a1"]),
            (t["faq_q2"], t["faq_a2"]),
            (t["faq_q3"], t["faq_a3"]),
        ]:
            st.markdown(f"**{_q}**")
            st.markdown(_a)


def render_learn():
    """푸터 직전 교육 섹션 — 사건 분석과 분리된 선거권 일반 정보 (중립·교육 목적)."""
    section_header("learn", t["learn_kicker"], t["learn_title"])
    st.caption(t["learn_intro"])
    for _title, _body in t["learn_items"]:
        with st.expander(_title, expanded=False):
            st.markdown(_body)
    st.caption(t["learn_sources"])

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 렌더: 위→아래 내러티브 (무슨 일 → 어디서 → 얼마나 → 어떻게 전개 → 근거)
# ─────────────────────────────────────────────────────────────────────────────
render_hero()
render_toc()
render_share()  # 상단 공유 영역
render_metrics()
st.divider()
render_map()       # 어디서
st.divider()
render_chart()     # 구별 규모
st.divider()
render_timeline()  # 어떻게 전개 + 원인
st.divider()
render_sources()   # 근거·출처
st.divider()
render_raw_data()  # 원본 데이터 (expander)
st.divider()
render_about_faq()  # 소개 + FAQ (expander)
st.divider()
render_learn()      # 참정권 알아보기 (교육 섹션 — 사건 분석과 분리)
st.divider()
render_share()  # 하단 공유 영역

# 상시 노출 푸터 (짧은 출처 + 중립성 한 줄) — 상세 버전은 About 참조
st.divider()
st.caption(t["footer"].format(as_of=DATA_AS_OF))
