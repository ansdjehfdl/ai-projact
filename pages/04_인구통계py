
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="지역별 연령 인구 통계",
    page_icon="📊",
    layout="wide"
)

HOT_PINK = "#FF1493"

# pages 폴더의 상위 폴더에서 CSV 찾기
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "population.csv"


# ==========================================
# 2. 디자인 CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background-color: #fffafd;
}

h1, h2, h3 {
    color: #b00068;
}

div[data-testid="stMetric"] {
    background: #fff0f7;
    border: 1px solid #ffd0e7;
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. CSV 데이터 불러오기 및 한글 인코딩
# ==========================================

@st.cache_data
def load_data(file_path):

    encodings = [
        "cp949",
        "euc-kr",
        "utf-8-sig",
        "utf-8"
    ]

    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                dtype=str
            )
            break

        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 인코딩을 확인할 수 없습니다.")

    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()

    # 인구수 쉼표 제거 및 숫자 변환
    for column in df.columns:

        if column != "행정구역":

            df[column] = pd.to_numeric(
                df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip(),
                errors="coerce"
            )

    return df


# ==========================================
# 4. 데이터 로딩
# ==========================================

if not DATA_FILE.exists():

    st.error(
        "population.csv 파일을 찾을 수 없습니다. "
        "상위 폴더에 CSV 파일이 있는지 확인해 주세요."
    )

    st.stop()

try:
    df = load_data(str(DATA_FILE))

except Exception as e:

    st.error(f"데이터 로딩 오류: {e}")
    st.stop()


# ==========================================
# 5. 제목
# ==========================================

st.title("📊 지역별 연령 인구 통계")

st.caption(
    "행정구역, 성별, 연도를 선택하여 "
    "연령별 인구 변화를 확인할 수 있습니다."
)


# ==========================================
# 6. 연도 추출
# ==========================================

years = sorted({

    int(match.group(1))

    for column in df.columns

    if (match := re.match(r"(\d{4})년_", column))

})


if not years:

    st.error("연도 정보를 찾을 수 없습니다.")
    st.stop()


# ==========================================
# 7. 성별 설정
# ==========================================

sex_options = {
    "전체": "",
    "남성": "남_",
    "여성": "여_"
}


# ==========================================
# 8. 검색 조건 선택
# ==========================================

st.subheader("검색 조건")

col1, col2, col3 = st.columns(3)


regions = (
    df["행정구역"]
    .dropna()
    .astype(str)
    .str.strip()
    .tolist()
)


with col1:

    selected_region = st.selectbox(
        "행정구역 선택",
        regions
    )


with col2:

    selected_sex = st.selectbox(
        "성별 선택",
        list(sex_options.keys())
    )


with col3:

    selected_year = st.selectbox(
        "연도 선택",
        years,
        index=len(years) - 1
    )


# ==========================================
# 9. 선택한 데이터 추출
# ==========================================

selected_rows = df[
    df["행정구역"].astype(str).str.strip()
    == selected_region
]


if selected_rows.empty:

    st.error("선택한 지역의 데이터가 없습니다.")
    st.stop()


row = selected_rows.iloc[0]


# 선택한 연도와 성별에 맞는 컬럼 찾기
prefix = (
    f"{selected_year}년_"
    f"{sex_options[selected_sex]}"
    "거주자_"
)


age_columns = [

    column

    for column in df.columns

    if column.startswith(prefix)

    and re.search(
        r"_(\d+~\d+세|100세 이상)$",
        column
    )

]


# ==========================================
# 10. 나이 순서 정렬
# ==========================================

def age_sort_key(column):

    match = re.search(
        r"_(\d+)~(\d+)세$",
        column
    )

    if match:
        return int(match.group(1))

    if column.endswith("_100세 이상"):
        return 100

    return 999


age_columns = sorted(
    age_columns,
    key=age_sort_key
)


if not age_columns:

    st.error("연령별 데이터를 찾을 수 없습니다.")
    st.stop()


# ==========================================
# 11. 그래프 데이터 생성
# ==========================================

age_labels = []
population_values = []

for column in age_columns:

    match = re.search(
        r"_(\d+~\d+세|100세 이상)$",
        column
    )

    age_labels.append(match.group(1))

    value = row[column]

    population_values.append(
        0 if pd.isna(value) else int(value)
    )


# 전체 연령 인구 합계
total_population = sum(population_values)

# 인구가 가장 많은 연령대
max_index = population_values.index(
    max(population_values)
)


# ==========================================
# 12. 주요 통계 표시
# ==========================================

st.subheader("주요 인구 통계")

m1, m2, m3 = st.columns(3)

m1.metric(
    "선택 지역",
    selected_region.split(" (")[0]
)

m2.metric(
    "연령별 인구 합계",
    f"{total_population:,}명"
)

m3.metric(
    "인구가 가장 많은 연령대",
    age_labels[max_index]
)


# ==========================================
# 13. 핫핑크 꺾은선 그래프
# ==========================================

st.subheader(
    f"{selected_region.split(' (')[0]} "
    f"· {selected_year}년 · {selected_sex}"
)


fig = go.Figure()


fig.add_trace(

    go.Scatter(

        x=age_labels,

        y=population_values,

        mode="lines+markers",

        name="인구수",

        line=dict(
            color=HOT_PINK,
            width=4
        ),

        marker=dict(
            color=HOT_PINK,
            size=9,
            line=dict(
                color="white",
                width=1.5
            )
        ),

        hovertemplate=
        "%{x}<br>인구수: %{y:,}명<extra></extra>"

    )

)


# 세로축 최대값을 10만 단위로 설정
max_population = max(population_values)

y_axis_max = max(
    100000,
    ((max_population // 100000) + 1) * 100000
)


# 그래프 디자인
fig.update_layout(

    template="plotly_white",

    height=560,

    margin=dict(
        l=25,
        r=25,
        t=30,
        b=35
    ),

    plot_bgcolor="white",

    paper_bgcolor="white",

    font=dict(
        family="Malgun Gothic, Apple SD Gothic Neo, NanumGothic, sans-serif",
        size=13,
        color="#333333"
    ),

    showlegend=False,

    hovermode="x unified",

    xaxis=dict(

        title="나이",

        type="category",

        categoryorder="array",

        categoryarray=age_labels,

        showgrid=True,

        gridcolor="#f3d7e5",

        gridwidth=1,

        showline=True,

        linecolor="#d8a9c0"

    ),

    yaxis=dict(

        title="인구수 (명)",

        range=[0, y_axis_max],

        dtick=100000,

        tickformat=",",

        showgrid=True,

        gridcolor="#dedede",

        gridwidth=1,

        zeroline=True

    )

)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================
# 14. 연령별 인구 데이터 표
# ==========================================

with st.expander("📋 연령별 인구 데이터 확인"):

    result_table = pd.DataFrame({

        "연령대": age_labels,

        "인구수": population_values

    })

    st.dataframe(
        result_table,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 15. 하단 안내
# ==========================================

st.divider()

st.caption(
    "자료: population.csv | "
    "연령대는 10년 단위로 구분됩니다."
)
