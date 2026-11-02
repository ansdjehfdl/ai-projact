
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"


# ==========================================
# 2. 데이터 불러오기
# ==========================================
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

    df["Country"] = df["Country"].astype("string").str.strip()

    for col in mbti_cols:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(subset=["Country"])
    df = df[df["Country"] != ""]

    # 중복 국가가 있다면 첫 번째 행 사용
    df = df.drop_duplicates(
        subset=["Country"], keep="first"
    )

    return df, mbti_cols


if not CSV_PATH.is_file():
    st.error(
        "CSV 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 "
        "countriesMBTI_16types.csv를 올려 주세요."
    )
    st.stop()

try:
    df, mbti_cols = load_data(str(CSV_PATH))
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

if df.empty or not mbti_cols:
    st.error("분석할 데이터가 없습니다.")
    st.stop()


# ==========================================
# 3. 제목
# ==========================================
st.title("🌍 국가별 MBTI 분석 대시보드")

st.write(
    "국가별 MBTI 분포와 MBTI 유형별 국가 순위를 "
    "시각적으로 비교할 수 있습니다."
)

st.divider()


# ==========================================
# 4. 데이터 요약
# ==========================================
c1, c2, c3 = st.columns(3)

c1.metric("국가 수", f"{df['Country'].nunique()}개")
c2.metric("MBTI 유형", f"{len(mbti_cols)}개")
c3.metric(
    "결측 셀 수",
    f"{int(df[mbti_cols].isna().sum().sum())}개"
)


# ==========================================
# 5. 그래프 1: 국가별 MBTI 비율
# ==========================================
st.header("📊 1. 국가별 MBTI 비율")

countries = sorted(df["Country"].unique().tolist())

default_country = (
    "South Korea"
    if "South Korea" in countries
    else countries[0]
)

country = st.selectbox(
    "분석할 국가를 선택하세요",
    countries,
    index=countries.index(default_country),
    key="country_select",
)

row = df.loc[
    df["Country"] == country,
    mbti_cols
].iloc[0]

country_data = pd.DataFrame({
    "MBTI": mbti_cols,
    "비율": [
        row[m] * 100 if pd.notna(row[m]) else None
        for m in mbti_cols
    ],
})

country_data = (
    country_data
    .dropna(subset=["비율"])
    .sort_values("비율", ascending=False)
    .reset_index(drop=True)
)

if country_data.empty:
    st.warning("선택한 국가의 데이터가 없습니다.")
