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

## 색상 원칙

정당 연상색(빨강·파랑·주황) 사용 금지. 중립적 딥 틸(teal) 단색을 액센트로 사용한다.
지도/차트는 동일 도메인(0~`SHORTAGE_SCALE_MAX`)의 teal 시퀀셜 그라데이션을 공유한다.
