```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 월별 평균기온 회귀 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 회귀 예측")

st.write(
    "과거 서울의 월별 평균기온 데이터를 이용하여 "
    "여러 회귀 알고리즘으로 미래 기온을 예측하고 결과를 비교합니다."
)

st.divider()


# ==========================================
# 2. CSV 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    # 현재 Python 파일은 pages 폴더
    # CSV는 상위 폴더
    base_path = Path(__file__).resolve().parent.parent

    csv_path = base_path / "temperature.csv"

    # 혹시 파일명이 temperature(2).csv인 경우
    if not csv_path.exists():
        csv_path = base_path / "temperature(2).csv"

    if not csv_path.exists():
        st.error(
            "CSV 파일을 찾을 수 없습니다.\n\n"
            "상위 폴더에 temperature.csv 파일을 넣어주세요."
        )
        st.stop()

    # CSV 인코딩 처리
    try:
        df = pd.read_csv(
            csv_path,
            encoding="cp949"
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            csv_path,
            encoding="utf-8-sig"
        )

    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()

    # 필요한 열 확인
    required_columns = [
        "일시",
        "평균기온(℃)"
    ]

    for column in required_columns:

        if column not in df.columns:

            st.error(
                f"CSV 파일에 '{column}' 열이 없습니다."
            )

            st.stop()

    # ======================================
    # 날짜 변환
    # 예: Oct-07 → 2007-10
    # ======================================

    df["날짜"] = pd.to_datetime(
        df["일시"],
        format="%b-%y",
        errors="coerce"
    )

    # 날짜 변환에 실패한 데이터 제거
    df = df.dropna(
        subset=["날짜"]
    )

    # 연도 / 월 생성
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month

    # 평균기온 숫자 변환
    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    # 결측값 제거
    df = df.dropna(
        subset=[
            "연도",
            "월",
            "평균기온(℃)"
        ]
    )

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    df = df.sort_values(
        "연도"
    )

    return df


df = load_data()


# ==========================================
# 3. 데이터 정보
# ==========================================

min_year = int(df["연도"].min())
max_year = int(df["연도"].max())


# ==========================================
# 4. 사용자 입력
# ==========================================

st.subheader("📌 예측 조건")

col1, col2 = st.columns(2)

with col1:

    selected_month = st.selectbox(
        "예측할 월",
        options=list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )


with col2:

    predict_year = st.number_input(
        "예측할 연도",
        min_value=min_year,
        max_value=3000,
        value=max_year + 5,
        step=1
    )

predict_year = int(predict_year)


# ==========================================
# 5. 회귀 알고리즘 선택
# ==========================================

st.subheader("🤖 회귀 알고리즘 선택")

algorithm = st.radio(
    "사용할 회귀 알고리즘을 선택하세요.",
    [
        "선형회귀",
        "랜덤 포레스트 회귀",
        "서포트 벡터 회귀(SVR)",
        "3개 알고리즘 비교"
    ],
    horizontal=True
)


st.info(
    "같은 데이터라도 회귀 알고리즘에 따라 "
    "예측 결과가 달라질 수 있습니다. "
    "특히 '3개 알고리즘 비교'를 선택하면 차이를 한눈에 볼 수 있습니다."
)


# ==========================================
# 6. 선택한 월 데이터
# ==========================================

month_data = df[
    df["월"] == selected_month
].copy()

month_data = month_data.sort_values(
    "연도"
)

if len(month_data) < 3:

    st.error(
        "선택한 월의 데이터가 충분하지 않습니다."
    )

    st.stop()


X = month_data[
    ["연도"]
]

y = month_data[
    "평균기온(℃)"
]


# ==========================================
# 7. 모델 생성 함수
# ==========================================

def create_models():

    models = {}

    # --------------------------------------
    # ① 선형회귀
    # --------------------------------------

    models["선형회귀"] = LinearRegression()


    # --------------------------------------
    # ② 랜덤 포레스트 회귀
    # --------------------------------------

    models["랜덤 포레스트 회귀"] = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        max_depth=6,
        min_samples_leaf=2
    )


    # --------------------------------------
    # ③ SVR
    # --------------------------------------

    models["서포트 벡터 회귀(SVR)"] = make_pipeline(
        StandardScaler(),
        SVR(
            kernel="rbf",
            C=100,
            gamma="scale",
            epsilon=0.1
        )
    )

    return models


models = create_models()


# ==========================================
# 8. 모델 학습 및 예측
# ==========================================

results = {}

for name, model in models.items():

    model.fit(
        X,
        y
    )

    # 미래 예측
    prediction = model.predict(
        pd.DataFrame({
            "연도": [predict_year]
        })
    )[0]

    # 학습 데이터 예측
    fitted = model.predict(X)

    # R²
    r2 = r2_score(
        y,
        fitted
    )

    results[name] = {
        "model": model,
        "prediction": prediction,
        "fitted": fitted,
        "r2": r2
    }


# ==========================================
# 9. 예측 결과 표시
# ==========================================

st.divider()

st.subheader(
    f"🔮 {predict_year}년 {selected_month}월 예측 결과"
)


if algorithm == "3개 알고리즘 비교":

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "선형회귀",
            f"{results['선형회귀']['prediction']:.2f} ℃"
        )

    with col2:

        st.metric(
            "랜덤 포레스트",
            f"{results['랜덤 포레스트 회귀']['prediction']:.2f} ℃"
        )

    with col3:

        st.metric(
            "SVR",
            f"{results['서포트 벡터 회귀(SVR)']['prediction']:.2f} ℃"
        )

else:

    prediction = results[
        algorithm
    ]["prediction"]

    r2 = results[
        algorithm
    ]["r2"]

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            f"{algorithm} 예측 기온",
            f"{prediction:.2f} ℃"
        )

    with col2:

        st.metric(
            "학습 데이터 R²",
            f"{r2:.4f}"
        )


# ==========================================
# 10. 그래프용 연도 생성
# ==========================================

line_years = np.linspace(
    min_year,
    max(
        max_year,
        predict_year
    ),
    500
)

line_df = pd.DataFrame({
    "연도": line_years
})


# ==========================================
# 11. 그래프 생성
# ==========================================

st.divider()

st.subheader(
    f"📈 {selected_month}월 회귀 알고리즘 분석"
)


fig = go.Figure()


# ==========================================
# 실제 데이터
# ==========================================

fig.add_trace(
    go.Scatter(
        x=month_data["연도"],
        y=month_data["평균기온(℃)"],
        mode="markers",
        name="실제 평균기온",
        marker=dict(
            size=8,
            color="#2878D0"
        ),
        hovertemplate=
            "연도: %{x}년<br>" +
            "평균기온: %{y:.2f}℃" +
            "<extra></extra>"
    )
)


# ==========================================
# 실제 데이터 연결선
# ==========================================

fig.add_trace(
    go.Scatter(
        x=month_data["연도"],
        y=month_data["평균기온(℃)"],
        mode="lines",
        name="실제 기온 변화",
        line=dict(
            color="#87CEEB",
            width=1.5
        ),
        hoverinfo="skip"
    )
)


# ==========================================
# 알고리즘별 회귀선
# ==========================================

colors = {
    "선형회귀": "red",
    "랜덤 포레스트 회귀": "green",
    "서포트 벡터 회귀(SVR)": "purple"
}


# 선택된 알고리즘만 표시할지 결정
if algorithm == "3개 알고리즘 비교":

    selected_models = list(
        models.keys()
    )

else:

    selected_models = [
        algorithm
    ]


for name in selected_models:

    model = results[name]["model"]

    predictions = model.predict(
        line_df
    )

    fig.add_trace(
        go.Scatter(
            x=line_years,
            y=predictions,
            mode="lines",
            name=name,
            line=dict(
                color=colors[name],
                width=3
            ),
            hovertemplate=
                "연도: %{x:.0f}년<br>" +
                "예측 기온: %{y:.2f}℃" +
                "<extra>" +
                name +
                "</extra>"
        )
    )


# ==========================================
# 알고리즘별 미래 예측 지점
# ==========================================

for name in selected_models:

    prediction = results[
        name
    ]["prediction"]

    fig.add_trace(
        go.Scatter(
            x=[predict_year],
            y=[prediction],
            mode="markers+text",
            name=f"{name} 예측",
            marker=dict(
                color=colors[name],
                size=14,
                line=dict(
                    color="black",
                    width=1
                )
            ),
            text=[
                f"{prediction:.2f}℃"
            ],
            textposition="top center",
            textfont=dict(
                size=12
            ),
            hovertemplate=
                "예측 연도: %{x}년<br>" +
                "예측 기온: %{y:.2f}℃" +
                "<extra>" +
                name +
                "</extra>"
        )
    )


# ==========================================
# 예측 연도 세로선
# ==========================================

fig.add_vline(
    x=predict_year,
    line_width=2,
    line_dash="dash",
    line_color="orange"
)


# ==========================================
# 그래프 디자인
# ==========================================

fig.update_layout(

    title=dict(
        text=(
            f"{selected_month}월 평균기온 "
            f"회귀 알고리즘 비교"
        ),
        font=dict(
            size=21
        ),
        x=0.5
    ),

    xaxis=dict(
        title="연도",
        showgrid=True,
        gridcolor="lightgray",
        dtick=2
    ),

    yaxis=dict(
        title="평균기온 (℃)",
        showgrid=True,
        gridcolor="lightgray"
    ),

    font=dict(
        family="Arial, sans-serif",
        size=13,
        color="#333333"
    ),

    hovermode="closest",

    template="plotly_white",

    height=620,

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),

    margin=dict(
        l=60,
        r=40,
        t=110,
        b=60
    )
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================
# 12. 알고리즘별 예측값 비교표
# ==========================================

st.divider()

st.subheader("📊 알고리즘별 예측값 비교")

comparison_data = []

for name in models.keys():

    comparison_data.append({
        "알고리즘": name,
        "예측 기온(℃)": round(
            results[name]["prediction"],
            2
        ),
        "R²": round(
            results[name]["r2"],
            4
        )
    })

comparison_df = pd.DataFrame(
    comparison_data
)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 13. 알고리즘별 차이 계산
# ==========================================

if algorithm == "3개 알고리즘 비교":

    st.subheader("🔍 알고리즘별 예측 차이")

    predictions_only = {
        name: results[name]["prediction"]
        for name in models.keys()
    }

    min_prediction = min(
        predictions_only.values()
    )

    max_prediction = max(
        predictions_only.values()
    )

    difference = (
        max_prediction -
        min_prediction
    )

    st.write(
        f"세 알고리즘의 예측값 차이는 "
        f"최대 **{difference:.2f}℃**입니다."
    )

    st.info(
        "같은 과거 기온 데이터를 사용하더라도 "
        "알고리즘이 데이터를 학습하는 방식이 다르기 때문에 "
        "미래 예측값이 달라질 수 있습니다."
    )


# ==========================================
# 14. 알고리즘 설명
# ==========================================

st.divider()

st.subheader("📚 사용한 회귀 알고리즘")


# ------------------------------------------
# 선형회귀
# ------------------------------------------

st.markdown("### 🔴 1. 선형회귀 (Linear Regression)")

st.write("""
선형회귀는 데이터를 가장 잘 설명하는 하나의 직선을
찾아서 미래의 값을 예측하는 방법입니다.

과거 연도와 평균기온의 관계가 일정한 방향으로
변화한다고 가정하고 추세를 계산합니다.

따라서 그래프에서는 하나의 직선으로
전체적인 기온 변화 추세가 나타납니다.
""")


st.latex(
    r"\hat{y} = ax + b"
)


# ------------------------------------------
# 랜덤 포레스트
# ------------------------------------------

st.markdown(
    "### 🟢 2. 랜덤 포레스트 회귀 (Random Forest Regression)"
)

st.write("""
랜덤 포레스트 회귀는 여러 개의 결정트리를 만들고
각 결정트리가 예측한 결과를 평균하여 최종 예측값을 만드는 방법입니다.

하나의 직선만 사용하는 선형회귀와 달리
데이터의 복잡한 패턴을 표현할 수 있습니다.

여러 개의 트리를 사용하기 때문에
하나의 모델에 의존하는 것보다 안정적인 예측을 할 수 있습니다.
""")


# ------------------------------------------
# SVR
# ------------------------------------------

st.markdown(
    "### 🟣 3. 서포트 벡터 회귀 (SVR)"
)

st.write("""
SVR은 서포트 벡터 머신을 회귀 문제에 적용한 알고리즘입니다.

이번 프로그램에서는 RBF 커널을 사용하여
단순한 직선뿐만 아니라 곡선 형태의 관계도
학습할 수 있도록 했습니다.

따라서 선형회귀와 다른 형태의 예측선을 만들 수 있습니다.
""")


# ==========================================
# 15. 알고리즘 차이 정리
# ==========================================

st.subheader("🧠 세 알고리즘의 차이")

difference_table = pd.DataFrame({
    "알고리즘": [
        "선형회귀",
        "랜덤 포레스트 회귀",
        "SVR"
    ],

    "특징": [
        "하나의 직선으로 추세를 표현",
        "여러 결정트리의 결과를 평균",
        "커널을 이용해 비선형 관계 표현"
    ],

    "장점": [
        "간단하고 이해하기 쉬움",
        "복잡한 패턴을 학습할 수 있음",
        "비선형 패턴을 표현할 수 있음"
    ],

    "그래프 형태": [
        "직선",
        "구간에 따라 변화하는 곡선",
        "부드러운 곡선"
    ]
})


st.dataframe(
    difference_table,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 16. 주의사항
# ==========================================

st.divider()

st.subheader("⚠️ 예측 결과 해석 시 주의사항")

st.write("""
이 프로그램은 과거의 기온 데이터만을 이용하여
미래의 기온을 예측합니다.

실제 기온은 기후 변화, 대기 상태, 강수량,
해류 등 다양한 요인의 영향을 받기 때문에
모델의 예측값과 실제 미래 기온에는 차이가 생길 수 있습니다.

또한 세 알고리즘 중 R²가 가장 높은 모델이
반드시 미래 예측에서도 가장 정확하다고 보장할 수는 없습니다.
""")

st.divider()

st.caption(
    "서울 월별 평균기온 분석 | "
    "Linear Regression · Random Forest Regression · SVR | "
    "Python · Streamlit · Plotly · Scikit-learn"
)
```
