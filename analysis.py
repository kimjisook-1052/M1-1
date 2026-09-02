# %% [markdown]
# # 세종 합강캠핑장 지역 날씨 시계열 분석
#
# - 데이터 출처: 기상청 기상자료개방포털(data.kma.go.kr) ASOS 세종(지점번호 239) 일자료
# - 기간: 2023-01-01 ~ 2026-09-01 (일별, 총 1,340개 데이터 포인트)
# - 목적: 캠핑하기 좋은 시기를 데이터 기반으로 파악

# %% [markdown]
# ## 1. 라이브러리 불러오기

# %%
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (환경에 나눔고딕 등이 있으면 그것을 사용해도 됩니다)
try:
    fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'
except Exception:
    plt.rcParams['font.family'] = 'AppleGothic'  # 맥 환경 등 대체
plt.rcParams['axes.unicode_minus'] = False

# %% [markdown]
# ## 2. 원본 데이터 불러오기
#
# 기상청에서 받은 CSV는 CP949(EUC-KR) 인코딩이며, 상단에 검색조건 메타데이터가 포함되어 있어
# 헤더 위치를 직접 지정해서 읽습니다. 기온 파일은 원본 헤더에 콤마 누락으로 컬럼이 밀리는 문제가 있어
# 컬럼명을 직접 지정했습니다.

# %%
temp_cols = ['지점번호','지점명','일시','평균기온','최고기온','최고기온시각',
             '최저기온','최저기온시각','일교차']
temp = pd.read_csv('raw_data/raw_temperature.csv', encoding='cp949',
                    skiprows=12, header=None, names=temp_cols, sep=',')
