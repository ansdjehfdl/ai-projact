
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error, r2_score


# ==========================================
# EARTH FUTURE AI
# ==========================================

st.set_page_config(
    page_title="EARTH FUTURE AI",
    page_icon="🌍",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

CANDIDATE_PATHS = [
    BASE_DIR / "data" / "earth_environment.csv",
    BASE_DIR / "earth_environment.csv",
]

COLUMN_INFO = {
    "Sea_Level_mm_from_1993_2008_avg": {
        "label": "해수면 높이 변화",
        "unit": "mm",
        "description": "1993~2008년 평균 기준 해수면 변화",
        "color": "#2586C8",
    },
    "CO2_Global_Annual_Mean_ppm": {
        "label": "이산화탄소 농도",
        "unit": "ppm",
        "description": "전 지구 연평균 CO2 농도",
        "color": "#E58A36",
    },
    "FAO_Area_Mean_Temp_Change_C": {
        "label": "기온 변화 참고 지표",
        "unit": "°C",
        "description": "FAO 지역별 보고값의 단순 평균",
        "color": "#D9536F",
    },
}

MODEL_NAMES = {
    "Linear Regression": "선형 회귀",
    "Random Forest": "랜덤 포레스트",
    "Gradient Boosting": "그래디언트 부스팅",
}


# ==========================================
# 데이터 불러오기
# ==========================================

def load_data():

    for path in CANDIDATE_PATHS:

        if path.exists():

            return pd.read_csv(path), path

    raise FileNotFoundError(
        "earth_environment.csv 파일을 찾을 수 없습니다."
    )


# ==========================================
# 머신러닝 알고리즘
# ==========================================

def make_models():

    return {

        "Linear Regression": LinearRegression(),

        "Random Forest": RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=2,
            loss="huber",
            random_state=42
        )
    }


# ==========================================
# 모델 성능 평가
# ==========================================

def evaluate_models(series):

    clean = series.dropna().sort_index()

    clean = clean[
        ~clean.index.duplicated(keep="last")
    ]

    if len(clean) < 12:

        return None, None, (
            f"관측값이 {len(clean)}개뿐이라 "
            "모델 비교에 필요한 데이터가 부족합니다."
        )

    X = clean.index.to_numpy(
        dtype=float
    ).reshape(-1, 1)

    y = clean.to_numpy(dtype=float)

    split_at = int(len(clean) * 0.8)

    split_at = min(
        max(split_at, 5),
        len(clean) - 2
    )

    X_train = X[:split_at]
    X_test = X[split_at:]

    y_train = y[:split_at]
    y_test = y[split_at:]

    results = []

    for name, model in make_models().items():

        model.fit(X_train, y_train)

        pred = model.predict(X_test)

        results.append({

            "알고리즘": MODEL_NAMES[name],

            "MAE": mean_absolute_error(
                y_test, pred
            ),

            "RMSE": np.sqrt(
                mean_squared_error(
                    y_test, pred
                )
            ),

            "R²": r2_score(
                y_test, pred
            )

        })

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values("MAE")

    return result_df, clean, None


# ==========================================
# 미래 예측
# ==========================================

def fit_and_forecast(
    clean,
    model_name,
    end_year
):

    X = clean.index.to_numpy(
        dtype=float
    ).reshape(-1, 1)

    y = clean.to_numpy(dtype=float)

    model = make_models()[model_name]

    model.fit(X, y)

    last_year = int(clean.index.max())

    future_years = np.arange(
        last_year + 1,
        end_year + 1
    )

    if len(future_years) == 0:

        return model, pd.DataFrame(
            columns=["Year", "Prediction"]
        )

    future_X = future_years.astype(
        float
    ).reshape(-1, 1)

    predictions = model.predict(future_X)

    forecast = pd.DataFrame({

        "Year": future_years,

        "Prediction": predictions

    })

    return model, forecast


# ==========================================
# 메인 디자인
# ==========================================

