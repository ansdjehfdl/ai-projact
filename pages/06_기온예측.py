
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="서울 기온 예측 시스템",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 월별 평균기온 예측 시스템")

st.write(
    "과거 서울의 평균기온 데이터를 분석하고 "
    "3가지 회귀 알고리즘으로 미래 기온을 예측합니다."
)

st.divider()


# ==========================================
# 2. 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    # pages 폴더의 상위 폴더
    base_path = Path(__file__).resolve().parent.parent

    csv_path = base_path / "temperature.csv"

    # 대체 파일명 확인
    if not csv_path.exists():
        csv_path = base_path / "temperature(2).csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            "상위 폴더에 temperature.csv 파일이 없습니다."
        )

    try:
        data = pd.read_csv(
            csv_path,
            encoding="cp949"
        )
    except UnicodeDecodeError:
        data = pd.read_csv(
            csv_path,
            encoding="utf-8-sig"
        )

    data.columns = data.columns.astype(str).str.strip()

    # 필요한 열 확인
    if "일시" not in data.columns:
        raise ValueError("CSV에 일시 열이 없습니다.")

    if "평균기온(℃)" not in data.columns:
        raise ValueError("CSV에 평균기온(℃) 열이 없습니다.")

    # 날짜 변환
    # Oct-07 -> 2007년 10월
    data["날짜"] = pd.to_datetime(
        data["일시"].astype(str).str.strip(),
        format="%b-%y",
        errors="coerce"
    )

    # 기온 숫자 변환
    data["평균기온(℃)"] = pd.to_numeric(
        data["평균기온(℃)"],
        errors="coerce"
    )

    # 결측값 제거
    data = data.dropna(
        subset=["날짜", "평균기온(℃)"]
    ).copy()

    data["연도"] = data["날짜"].dt.year.astype(int)
    data["월"] = data["날짜"].dt.month.astype(int)

    data = data.sort_values("날짜")

    if data.empty:
        raise ValueError("사용할 수 있는 기온 데이터가 없습니다.")

    return data.reset_index(drop=True)


try:
    df = load_data()

except Exception as error:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(error))
    st.stop()


# ==========================================
# 3. 사용자 입력
# ==========================================

st.subheader("1. 예측 조건 설정")

col1, col2 = st.columns(2)

with col1:

    selected_month = st.selectbox(
        "예측할 월 선택",
        options=list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )

with col2:

    min_year = int(df["연도"].min())
    max_year = int(df["연도"].max())

    predict_year = st.number_input(
        "예측할 연도 입력",
        min_value=min_year,
        max_value=3000,
        value=min(max_year + 5, 3000),
        step=1
    )

predict_year = int(predict_year)


# ==========================================
# 4. 회귀 알고리즘 선택
# ==========================================

st.divider()

st.subheader("2. 회귀 알고리즘 선택")

algorithm_names = [
    "선형회귀 (Linear Regression)",
    "다항 회귀 (Polynomial Regression)",
    "랜덤 포레스트 회귀 (Random Forest Regression)"
]

selected_algorithm = st.selectbox(
    "사용할 회귀 알고리즘을 선택하세요.",
    algorithm_names
)


# ==========================================
# 5. 선택 월 데이터 추출
# ==========================================

month_data = df[
    df["월"] == selected_month
].copy()

month_data = month_data.sort_values("연도")

if len(month_data) < 3:
    st.error("선택한 월의 데이터가 부족합니다.")
    st.stop()

years = month_data["연도"].to_numpy(dtype=float)

temperatures = month_data[
    "평균기온(℃)"
].to_numpy(dtype=float)

# 연도 기준점 설정
base_year = int(years.min())

# 입력 데이터
X = (years - base_year).reshape(-1, 1)

y = temperatures

# 미래 예측 데이터
future_X = np.array([
    [predict_year - base_year]
], dtype=float)


# ==========================================
# 6. 회귀 모델 생성
# ==========================================