temp = temp.dropna(subset=['일시'])
temp = temp[temp['일시'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')]
temp['일시'] = pd.to_datetime(temp['일시'])
for c in ['평균기온','최고기온','최저기온','일교차']:
    temp[c] = pd.to_numeric(temp[c], errors='coerce')

rain_cols = ['지점번호','지점명','일시','강수량','1시간최다강수량','1시간최다강수량시각','extra']
rain = pd.read_csv('raw_data/raw_precipitation.csv', encoding='cp949',
                    skiprows=13, header=None, names=rain_cols, sep=',')
rain = rain.dropna(subset=['일시'])
rain = rain[rain['일시'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')]
rain['일시'] = pd.to_datetime(rain['일시'])
rain['강수량'] = pd.to_numeric(rain['강수량'], errors='coerce')

print('기온 데이터:', temp.shape)
print('강수량 데이터:', rain.shape)

# %% [markdown]
# ## 3. 데이터 정제
#
# - 기온 결측치 2건(2023-02-01~02) → 선형보간
# - 강수량 결측치(비가 안 온 날) → 0mm로 처리 (기상청 관례: 강수 없음은 빈 칸으로 표기)
# - 두 데이터셋을 일시(날짜) 기준으로 병합

# %%
df = pd.merge(temp[['일시','평균기온','최고기온','최저기온','일교차']],
              rain[['일시','강수량']], on='일시', how='inner')
df['강수량'] = df['강수량'].fillna(0)

for c in ['평균기온','최고기온','최저기온','일교차']:
    df[c] = df[c].interpolate(method='linear')

df = df.sort_values('일시').reset_index(drop=True)
print('최종 데이터:', df.shape)
print('기간:', df['일시'].min().date(), '~', df['일시'].max().date())
df.isna().sum()

# %% [markdown]
# ## 4. 시계열 분석 기법 적용
#
# - **이동평균(7일/30일)**: 일별 노이즈를 줄여 계절적 추세 파악
# - **월별 집계**: 연도 구분 없이 월별 평균을 내어 계절성(seasonality) 확인
# - **캠핑 적합일 지표**: 평균기온 10~25℃ & 강수량 1mm 미만인 날을 '캠핑 적합일'로 정의

# %%
df['MA7'] = df['평균기온'].rolling(7).mean()
df['MA30'] = df['평균기온'].rolling(30).mean()
df['월'] = df['일시'].dt.month
df['연도'] = df['일시'].dt.year

df['캠핑적합'] = (df['평균기온'].between(10, 25)) & (df['강수량'] < 1)

month_avg = df.groupby('월').agg(평균기온=('평균기온','mean'),
                                  강수량평균=('강수량','mean')).reset_index()
camp_ratio = df.groupby('월')['캠핑적합'].mean().mul(100).round(1)
print(month_avg)
print()
print('월별 캠핑 적합일 비율(%)')
print(camp_ratio)

# %% [markdown]
# ## 5. 시각화 1 — 일별 평균기온 추이 + 30일 이동평균

# %%
fig, ax = plt.subplots(figsize=(12,5))
ax.plot(df['일시'], df['평균기온'], color='#a8c9e8', linewidth=0.6, label='일별 평균기온')
ax.plot(df['일시'], df['MA30'], color='#c0392b', linewidth=1.8, label='30일 이동평균')
ax.axhline(0, color='gray', linestyle=':', linewidth=0.8)
ax.set_title('세종 지역 일별 평균기온 추이 (2023-01 ~ 2026-09)', fontsize=13)
ax.set_xlabel('날짜'); ax.set_ylabel('평균기온 (℃)')
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('images/01_temp_trend.png', dpi=130)
plt.show()

# %% [markdown]
# ## 6. 시각화 2 — 월별 평균기온 & 강수량 패턴 (계절성)

# %%
fig, ax1 = plt.subplots(figsize=(10,5))
ax1.bar(month_avg['월'], month_avg['강수량평균'], color='#7fb3d5', alpha=0.7, label='일평균 강수량(mm)')
ax1.set_xlabel('월'); ax1.set_ylabel('일평균 강수량 (mm)', color='#2874a6')
ax1.set_xticks(range(1,13))
ax2 = ax1.twinx()
ax2.plot(month_avg['월'], month_avg['평균기온'], color='#c0392b', marker='o', linewidth=2, label='평균기온(℃)')
ax2.set_ylabel('평균기온 (℃)', color='#c0392b')
ax1.set_title('세종 지역 월별 평균기온 & 강수량 패턴 (계절성)', fontsize=13)
fig.legend(loc='upper left', bbox_to_anchor=(0.12,0.88))
plt.tight_layout()
plt.savefig('images/02_monthly_pattern.png', dpi=130)
plt.show()

# %% [markdown]
# ## 7. 시각화 3 — 월별 캠핑 적합일 비율

# %%
camp = df.groupby('월')['캠핑적합'].mean().reset_index()
camp.columns = ['월','적합비율']
camp['적합비율'] *= 100

fig, ax = plt.subplots(figsize=(10,5))
colors = ['#c0392b' if v<20 else '#f39c12' if v<50 else '#27ae60' for v in camp['적합비율']]
bars = ax.bar(camp['월'], camp['적합비율'], color=colors)
ax.set_xticks(range(1,13)); ax.set_xlabel('월'); ax.set_ylabel('캠핑 적합일 비율 (%)')
ax.set_title('월별 캠핑 적합일 비율\n(기준: 평균기온 10~25℃ & 강수량 1mm 미만)', fontsize=13)
for b,v in zip(bars, camp['적합비율']):
    ax.text(b.get_x()+b.get_width()/2, v+1, f'{v:.0f}%', ha='center', fontsize=9)
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('images/03_camping_suitability.png', dpi=130)
plt.show()

# %% [markdown]
# ## 8. 추가 통계 — 인사이트 근거 자료
#
# - 연도별(1~9월 기준) 평균기온 비교 → 장기 온난화 추세 여부 확인
# - 월별 평균 일교차 → 캠핑 장비(침낭 등급) 선택 참고
# - 강수량 상위 5일 및 여름철 강수 집중도

# %%
partial = df[df['월']<=9]
yearly = partial.groupby('연도')['평균기온'].mean().round(2)
print('연도별(1~9월) 평균기온:'); print(yearly)

diurnal = df.groupby('월')['일교차'].mean().round(1)
print('\n월별 평균 일교차:'); print(diurnal)

print('\n강수량 상위 5일:')
print(df.nlargest(5,'강수량')[['일시','강수량']])

rainy_days = (df['강수량']>0).sum()
print(f'\n전체 {len(df)}일 중 강수일: {rainy_days}일 ({rainy_days/len(df)*100:.1f}%)')
summer_rain = df[df['월'].isin([6,7,8])]['강수량'].sum()
total_rain = df['강수량'].sum()
print(f'여름철(6~8월) 강수량 비중: {summer_rain/total_rain*100:.1f}%')

# %% [markdown]
# ## 9. 정제된 데이터 저장

# %%
df.to_csv('data/sejong_weather_clean.csv', index=False, encoding='utf-8-sig')
print('저장 완료: data/sejong_weather_clean.csv')

# %% [markdown]
# ## 10. 결론
#
# 자세한 해석과 결론은 `REPORT.md`를 참고하세요. 요약하면:
#
# - 세종 지역은 뚜렷한 사계절 패턴을 보이며, 4~5월·10월이 캠핑에 가장 적합(적합일 비율 70%대)
# - 1월, 7~8월, 12월은 각각 혹한/장마·폭염/혹한으로 캠핑 적합일이 5% 미만
# - 여름철(6~8월)에 연간 강수량의 약 56%가 집중되어, 우천 대비가 특히 중요
# - 짧은 관측 기간(3.7년) 내에서는 뚜렷한 장기 온난화 추세는 확인되지 않음 (계절성이 지배적)
