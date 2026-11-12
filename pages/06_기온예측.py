
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from pathlib import Path

# -----------------------------------
# 1. 페이지 설정
# -----------------------------------

st.set_page_config(
    page_title="서울 기온 예측 시스템",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 예측 시스템")

st.write(
    "과거 서울의 기온 데이터를 분석하여 "
    "선형회귀 알고리즘으로 미래 기온을 예측합니다."
)

st.divider()


# -----------------------------------
# 2. CSV 데이터 불러오기
# -----------------------------------

@st.cache_data
def load_data():

    # pages 폴더의 상위 폴더 경로
    base_path = Path(__file__).resolve().parent.parent

    csv_path = base_path / "temperature.csv"

    # CSV 파일 읽기
    try:
        try:
            df = pd.read_csv(csv_path, encoding="cp949")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")

    except FileNotFoundError:
        st.error(
            f"CSV 파일을 찾을 수 없습니다.\n\n경로: {csv_path}"
        )
        st.stop()

    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()

    # 날짜 처리
    def convert_date(value):

        month_text, year_text = str(value).split("-")

        short_year = int(year_text)

        if short_year >= 7:
            year = 1900 + short_year
        else:
            year = 2000 + short_year

        return pd.to_datetime(
            f"{year}-{month_text}",
            format="%Y-%b"
        )

    df["날짜"] = df["일시"].apply(convert_date)

    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month

    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["평균기온(℃)", "연도", "월"]
    )

    return df


df = load_data()


# -----------------------------------
# 3. 사용자 입력
# -----------------------------------

st.subheader("📌 예측 조건 설정")

col1, col2 = st.columns(2)

with col1:

    selected_month = st.selectbox(
        "예측할 월 선택",
        range(1, 13),
        format_func=lambda x: f"{x}월"
    )

with col2:

    current_max_year = int(df["연도"].max())

    predict_year = st.number_input(
        "예측할 연도 입력",
        min_value=int(df["연도"].min()),
        max_value=3000,
        value=current_max_year + 5,
        step=1
    )

predict_year = int(predict_year)


# -----------------------------------
# 4. 선택한 월 데이터 추출
# -----------------------------------

month_data = df[
    df["월"] == selected_month
].copy()

month_data = month_data.sort_values("연도")

X = month_data[["연도"]]
y = month_data["평균기온(℃)"]

if len(month_data) < 2:
    st.error("예측에 필요한 데이터가 부족합니다.")
    st.stop()


# -----------------------------------
# 5. 선형회귀 모델 학습
# -----------------------------------

model = LinearRegression()

model.fit(X, y)

prediction = model.predict(
    pd.DataFrame({"연도": [predict_year]})
)[0]

slope = model.coef_[0]
intercept = model.intercept_

r2 = model.score(X, y)


# -----------------------------------
# 6. 예측 결과
# -----------------------------------

st.divider()

st.subheader("🔮 기온 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        f"{predict_year}년 {selected_month}월 예측 평균기온",
        f"{prediction:.2f} ℃"
    )

with col2:
    st.metric(
        "선형회귀 기울기",
        f"{slope:.4f}"
    )

with col3:
    st.metric(
        "결정계수 (R²)",
        f"{r2:.4f}"
    )


# -----------------------------------
# 7. 그래프 생성
# -----------------------------------

st.divider()

st.subheader(
    f"📈 {selected_month}월 연도별 평균기온 및 미래 예측"
)

line_years = np.linspace(
    int(month_data["연도"].min()),
    max(predict_year, current_max_year),
    300
)

line_predictions = model.predict(
    pd.DataFrame({"연도": line_years})
)

fig, ax = plt.subplots(figsize=(13, 6))

# 실제 기온 데이터
ax.scatter(
    month_data["연도"],
    month_data["평균기온(℃)"],
    color="royalblue",
    s=30,
    alpha=0.7,
    label="실제 평균기온"
)