models = {

    "선형회귀 (Linear Regression)":
        LinearRegression(),

    "다항 회귀 (Polynomial Regression)":
        make_pipeline(
            PolynomialFeatures(
                degree=2,
                include_bias=False
            ),
            LinearRegression()
        ),

    "랜덤 포레스트 회귀 (Random Forest Regression)":
        RandomForestRegressor(
            n_estimators=300,
            max_depth=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
}


# ==========================================
# 7. 세 가지 알고리즘 학습
# ==========================================

results = {}

for name, model in models.items():

    model.fit(X, y)

    # 학습 데이터 예측
    train_predictions = model.predict(X)

    # 미래 기온 예측
    future_prediction = float(
        model.predict(future_X)[0]
    )

    # 결정계수
    r2 = float(model.score(X, y))

    results[name] = {
        "model": model,
        "prediction": future_prediction,
        "train_predictions": train_predictions,
        "r2": r2
    }


# 선택한 알고리즘
selected_result = results[selected_algorithm]

prediction = selected_result["prediction"]

r2 = selected_result["r2"]


# ==========================================
# 8. 예측 결과
# ==========================================

st.divider()

st.subheader("3. 선택한 알고리즘의 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        f"{predict_year}년 {selected_month}월 예측 기온",
        f"{prediction:.2f} ℃"
    )

with col2:

    st.metric(
        "결정계수 (R²)",
        f"{r2:.4f}"
    )

with col3:

    st.metric(
        "학습 데이터 개수",
        f"{len(month_data)}개"
    )


# ==========================================
# 9. 선택한 알고리즘 그래프
# ==========================================

st.divider()

st.subheader("4. 실제 기온 및 회귀 예측 그래프")

# 회귀선 생성
line_end_year = max(predict_year, max_year)

line_years = np.linspace(
    base_year,
    line_end_year,
    400
)

line_X = (
    line_years - base_year
).reshape(-1, 1)

line_predictions = selected_result["model"].predict(
    line_X
)

fig = go.Figure()

# 실제 평균기온
fig.add_trace(
    go.Scatter(
        x=years,
        y=temperatures,
        mode="markers+lines",
        name="실제 평균기온",
        marker=dict(
            color="#2878D0",
            size=8
        ),
        line=dict(
            color="#87CEEB",
            width=1.5
        ),
        hovertemplate=(
            "연도: %{x:.0f}년<br>"
            "실제 기온: %{y:.2f}℃"
            "<extra></extra>"
        )
    )
)

# 회귀 예측선
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_predictions,
        mode="lines",
        name="회귀 예측 곡선",
        line=dict(
            color="red",
            width=3
        ),
        hovertemplate=(
            "연도: %{x:.0f}년<br>"
            "예측 기온: %{y:.2f}℃"
            "<extra></extra>"
        )
    )
)

# 미래 예측 지점
fig.add_trace(
    go.Scatter(
        x=[predict_year],
        y=[prediction],
        mode="markers+text",
        name="미래 예측 기온",
        marker=dict(
            color="darkorange",
            size=16,
            line=dict(
                color="black",
                width=1
            )
        ),
        text=[
            f"{predict_year}년<br>{prediction:.2f}℃"
        ],
        textposition="top center",
        textfont=dict(
            color="darkorange",
            size=13
        )
    )
)

# 미래 연도 표시
fig.add_vline(
    x=predict_year,
    line_dash="dash",
    line_color="darkorange",
    line_width=2
)

# 그래프 디자인
fig.update_layout(
    title=f"{selected_month}월 평균기온 분석 - {selected_algorithm}",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    template="plotly_white",
    height=560,
    hovermode="closest",
    font=dict(
        family="Arial, sans-serif",
        size=13
    ),
    legend=dict(
        orientation="h",
        y=1.12,
        x=0.5,
        xanchor="center"
    ),
    margin=dict(
        l=60,
        r=40,
        t=100,
        b=60
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption(
    "파란색 점과 하늘색 선: 실제 기온 | "
    "빨간색 선: 회귀 예측 곡선 | "
    "주황색 점: 미래 예측 기온"
)


# ==========================================
# 10. 알고리즘별 예측값 비교
# ==========================================

st.divider()

st.subheader("5. 세 가지 알고리즘 예측 결과 비교")

comparison_rows = []

for name in algorithm_names:

    comparison_rows.append({
        "알고리즘": name,
        "예측 기온(℃)": results[name]["prediction"],
        "결정계수(R²)": results[name]["r2"]
    })

comparison_df = pd.DataFrame(comparison_rows)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "예측 기온(℃)": st.column_config.NumberColumn(
            format="%.2f ℃"
        ),
        "결정계수(R²)": st.column_config.NumberColumn(
            format="%.4f"
        )
    }
)


