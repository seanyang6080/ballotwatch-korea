# BallotWatch Korea

공개 데이터로 2026년 6·3 지방선거 투표용지 부족 사태를 분석하는 비영리·오픈소스 프로젝트입니다.
선거의 정당성이나 부정 여부를 판정하지 않으며, 중앙선거관리위원회 공식 발표(2026-06-05, 구 단위 집계)를
바탕으로 행정상 용지 배분 실패가 유권자 접근성에 미친 영향을 정량화하는 것을 목표로 합니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 데이터

- `ballot_shortage_2026.csv` — 구별 집계 (region, district, shortage_stations, wait_stations)
- `ballot_shortage_geo.csv` — 위 데이터 + 위경도(lat/lon, 행정구역 대표점), 지도용
- `timeline.csv` — 사건 타임라인 (date_ko, date_en, text_ko, text_en). 코드 수정 없이 행만 추가/수정하면 됨.
- `sources.csv` — 검증된 출처 (category[domestic/international/primary], outlet, date, url, title, summary_ko, summary_en).
  `url`이 빈칸이면 화면에 "URL 확인 예정"으로 비활성 표기된다(없는 링크를 만들지 않음).
- 출처: 중앙선거관리위원회 2026-06-05 발표. 합계 검증값은 부족 50 / 투표 일시 중단 22.

## 디자인 메모 (수정 전 반드시 읽기)

> **이 앱은 OS 테마(`prefers-color-scheme`)가 아니라 Streamlit '앱 테마'(메뉴 → Settings → Theme)를 상속한다.**

`app.py`의 커스텀 CSS는 다음 원칙을 따릅니다. 어기면 다크/라이트에서 글자가 배경에 묻힙니다.

- Streamlit 1.58은 테마 색을 CSS 변수로 노출하지 **않는다**(`var(--text-color)` 등 없음).
  따라서 글자색을 하드코딩하거나 `@media (prefers-color-scheme: dark)`에 묶지 말 것.
  OS 테마와 앱 테마가 다르면(예: OS 라이트 + 앱 다크) 흰-on-흰으로 묻힌다.
- 글자색은 **Streamlit 본문색을 상속**시킨다(`--text-strong` / `--text-base`는 값이 `inherit`).
  Streamlit이 자기 배경 대비 대비를 보장하므로 양 테마에서 안전하다.
- 카드 배경/보더는 **테마 무관 반투명 중립값**(`rgba(128,128,128,…)`)을 쓴다.
- 색이 꼭 필요한 요소(뱃지)는 자체 배경을 가진 완결형(solid teal + 흰 글자)으로 만든다.

## 공유 / OG 미리보기 (SNS 카드)

SNS 크롤러(카톡·트위터·페북)는 **JS를 실행하지 않고** 서버가 내려주는 정적
`index.html`의 `<head>`만 읽는다. 그래서 `st.markdown`/`components.html`로 넣은
메타태그는 **미리보기에 잡히지 않는다**. 유일하게 동작하는 방법은 streamlit 패키지의
`static/index.html` `<head>`에 직접 메타를 끼워 넣는 것 — `app.py`의 `inject_og_tags()`가
시작 시 idempotent하게 처리한다.

- 더 정확히 하려면 `app.py` 상단 상수를 채운다: `SITE_URL`(공개 https URL),
  `OG_IMAGE_URL`(1200×630 절대 URL → 설정 시 `twitter:card`가 `summary_large_image`로 전환).
- **한계**: site-packages 파일을 수정하므로 재배포/재설치 시 사라진다(콜드스타트마다
  재주입되지만 **크롤러가 오기 전 실제 방문 1회**가 필요). 플랫폼별 OG 캐시는 각 디버거로
  갱신(페북 Sharing Debugger / 트위터 Card Validator / 카카오 재스크랩).
- 바이럴이 중요하면 리버스 프록시·Cloudflare Worker·정적 랜딩페이지에서 OG를 제공하는
  편이 더 견고하다.

공유 버튼(`render_share()`)은 클라이언트에서 완전히 동작한다: 링크 복사 / X(트위터) /
페이스북. 카카오 정식 버튼은 Kakao JS SDK 앱키가 필요해 제외했고, 링크 복사로 대체한다
(카톡은 OG가 잡히면 자동 미리보기).

## 색상 원칙

정당 연상색(빨강·파랑·주황) 사용 금지. 중립적 딥 틸(teal) 단색을 액센트로 사용한다.
지도/차트는 동일 도메인(0~`SHORTAGE_SCALE_MAX`)의 teal 시퀀셜 그라데이션을 공유한다.
