
import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------
# 페이지 설정
# -------------------------
st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

# -------------------------
# 데이터 불러오기
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("countriesMBTI_16types.csv")
    df.columns = df.columns.str.strip()

    if "Country" not in df.columns:
        raise ValueError(
            "CSV 파일에 Country 열이 없습니다."
        )

    # MBTI 유형별 수치를 숫자로 변환
    mbti_cols = [
        col for col in df.columns
        if col != "Country"
    ]

    for col in mbti_cols:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(subset=["Country"])
    df = df.dropna(subset=mbti_cols, how="all")

    return df, mbti_cols


try:
    df, mbti_cols = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

if not mbti_cols:
    st.error("MBTI 유형 열을 찾을 수 없습니다.")
    st.stop()

# -------------------------
# 제목
# -------------------------
st.title("🌍 국가별 MBTI 분석")
st.caption(
    "국가를 선택해 16가지 MBTI 유형의 비율을 비교해 보세요."
)

st.divider()

# -------------------------
# 국가 선택
# -------------------------
countries = sorted(
    df["Country"].astype(str).unique().tolist()
)

default_country = (
    "South Korea"
    if "South Korea" in countries
    else countries[0]
)

country = st.selectbox(
    "📍 분석할 국가를 선택하세요",
    countries,
    index=countries.index(default_country)
)

# 선택한 국가의 데이터
row = df.loc[
    df["Country"].astype(str) == country,
    mbti_cols
].iloc[0]

chart_data = pd.DataFrame({
    "MBTI": mbti_cols,
    "비율": [
        row[mbti] * 100
        for mbti in mbti_cols
    ]
})

# 결측값 제거 및 내림차순 정렬
chart_data = (
    chart_data
    .dropna(subset=["비율"])
    .sort_values("비율", ascending=False)
    .reset_index(drop=True)
)

if chart_data.empty:
    st.warning("선택한 국가에 표시할 데이터가 없습니다.")
    st.stop()

# -------------------------
# 순위 및 색상 설정
# 1위 빨강, 나머지는 파랑 그라데이션
# -------------------------
chart_data["순위"] = range(1, len(chart_data) + 1)

colors = []

for rank in chart_data["순위"]:
    if rank == 1:
        colors.append("#E53935")
    else:
        # 2위는 진한 파랑, 마지막은 연한 파랑
        denominator = max(len(chart_data) - 2, 1)
        t = (rank - 2) / denominator
        t = min(max(t, 0), 1)

        # 파랑 계열: #1565C0 -> #DCEBFA
        start = (21, 101, 192)
        end = (220, 235, 250)

        rgb = tuple(
            round(start[i] + (end[i] - start[i]) * t)
            for i in range(3)
        )

        colors.append(
            "#{:02X}{:02X}{:02X}".format(*rgb)
        )

chart_data["색상"] = colors

# -------------------------
# 요약 정보
# -------------------------
top = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("선택 국가", country)
col2.metric("비율 1위 MBTI", top["MBTI"])
col3.metric("1위 비율", f'{top["비율"]:.2f}%')

st.divider()

# -------------------------
# 막대그래프
# -------------------------
st.subheader(f"📊 {country}의 MBTI 비율")

fig = px.bar(
    chart_data,
    x="MBTI",
    y="비율",
    custom_data=["순위"],
    color="MBTI",
    color_discrete_map=dict(
        zip(chart_data["MBTI"], chart_data["색상"])
    ),
    category_orders={
        "MBTI": chart_data["MBTI"].tolist()
    },
    text=chart_data["비율"].map(
        lambda x: f"{x:.2f}%"
    )
)

fig.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "비율: %{y:.2f}%<br>"
        "순위: %{customdata[0]}위"
        "<extra></extra>"
    )
)

fig.update_layout(
    showlegend=False,
    height=600,
    xaxis_title="MBTI 유형",
    yaxis_title="비율 (%)",
    yaxis_ticksuffix="%",
    yaxis_rangemode="tozero",
    margin=dict(t=35, b=40, l=30, r=30)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption(
    "색상 기준: 1위 빨간색 · 2위부터 파란색 그라데이션"
)

# -------------------------
# 상세 데이터 표
# -------------------------
with st.expander("📋 순위별 상세 데이터 보기"):
    display_data = chart_data[
        ["순위", "MBTI", "비율"]
    ].copy()

    display_data["비율"] = (
        display_data["비율"].map(
            lambda x: f"{x:.2f}%"
        )
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )

# -------------------------
# CSV 다운로드
# -------------------------
st.download_button(
    label="📥 선택 국가의 MBTI 데이터 다운로드",
    data=chart_data[
        ["순위", "MBTI", "비율"]
    ].to_csv(index=False).encode("utf-8-sig"),
    file_name=f"{country}_MBTI.csv",
    mime="text/csv"
)

st.divider()

st.caption(
    "※ 표시된 비율은 제공된 CSV 데이터 기준입니다. "
    "조사 표본과 출처에 따라 해석에 차이가 있을 수 있습니다."
)