# ==========================================
# 11. 알고리즘별 예측 기온 막대그래프
# ==========================================

st.subheader("📊 알고리즘별 예측 기온 차이")

comparison_fig = go.Figure()

comparison_fig.add_trace(
    go.Bar(
        x=algorithm_names,
        y=[
            results[name]["prediction"]
            for name in algorithm_names
        ],
        marker_color=[
            "#2878D0",
            "#16A085",
            "#E67E22"
        ],
        text=[
            f"{results[name]['prediction']:.2f}℃"
            for name in algorithm_names
        ],
        textposition="outside",
        cliponaxis=False
    )
)

comparison_fig.update_layout(
    title=f"{predict_year}년 {selected_month}월 예측 결과 비교",
    xaxis_title="회귀 알고리즘",
    yaxis_title="예측 평균기온 (℃)",
    template="plotly_white",
    height=450,
    showlegend=False,
    font=dict(
        family="Arial, sans-serif",
        size=12
    ),
    margin=dict(
        t=70,
        b=110
    )
)

st.plotly_chart(
    comparison_fig,
    use_container_width=True
)


# ==========================================
# 12. 알고리즘별 결정계수 비교
# ==========================================

st.subheader("📈 알고리즘별 결정계수 비교")

r2_fig = go.Figure()

r2_fig.add_trace(
    go.Bar(
        x=algorithm_names,
        y=[
            results[name]["r2"]
            for name in algorithm_names
        ],
        marker_color=[
            "#2878D0",
            "#16A085",
            "#E67E22"
        ],
        text=[
            f"{results[name]['r2']:.4f}"
            for name in algorithm_names
        ],
        textposition="outside",
        cliponaxis=False
    )
)

r2_fig.update_layout(
    title="학습 데이터 기준 결정계수 비교",
    xaxis_title="회귀 알고리즘",
    yaxis_title="결정계수 (R²)",
    template="plotly_white",
    height=430,
    showlegend=False,
    font=dict(
        family="Arial, sans-serif",
        size=12
    ),
    margin=dict(
        t=70,
        b=110
    )
)

st.plotly_chart(
    r2_fig,
    use_container_width=True
)

st.caption(
    "결정계수는 학습 데이터에 대한 설명력입니다. "
    "높은 결정계수가 미래 예측의 정확성을 보장하지는 않습니다."
)


# ==========================================
# 13. 선택한 알고리즘의 원리 설명
# ==========================================

st.divider()

st.subheader("6. 회귀 알고리즘 작동 원리")

if selected_algorithm == algorithm_names[0]:

    st.markdown("""
    ### 선형회귀 (Linear Regression)

    선형회귀는 데이터 사이의 관계를 분석하여
    가장 적합한 직선을 찾는 알고리즘입니다.

    **작동 과정**

    1. 과거 연도별 평균기온 데이터를 수집합니다.
    2. 연도와 평균기온 사이의 관계를 분석합니다.
    3. 실제 데이터와 직선 사이의 오차 제곱합이 최소가 되는 직선을 찾습니다.
    4. 해당 직선을 이용하여 미래 기온을 예측합니다.

    **특징**

    - 전체적인 상승 및 하락 추세를 파악하기 좋습니다.
    - 계산이 빠르고 이해하기 쉽습니다.
    - 복잡한 곡선 형태의 관계를 표현하기 어렵습니다.
    """)

    st.latex(r"\hat{y} = ax + b")


