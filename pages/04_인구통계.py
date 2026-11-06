import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="지역별 인구 통계 대시보드",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "population.csv"

BLUE = "#2878FF"
PINK = "#FF4F9A"


# 디자인 설정
st.markdown("""
<style>
.stApp {
    background-color: #FFF9FC;
}

h1, h2, h3 {
    color: #9B245F;
}

div[data-testid="stMetric"] {
    background: #FFF0F6;
    border: 1px solid #F7C9DD;
    padding: 13px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. CSV 데이터 불러오기
# ==========================================

@st.cache_data
def load_data(file_path):

    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(
                file_path,
                encoding=encoding,
                dtype=str
            )
            break

        except UnicodeDecodeError:
            continue

    else:
        raise ValueError("CSV 인코딩을 확인해 주세요.")

    data.columns = data.columns.astype(str).str.strip()

    if "행정구역" not in data.columns:
        raise ValueError("'행정구역' 열이 없습니다.")

    data["행정구역"] = data["행정구역"].astype(str).str.strip()

    for col in data.columns:
        if col != "행정구역":

            data[col] = pd.to_numeric(
                data[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip(),
                errors="coerce"
            )

    return data


if not DATA_FILE.exists():
    st.error(
        "population.csv 파일을 찾을 수 없습니다.\n\n"
        "프로젝트 최상위 폴더에 population.csv를 넣어주세요."
    )
    st.stop()


try:
    df = load_data(DATA_FILE)

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


# ==========================================
# 3. 데이터 분석 함수
# ==========================================

years = sorted({
    int(match.group(1))
    for col in df.columns
    if (match := re.match(r"(\d{4})년_", col))
})

regions = df["행정구역"].dropna().tolist()


def clean_region(name):
    return re.sub(r"\s*\([^)]*\)", "", str(name)).strip()


def is_aggregate(name):
    return clean_region(name) in ["광주광역시", "전라남도"]


# 광주광역시와 전라남도 전체 합계 행 제외
rank_df = df[
    ~df["행정구역"].apply(is_aggregate)
].copy()

if rank_df.empty:
    rank_df = df.copy()


def get_age_columns(year, sex="전체"):

    if sex == "전체":
        prefix = f"{year}년_거주자_"
    else:
        prefix = f"{year}년_{sex}_거주자_"

    pattern = re.compile(r"(\d+~\d+세|100세 이상)$")

    result = {}

    for col in df.columns:

        if col.startswith(prefix):

            match = pattern.search(col)

            if match:
                result[match.group(1)] = col

    return dict(
        sorted(
            result.items(),
            key=lambda x: int(re.match(r"\d+", x[0]).group())
        )
    )


def get_total_column(year, sex="전체"):

    if sex == "전체":
        col = f"{year}년_거주자_총인구수"
    else:
        col = f"{year}년_{sex}_거주자_총인구수"

    return col if col in df.columns else None


def safe_number(value):

    if pd.isna(value):
        return 0

    return int(value)


# ==========================================
# 4. 메인 화면
# ==========================================

st.title("📊 지역별 인구 통계 대시보드")

st.write(
    "광주광역시와 전라남도의 연도별, "
    "지역별, 성별, 연령대별 인구를 분석합니다."
)

st.divider()

col1, col2 = st.columns(2)

with col1:

    selected_region = st.selectbox(
        "행정구역 선택",
        regions,
        format_func=clean_region,
        key="main_region"
    )

with col2:

    selected_year = st.selectbox(
        "연도 선택",
        years,
        index=len(years) - 1,
        key="main_year"
    )


selected_row = df[
    df["행정구역"] == selected_region
].iloc[0]


# ==========================================
# 5. 성별 연령별 인구 그래프
# ==========================================

st.header("1. 성별·연령대별 인구")

st.write(
    "남성은 파란색, 여성은 분홍색으로 표시됩니다."
)

male_cols = get_age_columns(selected_year, "남")
female_cols = get_age_columns(selected_year, "여")

common_ages = [
    age for age in male_cols
    if age in female_cols
]

if common_ages:

    male_values = [
        safe_number(selected_row[male_cols[a]])
        for a in common_ages
    ]

    female_values = [
        safe_number(selected_row[female_cols[a]])
        for a in common_ages
    ]

    male_total_col = get_total_column(selected_year, "남")
    female_total_col = get_total_column(selected_year, "여")

    male_total = (
        safe_number(selected_row[male_total_col])
        if male_total_col else sum(male_values)
    )

    female_total = (
        safe_number(selected_row[female_total_col])
        if female_total_col else sum(female_values)
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("남성 인구", f"{male_total:,}명")
    c2.metric("여성 인구", f"{female_total:,}명")
    c3.metric("전체 인구", f"{male_total + female_total:,}명")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=common_ages,
        y=male_values,
        mode="lines+markers",
        name="남성",
        line=dict(color=BLUE, width=3),
        marker=dict(size=8)
    ))

    fig.add_trace(go.Scatter(
        x=common_ages,
        y=female_values,
        mode="lines+markers",
        name="여성",
        line=dict(color=PINK, width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        template="plotly_white",
        height=480,
        hovermode="x unified",
        xaxis_title="연령대",
        yaxis_title="인구수(명)",
        yaxis_tickformat=",",
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("연령별 인구 데이터 보기"):

        st.dataframe(
            pd.DataFrame({
                "연령대": common_ages,
                "남성": male_values,
                "여성": female_values
            }),
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("남녀 연령별 데이터가 없습니다.")


st.divider()


# ==========================================
# 6. 추가 분석 기능
# ==========================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "연령대별 지역 순위",
    "인구 피라미드",
    "청년·고령층 분석",
    "지역별 총인구 순위",
    "연도별 인구 비교"
])


# ==========================================
# 기능 1. 연령대별 지역 순위
# ==========================================

with tab1:

    st.subheader("연령대별 인구가 많은 지역 TOP 10")

    c1, c2, c3 = st.columns(3)

    with c1:

        rank_year = st.selectbox(
            "연도",
            years,
            index=len(years) - 1,
            key="rank_year"
        )

    with c2:

        rank_sex = st.selectbox(
            "성별",
            ["전체", "남", "여"],
            format_func=lambda x: {
                "전체": "전체",
                "남": "남성",
                "여": "여성"
            }[x],
            key="rank_sex"
        )

    rank_columns = get_age_columns(
        rank_year,
        rank_sex
    )

    with c3:

        rank_age = st.selectbox(
            "연령대",
            list(rank_columns.keys()),
            key="rank_age"
        ) if rank_columns else None

    if rank_age:

        col = rank_columns[rank_age]

        ranking = rank_df[
            ["행정구역", col]
        ].copy()

        ranking["지역"] = ranking["행정구역"].apply(clean_region)

        ranking["인구수"] = ranking[col].fillna(0).astype(int)

        ranking = ranking.sort_values(
            "인구수",
            ascending=False
        )

        winner = ranking.iloc[0]

        st.metric(
            "인구가 가장 많은 지역",
            winner["지역"],
            f'{winner["인구수"]:,}명'
        )

        display = ranking.head(10).sort_values("인구수")

        fig = px.bar(
            display,
            x="인구수",
            y="지역",
            orientation="h",
            text="인구수",
            color="인구수",
            color_continuous_scale=["#F9C5DA", "#C02B75"]
        )

        fig.update_traces(
            texttemplate="%{text:,}명",
            textposition="outside"
        )

        fig.update_layout(
            template="plotly_white",
            height=520,
            coloraxis_showscale=False,
            xaxis_tickformat=","
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "광주광역시와 전라남도 전체 합계 행은 "
            "중복 계산을 방지하기 위해 제외했습니다."
        )

        with st.expander("전체 순위 데이터"):

            st.dataframe(
                ranking[["지역", "인구수"]],
                use_container_width=True,
                hide_index=True
            )


# ==========================================
# 기능 2. 인구 피라미드
# ==========================================

with tab2:

    st.subheader("남녀 인구 피라미드")

    c1, c2 = st.columns(2)

    with c1:

        pyramid_region = st.selectbox(
            "행정구역",
            regions,
            format_func=clean_region,
            key="pyramid_region"
        )

    with c2:

        pyramid_year = st.selectbox(
            "연도",
            years,
            index=len(years) - 1,
            key="pyramid_year"
        )

    row = df[
        df["행정구역"] == pyramid_region
    ].iloc[0]

    m = get_age_columns(pyramid_year, "남")
    f = get_age_columns(pyramid_year, "여")

    ages = [a for a in m if a in f]

    if ages:

        male = [
            safe_number(row[m[a]])
            for a in ages
        ]

        female = [
            safe_number(row[f[a]])
            for a in ages
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=ages,
            x=[-v for v in male],
            name="남성",
            orientation="h",
            marker_color=BLUE,
            customdata=male,
            hovertemplate="%{y}<br>남성: %{customdata:,}명<extra></extra>"
        ))

        fig.add_trace(go.Bar(
            y=ages,
            x=female,
            name="여성",
            orientation="h",
            marker_color=PINK,
            hovertemplate="%{y}<br>여성: %{x:,}명<extra></extra>"
        ))

        max_value = max(male + female + [1])
        tick = max(1000, int(max_value / 4 / 1000) * 1000)

        ticks = list(range(
            -((max_value // tick) + 1) * tick,
            ((max_value // tick) + 1) * tick + tick,
            tick
        ))

        fig.update_layout(
            barmode="relative",
            template="plotly_white",
            height=560,
            xaxis=dict(
                title="인구수(명)",
                tickvals=ticks,
                ticktext=[f"{abs(v):,}" for v in ticks]
            ),
            yaxis_title="연령대",
            legend=dict(orientation="h", y=1.12)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "남성은 왼쪽, 여성은 오른쪽에 표시됩니다."
        )

    else:

        st.warning("인구 피라미드 데이터가 없습니다.")


# ==========================================
# 기능 3. 청년층·고령층 분석
# ==========================================

with tab3:

    st.subheader("청년층·고령층 인구 비율 분석")

    st.info(
        "원본 데이터가 10세 단위이므로 정확한 65세 이상 인구는 "
        "계산할 수 없습니다. 이 분석에서는 청년층을 0~19세, "
        "고령층을 70세 이상으로 정의합니다."
    )

    ratio_year = st.selectbox(
        "분석 연도",
        years,
        index=len(years) - 1,
        key="ratio_year"
    )

    age_map = get_age_columns(ratio_year, "전체")

    youth_ages = ["0~9세", "10~19세"]

    senior_ages = [
        age for age in age_map
        if int(re.match(r"\d+", age).group()) >= 70
    ]

    if all(a in age_map for a in youth_ages) and senior_ages:

        total_col = get_total_column(ratio_year, "전체")

        rows = []

        for _, row in rank_df.iterrows():

            total = (
                safe_number(row[total_col])
                if total_col
                else sum(
                    safe_number(row[c])
                    for c in age_map.values()
                )
            )

            youth = sum(
                safe_number(row[age_map[a]])
                for a in youth_ages
            )

            senior = sum(
                safe_number(row[age_map[a]])
                for a in senior_ages
            )

            rows.append({
                "지역": clean_region(row["행정구역"]),
                "총인구": total,
                "청년층 인구": youth,
                "고령층 인구": senior,
                "청년층 비율(%)": youth / total * 100 if total else 0,
                "고령층 비율(%)": senior / total * 100 if total else 0
            })

        ratio_df = pd.DataFrame(rows)

        oldest = ratio_df.sort_values(
            "고령층 비율(%)",
            ascending=False
        ).iloc[0]

        youngest = ratio_df.sort_values(
            "청년층 비율(%)",
            ascending=False
        ).iloc[0]

        c1, c2 = st.columns(2)

        c1.metric(
            "고령층 비율이 가장 높은 지역",
            oldest["지역"],
            f'{oldest["고령층 비율(%)"]:.1f}%'
        )

        c2.metric(
            "청년층 비율이 가장 높은 지역",
            youngest["지역"],
            f'{youngest["청년층 비율(%)"]:.1f}%'
        )

        long_df = ratio_df.melt(
            id_vars="지역",
            value_vars=[
                "청년층 비율(%)",
                "고령층 비율(%)"
            ],
            var_name="구분",
            value_name="비율(%)"
        )

        fig = px.bar(
            long_df,
            x="지역",
            y="비율(%)",
            color="구분",
            barmode="group",
            color_discrete_map={
                "청년층 비율(%)": BLUE,
                "고령층 비율(%)": PINK
            }
        )

        fig.update_layout(
            template="plotly_white",
            height=540,
            xaxis_tickangle=-55,
            margin=dict(b=100)
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("비율 데이터 확인"):

            st.dataframe(
                ratio_df.round(2),
                use_container_width=True,
                hide_index=True
            )

    else:

        st.warning("분석에 필요한 연령별 데이터가 없습니다.")


# ==========================================
# 기능 4. 지역별 총인구 순위
# ==========================================

with tab4:

    st.subheader("지역별 총인구 TOP 10")

    c1, c2 = st.columns(2)

    with c1:

        total_year = st.selectbox(
            "연도",
            years,
            index=len(years) - 1,
            key="total_year"
        )

    with c2:

        total_sex = st.selectbox(
            "성별",
            ["전체", "남", "여"],
            format_func=lambda x: {
                "전체": "전체",
                "남": "남성",
                "여": "여성"
            }[x],
            key="total_sex"
        )

    total_col = get_total_column(
        total_year,
        total_sex
    )

    if total_col:

        ranking = rank_df[
            ["행정구역", total_col]
        ].copy()

        ranking["지역"] = ranking["행정구역"].apply(clean_region)

        ranking["인구수"] = ranking[total_col].fillna(0).astype(int)

        ranking = ranking.sort_values(
            "인구수",
            ascending=False
        )

        winner = ranking.iloc[0]

        st.metric(
            "인구가 가장 많은 지역",
            winner["지역"],
            f'{winner["인구수"]:,}명'
        )

        display = ranking.head(10).sort_values("인구수")

        fig = px.bar(
            display,
            x="인구수",
            y="지역",
            orientation="h",
            text="인구수",
            color="인구수",
            color_continuous_scale=["#C9DFFF", "#2463C7"]
        )

        fig.update_traces(
            texttemplate="%{text:,}명",
            textposition="outside"
        )

        fig.update_layout(
            template="plotly_white",
            height=520,
            coloraxis_showscale=False,
            xaxis_tickformat=","
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("전체 지역 순위 데이터"):

            st.dataframe(
                ranking[["지역", "인구수"]],
                use_container_width=True,
                hide_index=True
            )

    else:

        st.warning("총인구 열을 찾을 수 없습니다.")


# ==========================================
# 기능 5. 연도별 인구 비교
# ==========================================

with tab5:

    st.subheader("두 연도의 인구 변화 비교")

    compare_region = st.selectbox(
        "행정구역",
        regions,
        format_func=clean_region,
        key="compare_region"
    )

    c1, c2 = st.columns(2)

    with c1:

        year_a = st.selectbox(
            "첫 번째 연도",
            years,
            index=0,
            key="year_a"
        )

    with c2:

        year_b = st.selectbox(
            "두 번째 연도",
            years,
            index=len(years) - 1,
            key="year_b"
        )

    row = df[
        df["행정구역"] == compare_region
    ].iloc[0]

    total_a = get_total_column(year_a, "전체")
    total_b = get_total_column(year_b, "전체")

    if total_a and total_b:

        pop_a = safe_number(row[total_a])
        pop_b = safe_number(row[total_b])

        diff = pop_b - pop_a

        rate = (
            diff / pop_a * 100
            if pop_a else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            f"{year_a}년 총인구",
            f"{pop_a:,}명"
        )

        c2.metric(
            f"{year_b}년 총인구",
            f"{pop_b:,}명",
            f"{diff:+,}명"
        )

        c3.metric(
            "인구 증감률",
            f"{rate:+.2f}%"
        )

    age_a = get_age_columns(year_a, "전체")
    age_b = get_age_columns(year_b, "전체")

    common = [
        age for age in age_a
        if age in age_b
    ]

    if common:

        values_a = [
            safe_number(row[age_a[a]])
            for a in common
        ]

        values_b = [
            safe_number(row[age_b[a]])
            for a in common
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=common,
            y=values_a,
            name=f"{year_a}년",
            marker_color="#9BBCEB"
        ))

        fig.add_trace(go.Bar(
            x=common,
            y=values_b,
            name=f"{year_b}년",
            marker_color="#E78AB4"
        ))

        fig.update_layout(
            barmode="group",
            template="plotly_white",
            height=480,
            xaxis_title="연령대",
            yaxis_title="인구수(명)",
            yaxis_tickformat=","
        )

        st.plotly_chart(fig, use_container_width=True)

        change_df = pd.DataFrame({
            "연령대": common,
            f"{year_a}년": values_a,
            f"{year_b}년": values_b,
            "증감 인구": [
                b - a for a, b in zip(values_a, values_b)
            ]
        })

        with st.expander("연령대별 인구 변화 데이터"):

            st.dataframe(
                change_df,
                use_container_width=True,
                hide_index=True
            )

    else:

        st.warning("비교할 연령별 데이터가 없습니다.")


# ==========================================
# 마지막 안내
# ==========================================

st.divider()

st.caption(
    "데이터 출처: population.csv | "
    "원본 데이터의 행정구역과 연령 구간을 기준으로 분석합니다."
)
