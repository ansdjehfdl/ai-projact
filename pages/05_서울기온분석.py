
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# =========================================
# 1. 페이지 설정
# =========================================

st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 분석 대시보드")
st.markdown(
    "서울의 월별 평균기온과 연도별 최고·최저기온을 분석합니다."
)

st.divider()


# =========================================
# 2. 한글 CSV 데이터 불러오기
# =========================================

@st.cache_data
def load_data(file_bytes):

    encodings = [
        "cp949",
        "euc-kr",
        "utf-8-sig",
        "utf-8"
    ]

    for encoding in encodings:
        try:
            return pd.read_csv(
                BytesIO(file_bytes),
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 인코딩을 확인해주세요.")


uploaded_file = st.file_uploader(
    "기온 데이터 CSV 업로드",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = load_data(uploaded_file.getvalue())
    else:
        with open("temperature.csv", "rb") as f:
            df = load_data(f.read())

except FileNotFoundError:
    st.error("temperature.csv 파일이 없습니다.")
    st.stop()

except Exception as e:
    st.error(f"데이터 오류: {e}")
    st.stop()


# =========================================
# 3. 데이터 전처리
# =========================================

required_columns = [
    "일시",
    "평균기온(℃)",
    "최고기온(℃)",
    "최저기온(℃)"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 컬럼 구성이 올바르지 않습니다.")
    st.stop()


month_dict = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}

# 월과 연도 분리
parts = df["일시"].astype(str).str.strip().str.split(
    "-", expand=True
)

if parts.shape[1] != 2:
    st.error("일시 데이터 형식이 올바르지 않습니다.")
    st.stop()

df["월"] = parts[0].str.title().map(month_dict)

yy = pd.to_numeric(parts[1], errors="coerce")

# =========================================
# 4. 실제 연도 복원
# =========================================

# 데이터가 시간순으로 정렬되어 있다는 전제에서
# 2자리 연도가 100년 주기로 반복되는 문제 해결

years = []
previous_serial = None

for month, year_code in zip(df["월"], yy):

    if pd.isna(month) or pd.isna(year_code):
        years.append(None)
        continue

    year = 1900 + int(year_code)

    serial = year * 12 + int(month)

    while previous_serial is not None and serial <= previous_serial:
        year += 100
        serial = year * 12 + int(month)

    years.append(year)
    previous_serial = serial

df["연도"] = years

# 숫자형으로 변환
for col in [
    "평균기온(℃)",
    "최고기온(℃)",
    "최저기온(℃)"
]:
    df[col] = pd.to_numeric(
        df[col], errors="coerce"
    )

df = df.dropna(
    subset=["연도", "월"]
).copy()

df["연도"] = df["연도"].astype(int)
df["월"] = df["월"].astype(int)

# 월 이름
month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

df["월이름"] = df["월"].map(
    lambda x: f"{x}월"
)

# =========================================
# 5. 같은 연도와 월의 중복 데이터 통합
# =========================================

# 동일한 연월 데이터가 여러 개라면 평균으로 통합
monthly_data = (
    df.groupby(["연도", "월"], as_index=False)
    .agg({
        "평균기온(℃)": "mean",
        "최고기온(℃)": "mean",
        "최저기온(℃)": "mean"
    })
)

monthly_data["월이름"] = monthly_data["월"].map(
    lambda x: f"{x}월"
)

years_list = sorted(
    monthly_data["연도"].unique().tolist()
)

if not years_list:
    st.error("분석할 데이터가 없습니다.")
    st.stop()


# =========================================
# 6. 전체 데이터 요약
# =========================================

st.subheader("📊 데이터 요약")

col1, col2, col3 = st.columns(3)

col1.metric(
    "분석 연도",
    f"{years_list[0]} ~ {years_list[-1]}"
)

col2.metric(
    "분석 데이터",
    f"{len(monthly_data):,}개월"
)

col3.metric(
    "평균기온",
    f"{monthly_data['평균기온(℃)'].mean():.1f}℃"
)

st.divider()


# =========================================
# 7. 그래프 1
# 서울 월별 평균기온
# =========================================

st.subheader("① 서울의 월별 평균기온")

# 전체 기간에서 각 월의 평균 계산
month_avg = (
    monthly_data.groupby("월")["평균기온(℃)"]
    .mean()
    .reindex(range(1, 13))
)

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=month_names,
        y=month_avg.values,
        mode="lines+markers",
        name="월별 평균기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(
            size=9,
            color="#FF1493"
        )
    )
)