st.markdown(
    """
    <div style="padding: 8px 0 2px 0;">
      <div style="
        font-size:13px;
        letter-spacing:3px;
        color:#65A9D8;
        font-weight:700;
      ">
        GLOBAL ENVIRONMENT ANALYSIS
      </div>

      <h1 style="margin:0; font-size:42px;">
        🌍 EARTH FUTURE AI
      </h1>

      <p style="
        color:#9AA4B2;
        font-size:16px;
        margin-top:5px;
      ">
        과거 환경 데이터를 분석하고
        미래 변화를 예측합니다.
      </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# 데이터 불러오기
# ==========================================

try:

    df, loaded_path = load_data()

except Exception as exc:

    st.error(str(exc))

    st.stop()


required_columns = [
    "Year",
    *COLUMN_INFO.keys()
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"CSV에 필요한 열이 없습니다: {missing_columns}"
    )

    st.stop()


df = df[required_columns].copy()

for col in required_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=["Year"]
).copy()

df["Year"] = df["Year"].astype(int)

df = df.sort_values(
    "Year"
).drop_duplicates(
    "Year",
    keep="last"
)


# ==========================================
# 사이드바 설정
# ==========================================

st.sidebar.title("분석 설정")

st.sidebar.caption(
    "분석할 환경 요소를 선택하세요."
)

selected_labels = st.sidebar.multiselect(

    "환경 요소 선택",

    options=[
        COLUMN_INFO[c]["label"]
        for c in COLUMN_INFO
    ],

    default=[
        COLUMN_INFO[c]["label"]
        for c in COLUMN_INFO
    ]

)

selected_columns = [

    c for c, info in COLUMN_INFO.items()

    if info["label"] in selected_labels

]


end_year = st.sidebar.slider(

    "예측 종료 연도",

    min_value=2030,

    max_value=2200,

    value=2200,

    step=10

)


selected_model_label = st.sidebar.selectbox(

    "예측 알고리즘",

    options=list(MODEL_NAMES.values())

)

selected_model = next(

    k for k, v in MODEL_NAMES.items()

    if v == selected_model_label

)


st.sidebar.divider()

st.sidebar.info(
    "과거 검증 성능이 2200년까지의 "
    "예측 정확도를 보장하지는 않습니다."
)


if not selected_columns:

    st.warning(
        "환경 요소를 하나 이상 선택해 주세요."
    )

    st.stop()


# ==========================================
# 데이터 개요
# ==========================================

st.subheader("📊 데이터 개요")

col1, col2, col3 = st.columns(3)

col1.metric(
    "데이터 연도 범위",
    f"{df['Year'].min()}~{df['Year'].max()}"
)

col2.metric(
    "연도 행 수",
    f"{len(df):,}개"
)

col3.metric(
    "분석 환경 요소",
    f"{len(selected_columns)}개"
)


with st.expander(
    "데이터 품질 및 변수 설명 보기"
):

    quality_rows = []

    for col, info in COLUMN_INFO.items():

        valid = df.dropna(
            subset=[col]
        )

        quality_rows.append({

            "환경 요소": info["label"],

            "단위": info["unit"],

            "관측 시작": (
                int(valid["Year"].min())
                if len(valid) else "없음"
            ),

            "관측 종료": (
                int(valid["Year"].max())
                if len(valid) else "없음"
            ),

            "관측값 수": int(
                df[col].count()
            ),

            "결측값 수": int(
                df[col].isna().sum()
            )

        })

    st.dataframe(
        pd.DataFrame(quality_rows),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "결측값은 0으로 바꾸지 않고 "
        "실제 관측값만 학습에 사용합니다."
    )

    st.caption(
        f"데이터 파일: {loaded_path.name}"
    )


# ==========================================
# 환경 데이터 분석 및 예측
# ==========================================

st.divider()

st.subheader(
    "📈 과거 데이터와 미래 변화 예측"
)

st.caption(
    "실선은 실제 관측값, 점선은 미래 예측값입니다."
)

forecast_downloads = []

comparison_downloads = []


for col in selected_columns:

    info = COLUMN_INFO[col]

    st.markdown(
        f"### {info['label']}"
    )

    st.caption(
        f"단위: {info['unit']} · {info['description']}"
    )

    series = (
        df.set_index("Year")[col]
        .dropna()
        .sort_index()
    )

    comparison, clean, error = evaluate_models(
        series
    )

    if error:

        st.warning(error)

        continue


    latest_year = int(
        clean.index.max()
    )

    latest_value = float(
        clean.iloc[-1]
    )


    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "마지막 관측 연도",
        f"{latest_year}년"
    )

    metric2.metric(
        "마지막 관측값",
        f"{latest_value:,.2f} {info['unit']}"
    )

    metric3.metric(
        "사용 알고리즘",
        MODEL_NAMES[selected_model]
    )


    # 모델 성능 비교

    st.markdown(
        "**알고리즘 성능 비교**"
    )

    display_comparison = comparison.copy()

    for metric in ["MAE", "RMSE", "R²"]:

        display_comparison[metric] = (
            display_comparison[metric]
            .map(lambda x: f"{x:,.4f}")
        )

    st.dataframe(
        display_comparison,
        use_container_width=True,
        hide_index=True
    )


    # 미래 예측

    _, forecast = fit_and_forecast(

        clean,

        selected_model,

        end_year

    )


    if len(forecast):

        forecast.insert(
            0,
            "환경 요소",
            info["label"]
        )

        forecast["단위"] = info["unit"]

        forecast_downloads.append(
            forecast
        )


    comp_export = comparison.copy()

    comp_export.insert(
        0,
        "환경 요소",
        info["label"]
    )

    comparison_downloads.append(
        comp_export
    )


    # 그래프

    fig, ax = plt.subplots(
        figsize=(11, 4.5)
    )

    ax.plot(

        clean.index,

        clean.values,

        label="Observed data",

        linewidth=2,

        color=info["color"]

    )


    if len(forecast):

        ax.plot(

            forecast["Year"],

            forecast["Prediction"],

            label=f"Forecast ({MODEL_NAMES[selected_model]})",

            linewidth=2,

            linestyle="--",

            color="#8C78C8"

        )


    ax.axvline(

        latest_year,

        color="gray",

        linestyle=":",

        linewidth=1

    )

    ax.set_xlabel("Year")

    ax.set_ylabel(
        f"{info['label']} ({info['unit']})"
    )

    ax.grid(alpha=0.25)

    ax.legend()

    fig.tight_layout()

    st.pyplot(
        fig,
        use_container_width=True
    )

    plt.close(fig)


    # 주요 연도 예측값

    if len(forecast):

        target_years = [
            2030, 2050, 2100, 2200
        ]

        target_years = [

            y for y in target_years

            if latest_year < y <= end_year

        ]

        if target_years:

            points = forecast[
                forecast["Year"].isin(target_years)
            ][["Year", "Prediction"]].copy()

            points["예측값"] = points[
                "Prediction"
            ].map(
                lambda x: f"{x:,.3f} {info['unit']}"
            )

            st.markdown(
                "**주요 연도 예측값**"
            )

            st.dataframe(
                points[["Year", "예측값"]],
                use_container_width=True,
                hide_index=True
            )

    st.divider()


# ==========================================
# 분석 결과 다운로드
# ==========================================

st.subheader(
    "⬇️ 분석 결과 다운로드"
)

left, right = st.columns(2)


with left:

    if forecast_downloads:

        all_forecasts = pd.concat(
            forecast_downloads,
            ignore_index=True
        )

        st.download_button(

            "미래 예측 CSV 다운로드",

            data=all_forecasts.to_csv(
                index=False
            ).encode("utf-8-sig"),

            file_name="earth_future_predictions.csv",

            mime="text/csv",

            use_container_width=True

        )


with right:

    if comparison_downloads:

        all_comparisons = pd.concat(
            comparison_downloads,
            ignore_index=True
        )

        st.download_button(

            "알고리즘 비교 CSV 다운로드",

            data=all_comparisons.to_csv(
                index=False
            ).encode("utf-8-sig"),

            file_name="earth_model_comparison.csv",

            mime="text/csv",

            use_container_width=True

        )


# ==========================================
# 주의사항
# ==========================================

st.subheader(
    "⚠️ 예측 결과 해석 시 주의사항"
)

st.warning(
    "이 프로그램은 지구가 멸망하는 날짜를 계산하지 않습니다. "
    "과거 관측 추세를 이용한 교육용 환경 변화 시나리오입니다."
)

st.markdown(
    """
    - 선형 회귀는 과거 추세를 직선으로 연장합니다.
    - 랜덤 포레스트와 그래디언트 부스팅은
      관측 범위를 벗어난 미래를 잘 외삽하지 못합니다.
    - 기온 데이터는 공식 전 지구 평균기온이 아닙니다.
    - 환경 데이터마다 관측 기간이 다릅니다.
    - 실제 기후 전망에는 IPCC 시나리오와
      물리 기반 기후 모델도 필요합니다.
    """
)

st.caption(
    "EARTH FUTURE AI · Educational environmental trend analysis"
)