elif selected_algorithm == algorithm_names[1]:

    st.markdown("""
    ### 다항 회귀 (Polynomial Regression)

    다항 회귀는 데이터를 곡선 형태로 표현하는 알고리즘입니다.

    이번 프로그램에서는 2차 다항식을 사용합니다.

    **작동 과정**

    1. 과거 연도별 평균기온 데이터를 수집합니다.
    2. 연도 데이터의 제곱값을 추가로 생성합니다.
    3. 연도와 제곱한 연도를 함께 분석합니다.
    4. 곡선 형태의 관계를 학습합니다.
    5. 학습한 곡선을 이용하여 미래 기온을 예측합니다.

    **특징**

    - 직선으로 표현하기 어려운 곡선 형태를 학습합니다.
    - 비선형적인 관계를 표현할 수 있습니다.
    - 먼 미래를 예측할 때 곡선이 과도하게 변할 수 있습니다.
    """)

    st.latex(r"\hat{y} = ax^2 + bx + c")


else:

    st.markdown("""
    ### 랜덤 포레스트 회귀 (Random Forest Regression)

    랜덤 포레스트는 여러 개의 의사결정나무를 학습시키고
    각각의 예측 결과를 평균하여 최종 결과를 계산합니다.

    **작동 과정**

    1. 과거 기온 데이터를 이용하여 여러 학습용 데이터를 구성합니다.
    2. 각각의 데이터로 의사결정나무를 학습시킵니다.
    3. 각 의사결정나무가 독립적으로 기온을 예측합니다.
    4. 여러 나무의 예측 결과를 평균하여 최종 기온을 계산합니다.

    **특징**

    - 복잡한 데이터 관계를 학습할 수 있습니다.
    - 여러 의사결정나무의 결과를 종합합니다.
    - 학습 데이터 범위 밖의 미래 추세를 예측하는 데는 한계가 있습니다.
    """)

    st.latex(
        r"\hat{y} = \frac{1}{N}\sum_{i=1}^{N}T_i(x)"
    )


# ==========================================
# 14. 예측 결과 해석
# ==========================================

st.divider()

st.subheader("7. 예측 결과 분석")

highest_name = max(
    algorithm_names,
    key=lambda name: results[name]["prediction"]
)

lowest_name = min(
    algorithm_names,
    key=lambda name: results[name]["prediction"]
)

highest_value = results[highest_name]["prediction"]
lowest_value = results[lowest_name]["prediction"]

difference = highest_value - lowest_value

st.write(
    f"가장 높은 예측값은 **{highest_name}**이며 "
    f"예측 기온은 **{highest_value:.2f}℃**입니다."
)

st.write(
    f"가장 낮은 예측값은 **{lowest_name}**이며 "
    f"예측 기온은 **{lowest_value:.2f}℃**입니다."
)

st.info(
    f"세 알고리즘의 최고 예측값과 최저 예측값 차이는 "
    f"{difference:.2f}℃입니다."
)

st.warning(
    "랜덤 포레스트는 학습 데이터의 범위를 벗어난 미래 연도에서 "
    "장기적인 기온 상승 또는 하락 추세를 이어서 예측하는 데 한계가 있습니다. "
    "결정계수가 높다고 미래 예측이 반드시 정확한 것은 아닙니다."
)


# ==========================================
# 15. 마무리
# ==========================================

st.divider()

st.subheader("📌 전체 알고리즘 정리")

st.markdown("""
| 알고리즘 | 학습 방식 | 주요 특징 |
|---|---|---|
| 선형회귀 | 직선 | 전체적인 추세 분석 |
| 다항 회귀 | 곡선 | 비선형 관계 분석 |
| 랜덤 포레스트 | 여러 의사결정나무 | 복잡한 관계 분석 |

동일한 과거 기온 데이터를 사용해도 알고리즘의 학습 방식이 다르기 때문에
미래 기온 예측 결과가 달라질 수 있습니다.
""")

st.caption(
    "서울 월별 평균기온 분석 | "
    "Linear Regression · Polynomial Regression · "
    "Random Forest Regression | "
    "Python · Streamlit · Plotly · Scikit-learn"
)
