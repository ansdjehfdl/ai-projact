
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================
# 1. 페이지 설정
# =====================================

st.set_page_config(
    page_title="월별 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온 분석")
st.write("원하는 월을 선택하여 연도별 최고기온과 최저기온을 비교해 보세요.")

# =====================================
# 2. 데이터 불러오기
# =====================================

@st.cache_data
def load_data(file):
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]

    for enc in encodings:
        try:
            df = pd.read_csv(file, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("CSV 인코딩을 확인할 수 없습니다.")

    return df


try:
    uploaded_file = st.file_uploader(
        "기온 CSV 파일 업로드 (선택)",
        type=["csv"]
    )

    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        df = load_data("temperature.csv")

except FileNotFoundError:
    st.error("temperature.csv 파일을 찾을 수 없습니다.")
    st.stop()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류 발생: {e}")
    st.stop()


# =====================================
# 3. 데이터 전처리
# =====================================

required_columns = [
    "일시",
    "최고기온(℃)",
    "최저기온(℃)"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"필요한 컬럼이 없습니다: {missing_columns}")
    st.stop()

# 월 영문 약어를 숫자로 변환
month_dict = {
    "Jan": 1, "Feb": 2, "Mar": 3,
    "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12
}

date_parts = df["일시"].astype(str).str.strip().str.split("-", expand=True)

if date_parts.shape[1] != 2:
    st.error("일시 데이터 형식이 올바르지 않습니다.")
    st.stop()

df["월"] = date_parts[0].map(month_dict)
df["연도"] = pd.to_numeric(
    date_parts[1], errors="coerce"
)

# 현재 데이터의 두 자리 연도는 2000년대로 변환
df["연도"] = df["연도"].apply(
    lambda x: 2000 + int(x) if pd.notna(x) and x < 100 else x
)

df["최고기온(℃)"] = pd.to_numeric(
    df["최고기온(℃)"], errors="coerce"
)

df["최저기온(℃)"] = pd.to_numeric(
    df["최저기온(℃)"], errors="coerce"
)

df = df.dropna(subset=["월", "연도"])

df["연도"] = df["연도"].astype(int)
df["월"] = df["월"].astype(int)


# =====================================
# 4. 월 선택
# =====================================

month_names = {
    1: "1월", 2: "2월", 3: "3월",
    4: "4월", 5: "5월", 6: "6월",
    7: "7월", 8: "8월", 9: "9월",
    10: "10월", 11: "11월", 12: "12월"
}

selected_month_name = st.selectbox(
    "📅 분석할 월을 선택하세요.",
    list(month_names.values())
)

selected_month = [
    key for key, value in month_names.items()
    if value == selected_month_name
][0]


# =====================================
# 5. 선택한 월 데이터 필터링
# =====================================

filtered_df = df[
    df["월"] == selected_month
].copy()

filtered_df = filtered_df.sort_values("연도")

if filtered_df.empty:
    st.warning("선택한 월에 해당하는 데이터가 없습니다.")
    st.stop()


# =====================================
# 6. 기온 분석 그래프
# =====================================

fig = go.Figure()

# 최고기온 그래프
fig.add_trace(
    go.Scatter(
        x=filtered_df["연도"],
        y=filtered_df["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(
            size=8,
            color="#FF1493"
        )
    )
)

# 최저기온 그래프
fig.add_trace(
    go.Scatter(
        x=filtered_df["연도"],
        y=filtered_df["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#1E90FF",
            width=3
        ),
        marker=dict(
            size=8,
            color="#1E90FF"
        )
    )
)

# 그래프 디자인
fig.update_layout(
    title={
        "text": "월별 기온분석",
        "x": 0.5,
        "xanchor": "center"
    },

    xaxis_title="연도",
    yaxis_title="온도(℃)",

    legend=dict(
        title="범례",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),

    template="plotly_white",

    height=550,

    hovermode="x unified"
)

fig.update_xaxes(
    dtick=1
)

fig.update_yaxes(
    showgrid=True,
    zeroline=True
)

# 그래프 출력
st.plotly_chart(
    fig,
    use_container_width=True
)


# =====================================
# 7. 데이터 표 출력
# =====================================

st.subheader("📊 선택한 월의 기온 데이터")

result_df = filtered_df[
    ["연도", "최고기온(℃)", "최저기온(℃)"]
].copy()

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"분석 월: {selected_month_name} | "
    f"데이터 개수: {len(result_df)}개"
)
