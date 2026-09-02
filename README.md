# 세종 합강캠핑장 날씨 트렌드 분석

세종 지역(기상청 ASOS 지점 239)의 2023-01-01 ~ 2026-09-01 일별 기온·강수량 데이터를 분석하여, 캠핑하기 좋은 시기를 데이터 기반으로 확인하는 프로젝트입니다.

자세한 분석 내용과 인사이트는 [REPORT.md](REPORT.md)를 참고하세요.

## 폴더 구조

```
.
├── raw_data/
│   ├── raw_temperature.csv       # 기상청 원본 기온 데이터
│   └── raw_precipitation.csv     # 기상청 원본 강수량 데이터
├── data/
│   └── sejong_weather_clean.csv  # 정제·병합된 최종 데이터
├── images/
│   ├── 01_temp_trend.png
│   ├── 02_monthly_pattern.png
│   └── 03_camping_suitability.png
├── analysis.ipynb                # 전체 분석 코드
├── REPORT.md                     # 분석 리포트
├── requirements.txt
└── README.md
```

## 실행 방법

```bash
pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

노트북을 처음부터 순서대로 실행하면 데이터 정제 → 시계열 분석 → 시각화 → 데이터 저장까지 재현됩니다.

## 데이터 출처

- 기상청 기상자료개방포털(https://data.kma.go.kr) — 종관기상관측(ASOS) 세종 지점 일자료
- 공공데이터로, 출처를 명시하면 자유롭게 활용 가능합니다.