# 실제 데이터 연결
ax.plot(
    month_data["연도"],
    month_data["평균기온(℃)"],
    color="skyblue",
    alpha=0.4
)

# 회귀 직선
ax.plot(
    line_years,
    line_predictions,
    color="red",
    linewidth=2.5,
    label="선형회귀 예측 직선"
)

# 미래 예측 지점
ax.scatter(
    predict_year,
    prediction,
    color="darkorange",
    edgecolors="black",
    s=180,
    zorder=5,
    label="미래 예측 기온"
)

# 예측값 설명
ax.annotate(
    f"{predict_year}년\n{prediction:.2f}℃",
    xy=(predict_year, prediction),
    xytext=(12, 15),
    textcoords="offset points",
    fontsize=11,
    fontweight="bold",
    color="darkorange"
)

# 예측 연도 표시
ax.axvline(
    predict_year,
    color="darkorange",
    linestyle="--",
    alpha=0.7
)

ax.set_title(
    f"{selected_month}월 평균기온 선형회귀 분석",
    fontsize=16,
    fontweight="bold"
)

ax.set_xlabel("연도", fontsize=12)
ax.set_ylabel("평균기온 (℃)", fontsize=12)

ax.grid(
    True,
    linestyle="--",
    alpha=0.4
)

ax.legend()

plt.tight_layout()

st.pyplot(fig)

plt.close(fig)


# -----------------------------------
# 8. 선형회귀 알고리즘 설명
# -----------------------------------

st.divider()

st.subheader("📚 선형회귀 알고리즘이란?")

st.write("""
선형회귀는 여러 데이터 사이의 관계를 분석하여
가장 적합한 직선을 찾는 머신러닝 알고리즘입니다.

이번 프로그램에서는 과거의 연도별 평균기온 데이터를
학습하여 연도와 기온 사이의 관계를 분석합니다.

그다음 학습한 직선을 이용해 사용자가 입력한
미래 연도의 평균기온을 예측합니다.
""")

st.latex(r"y = ax + b")

st.markdown("""
- **x** : 연도
- **y** : 평균기온
- **a** : 기울기
- **b** : y절편

선형회귀는 실제 데이터와 직선 사이의 차이를
제곱하여 모두 더한 값이 최소가 되도록 직선을 결정합니다.

이 방법을 최소제곱법이라고 합니다.
""")

st.subheader("⚙️ 현재 학습된 선형회귀 모델")

st.latex(
    rf"\hat{{y}} = {slope:.4f}x + ({intercept:.4f})"
)

st.write(f"""
현재 선택한 {selected_month}월의 과거 기온 데이터를
이용해 학습한 결과입니다.

- 기울기: {slope:.4f}
- y절편: {intercept:.4f}
- 결정계수(R²): {r2:.4f}
- 학습 데이터 개수: {len(month_data)}개
""")

if slope > 0:

    st.info(
        f"기울기가 양수이므로 장기적인 추세에서 "
        f"연간 평균기온이 약 {slope:.4f}℃ 상승하는 경향이 있습니다."
    )

elif slope < 0:

    st.info(
        f"기울기가 음수이므로 장기적인 추세에서 "
        f"연간 평균기온이 약 {abs(slope):.4f}℃ 하락하는 경향이 있습니다."
    )

else:

    st.info("장기적인 기온 변화 추세가 거의 없습니다.")


# -----------------------------------
# 9. 결정계수 설명
# -----------------------------------

st.subheader("📊 결정계수(R²)란?")

st.write("""
결정계수는 회귀 모델이 학습 데이터의 기온 변화를
얼마나 설명하는지 나타내는 지표입니다.

일반적으로 1에 가까울수록 학습 데이터에 대한
설명력이 높다는 의미입니다.

다만 결정계수가 높다고 해서 미래 예측이
반드시 정확하다는 뜻은 아닙니다.
""")

st.divider()

st.caption(
    "서울 월별 평균기온 데이터 | "
    "Linear Regression | "
    "Python · Streamlit · Scikit-learn"
)
