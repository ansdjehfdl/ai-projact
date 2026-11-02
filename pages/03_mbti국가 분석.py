
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide",
)

# 현재 app.py가 위치한 폴더
BASE_DIR = Path(__file__).resolve().parent

# CSV 파일 경로
CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"


# =====================================
# 2. 데이터 불러오기
# =====================================
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    if "Country" not in df.columns:
        raise ValueError(
            "CSV 파일에 Country 열이 없습니다."
        )

    mbti_cols = [
        col for col in df.columns
        if col != "Country"
    ]

    if not mbti_cols:
        raise ValueError(
            "MBTI 유형 열을 찾을 수 없습니다."
        )

    # 국가 이름 정리
    df["Country"] = df["Country"].astype("string").str.strip()

    # MBTI 값 숫자 변환
    for col in mbti_cols:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    # 빈 국가 이름 제거
    df = df.dropna(subset=["Country"])
    df = df[df["Country"] != ""]

    return df, mbti_cols


# 파일 존재 여부 확인
if not CSV_PATH.is_file():
    st.error("CSV 데이터 파일을 찾을 수 없습니다.")

    st.markdown(
        """
        ### 해결 방법

        GitHub 저장소에 다음 파일 3개가 있는지 확인해 주세요.

        - `app.py`
        - `countriesMBTI_16types.csv`
        - `requirements.txt`

        **중요:** CSV 파일은 기본적으로 `app.py`와
        같은 폴더에 있어야 합니다.

        파일 이름의 대소문자와 철자도 확인해 주세요.
        """
    )

    st.stop()


# 데이터 로드
try:
    df, mbti_cols = load_data(str(CSV_PATH))

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


if df.empty:
    st.error("CSV 파일에 분석할 데이터가 없습니다.")
    st.stop()


# =====================================
# 3. 제목 및 설명
# =====================================
st.title("🌍 국가별 MBTI 분석")
st.write(
    "국가를 선택하면 16가지 MBTI 유형의 비율을 "
    "막대그래프로 확인할 수 있습니다."
)

st.caption(
    "빨간색은 해당 국가에서 비율이 가장 높은 MBTI이며, "
    "나머지는 파란색 그라데이션으로 표시됩니다."
)

st.divider()


# =====================================
# 4. 기본 데이터 정보
# =====================================
col1, col2, col3 = st.columns(3)

col1.metric(
    "국가 수",
    f"{df['Country'].nunique()}개",
)

col2.metric(
    "MBTI 유형 수",
    f"{len(mbti_cols)}개",
)

col3.metric(
    "결측 셀 수",
    f"{int(df[mbti_cols].isna().sum().sum())}개",
)


# =====================================
# 5. 국가 선택
# =====================================
st.subheader("🔎 국가 선택")

countries = sorted(
    df["Country"].unique().tolist()
)

default_country = (
    "South Korea"
    if "South Korea" in countries
    else countries[0]
)

country = st.selectbox(
    "분석할 국가를 선택하세요.",
    options=countries,
    index=countries.index(default_country),
)


# =====================================
# 6. 선택 국가 데이터 처리
# =====================================
selected_rows = df.loc[
    df["Country"] == country,
    mbti_cols,
]

# 국가 이름이 중복된 경우 첫 번째 행 사용
row = selected_rows.iloc[0]

chart_data = pd.DataFrame({
    "MBTI": mbti_cols,
    "비율": [
        row[mbti] * 100
        if pd.notna(row[mbti])
        else None
        for mbti in mbti_cols
    ],
})

# 결측값 제외, 비율이 높은 순으로 정렬
chart_data = (
    chart_data
    .dropna(subset=["비율"])
    .sort_values(
        "비율",
        ascending=False,
        kind="stable",
    )
    .reset_index(drop=True)
)

if chart_data.empty:
    st.warning(
        "선택한 국가에 표시할 MBTI 데이터가 없습니다."
    )
    st.stop()


# =====================================
# 7. 순위와 색상 설정
# =====================================
chart_data["순위"] = range(
    1, len(chart_data) + 1
)

colors = []

# 파란색 그라데이션 시작 및 종료 색상
blue_start = (21, 101, 192)    # 진한 파랑
blue_end = (220, 235, 250)     # 연한 파랑

total = len(chart_data)

for rank in chart_data["순위"]:

    # 1위: 빨간색
    if rank == 1:
        colors.append("#E53935")

    # 나머지: 진한 파랑에서 연한 파랑으로
    else:
        denominator = max(total - 2, 1)
        t = (rank - 2) / denominator
        t = max(0, min(t, 1))

        rgb = tuple(
            round(
                blue_start[i]
                + (blue_end[i] - blue_start[i]) * t
            )
            for i in range(3)
        )

        color = "#{:02X}{:02X}{:02X}".format(*rgb)
        colors.append(color)

chart_data["색상"] = colors


# =====================================
# 8. 최고 비율 요약
# =====================================
top = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric(
    "선택 국가",
    country,
)

col2.metric(
    "비율 1위 MBTI",
    top["MBTI"],
)

col3.metric(
    "1위 비율",
    f"{top['비율']:.2f}%",
)


# =====================================
# 9. 막대그래프
# =====================================
st.divider()

st.subheader(
    f"📊 {country}의 MBTI 유형별 비율"
)

fig = px.bar(
    chart_data,
    x="MBTI",
    y="비율",
    custom_data=["순위"],
    color="MBTI",
    color_discrete_map=dict(
        zip(
            chart_data["MBTI"],
            chart_data["색상"],
        )
    ),
    category_orders={
        "MBTI": chart_data["MBTI"].tolist()
    },
    text=chart_data["비율"].map(
        lambda value: f"{value:.2f}%"
    ),
)

fig.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "비율: %{y:.2f}%<br>"
        "순위: %{customdata[0]}위"
        "<extra></extra>"
    ),
)

fig.update_layout(
    showlegend=False,
    height=600,
    bargap=0.25,
    xaxis_title="MBTI 유형",
    yaxis_title="비율 (%)",
    yaxis_ticksuffix="%",
    yaxis_rangemode="tozero",
    margin=dict(
        t=40,
        b=40,
        l=30,
        r=35,
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

st.caption(
    "색상 기준: 1위 빨간색 · 2위부터 파란색 그라데이션"
)


# =====================================
# 10. 상세 순위표
# =====================================
st.divider()

st.subheader("🏆 MBTI 순위")

display_data = chart_data[
    ["순위", "MBTI", "비율"]
].copy()

display_data["비율"] = display_data["비율"].map(
    lambda value: f"{value:.2f}%"
)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True,
)


# =====================================
# 11. CSV 다운로드
# =====================================
download_data = chart_data[
    ["순위", "MBTI", "비율"]
].copy()

st.download_button(
    label="📥 선택 국가 데이터 다운로드",
    data=download_data.to_csv(
        index=False
    ).encode("utf-8-sig"),
    file_name=f"{country}_MBTI.csv",
    mime="text/csv",
)


# =====================================
# 12. 전체 데이터 확인
# =====================================
with st.expander("📚 전체 국가 데이터 확인"):

    search = st.text_input(
        "국가 이름 검색",
        placeholder="국가 이름을 입력하세요.",
    )

    filtered_df = df[
        df["Country"].str.contains(
            search,
            case=False,
            na=False,
        )
    ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )


# =====================================
# 13. 하단 안내
# =====================================
st.divider()

st.caption(
    "본 분석은 제공된 CSV 파일의 비율을 기준으로 합니다. "
    "데이터의 출처와 조사 방법에 따라 해석에 차이가 있을 수 있습니다."
)