else:
    country_data["순위"] = range(
        1, len(country_data) + 1
    )

    # 1위 빨강, 이후 파란색 그라데이션
    country_colors = []

    total = len(country_data)
    blue_start = (21, 101, 192)
    blue_end = (220, 235, 250)

    for rank in country_data["순위"]:
        if rank == 1:
            country_colors.append("#E53935")
        else:
            t = (rank - 2) / max(total - 2, 1)
            t = max(0, min(t, 1))

            rgb = tuple(
                round(
                    blue_start[i]
                    + (blue_end[i] - blue_start[i]) * t
                )
                for i in range(3)
            )

            country_colors.append(
                "#{:02X}{:02X}{:02X}".format(*rgb)
            )

    country_data["색상"] = country_colors

    top = country_data.iloc[0]

    m1, m2 = st.columns(2)
    m1.metric("비율 1위 MBTI", top["MBTI"])
    m2.metric("1위 비율", f"{top['비율']:.2f}%")

    fig1 = px.bar(
        country_data,
        x="MBTI",
        y="비율",
        custom_data=["순위"],
        color="MBTI",
        color_discrete_map=dict(
            zip(
                country_data["MBTI"],
                country_data["색상"]
            )
        ),
        category_orders={
            "MBTI": country_data["MBTI"].tolist()
        },
        text=country_data["비율"].map(
            lambda x: f"{x:.2f}%"
        ),
    )

    fig1.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "비율: %{y:.2f}%<br>"
            "순위: %{customdata[0]}위"
            "<extra></extra>"
        ),
    )

    fig1.update_layout(
        showlegend=False,
        height=580,
        bargap=0.25,
        xaxis_title="MBTI 유형",
        yaxis_title="비율 (%)",
        yaxis_ticksuffix="%",
        yaxis_rangemode="tozero",
        margin=dict(t=40, b=40, l=30, r=30),
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    with st.expander("국가별 MBTI 순위표"):
        st.dataframe(
            country_data[["순위", "MBTI", "비율"]]
            .assign(
                비율=lambda x: x["비율"].map(
                    lambda v: f"{v:.2f}%"
                )
            ),
            use_container_width=True,
            hide_index=True,
        )


# ==========================================
# 6. 그래프 2: MBTI별 국가 순위
# ==========================================
st.divider()
st.header("🏆 2. MBTI별 국가 순위")

st.write(
    "MBTI 유형을 선택하면 해당 유형의 비율이 "
    "높은 국가부터 순서대로 표시됩니다."
)

selected_mbti = st.selectbox(
    "비교할 MBTI 유형을 선택하세요",
    mbti_cols,
    key="mbti_select",
)

top_n = st.slider(
    "표시할 국가 수",
    min_value=5,
    max_value=min(50, len(df)),
    value=min(20, len(df)),
    step=5,
)

ranking_data = df[
    ["Country", selected_mbti]
].copy()

ranking_data = ranking_data.dropna(
    subset=[selected_mbti]
)

ranking_data["비율"] = (
    ranking_data[selected_mbti] * 100
)

ranking_data = (
    ranking_data
    .drop(columns=[selected_mbti])
    .sort_values("비율", ascending=False)
    .reset_index(drop=True)
)

ranking_data["순위"] = range(
    1, len(ranking_data) + 1
)

ranking_data = ranking_data.head(top_n).copy()

if ranking_data.empty:
    st.warning("선택한 MBTI의 국가별 데이터가 없습니다.")
else:
    ranking_data["색상"] = [
        "#E53935" if rank == 1 else "#2878C8"
        for rank in ranking_data["순위"]
    ]

    first = ranking_data.iloc[0]

    r1, r2 = st.columns(2)

    r1.metric(
        f"{selected_mbti} 비율 1위 국가",
        first["Country"],
    )

    r2.metric(
        "해당 국가의 비율",
        f"{first['비율']:.2f}%",
    )

    fig2 = px.bar(
        ranking_data,
        x="Country",
        y="비율",
        custom_data=["순위"],
        color="Country",
        color_discrete_map=dict(
            zip(
                ranking_data["Country"],
                ranking_data["색상"]
            )
        ),
        category_orders={
            "Country": ranking_data["Country"].tolist()
        },
        text=ranking_data["비율"].map(
            lambda x: f"{x:.2f}%"
        ),
    )

    fig2.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"MBTI: {selected_mbti}<br>"
            "비율: %{y:.2f}%<br>"
            "순위: %{customdata[0]}위"
            "<extra></extra>"
        ),
    )

    fig2.update_layout(
        showlegend=False,
        height=580,
        bargap=0.25,
        xaxis_title="국가",
        yaxis_title=f"{selected_mbti} 비율 (%)",
        yaxis_ticksuffix="%",
        yaxis_rangemode="tozero",
        xaxis_tickangle=-45,
        margin=dict(t=45, b=100, l=30, r=30),
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
    )

    with st.expander("국가별 상세 순위표"):
        display_ranking = ranking_data[
            ["순위", "Country", "비율"]
        ].copy()

        display_ranking["비율"] = (
            display_ranking["비율"].map(
                lambda x: f"{x:.2f}%"
            )
        )

        st.dataframe(
            display_ranking,
            use_container_width=True,
            hide_index=True,
        )

    st.download_button(
        label="📥 국가 순위 CSV 다운로드",
        data=ranking_data[
            ["순위", "Country", "비율"]
        ].to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{selected_mbti}_국가순위.csv",
        mime="text/csv",
    )


# ==========================================
# 7. 전체 데이터 검색
# ==========================================
st.divider()

with st.expander("🔎 전체 데이터 검색"):
    search = st.text_input(
        "국가 이름 검색",
        placeholder="예: South Korea, Japan",
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


# ==========================================
# 8. 안내
# ==========================================
st.divider()

st.caption(
    "분석 결과는 제공된 CSV 파일의 수치를 기준으로 합니다. "
    "자료의 출처와 표본에 따라 결과 해석에 차이가 있을 수 있습니다."
)