fig1.update_layout(
    title="서울의 월별 평균기온",
    xaxis_title="월",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    showlegend=True
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.caption(
    "전체 데이터 기간의 동일한 월에 대한 평균기온을 계산한 그래프입니다."
)

st.divider()


# =========================================
# 8. 그래프 2
# 연도별 최고기온과 최저기온
# =========================================

st.subheader("② 연도별 최고기온 및 최저기온")

# 연도별 최고기온과 최저기온 계산
year_temp = (
    monthly_data.groupby("연도")
    .agg({
        "최고기온(℃)": "max",
        "최저기온(℃)": "min"
    })
    .reset_index()
)

fig2 = go.Figure()

# 최고기온
fig2.add_trace(
    go.Scatter(
        x=year_temp["연도"],
        y=year_temp["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=7)
    )
)

# 최저기온
fig2.add_trace(
    go.Scatter(
        x=year_temp["연도"],
        y=year_temp["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#1E90FF",
            width=3
        ),
        marker=dict(size=7)
    )
)

fig2.update_layout(
    title="연도별 최고기온 및 최저기온",
    xaxis_title="연도",
    yaxis_title="온도(℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(
        title="범례",
        orientation="h",
        y=1.12,
        x=0.5,
        xanchor="center"
    )
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.caption(
    "각 연도에 기록된 월별 최고기온 중 가장 높은 값과 "
    "월별 최저기온 중 가장 낮은 값을 표시합니다."
)

st.divider()


# =========================================
# 9. 그래프 3
# 사용자가 선택한 두 연도 비교
# =========================================

st.subheader("③ 두 연도 기온 비교")

st.write(
    "비교하고 싶은 연도 2개를 선택하면 "
    "월별 평균기온을 비교할 수 있습니다."
)

col1, col2 = st.columns(2)

year1 = col1.selectbox(
    "첫 번째 연도 선택",
    years_list,
    index=0
)

second_years = [
    y for y in years_list if y != year1
]

year2 = col2.selectbox(
    "두 번째 연도 선택",
    second_years,
    index=min(1, len(second_years)-1)
)

# 선택한 두 연도 데이터
compare_data = monthly_data[
    monthly_data["연도"].isin([year1, year2])
].copy()

fig3 = go.Figure()

# 첫 번째 연도
data1 = compare_data[
    compare_data["연도"] == year1
].sort_values("월")

fig3.add_trace(
    go.Scatter(
        x=data1["월이름"],
        y=data1["평균기온(℃)"],
        mode="lines+markers",
        name=f"{year1}년",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=8)
    )
)

# 두 번째 연도
data2 = compare_data[
    compare_data["연도"] == year2
].sort_values("월")

fig3.add_trace(
    go.Scatter(
        x=data2["월이름"],
        y=data2["평균기온(℃)"],
        mode="lines+markers",
        name=f"{year2}년",
        line=dict(
            color="#1E90FF",
            width=3
        ),
        marker=dict(size=8)
    )
)

fig3.update_layout(
    title=f"{year1}년과 {year2}년 월별 평균기온 비교",
    xaxis_title="월",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(
        title="비교 연도",
        orientation="h",
        y=1.12,
        x=0.5,
        xanchor="center"
    )
)

fig3.update_xaxes(
    categoryorder="array",
    categoryarray=month_names
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.divider()


# =========================================
# 10. 원본 분석 데이터 확인
# =========================================

with st.expander("📋 분석에 사용된 데이터 확인"):

    st.dataframe(
        monthly_data.sort_values(
            ["연도", "월"]
        ),
        use_container_width=True,
        hide_index=True
    )

    csv_data = monthly_data.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "분석 데이터 CSV 다운로드",
        data=csv_data,
        file_name="temperature_analysis.csv",
        mime="text/csv"
    )

st.caption(
    "서울 기온 분석 대시보드 | Pandas + Streamlit + Plotly"
)
