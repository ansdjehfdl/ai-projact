
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="EARTH FUTURE AI",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 EARTH FUTURE AI")
st.subheader("인공지능을 활용한 지구 환경 변화 분석 및 미래 예측")

st.markdown("""
지구 환경 데이터를 분석하고 머신러닝을 활용하여
미래의 환경 변화 추세를 예측하는 프로젝트입니다.
""")

st.divider()


# --------------------------------------------------
# 2. CSV 파일 불러오기
# --------------------------------------------------

# 현재 app.py는 pages 폴더 안에 있음
# parent.parent를 사용하면 프로젝트 최상위 폴더로 이동함

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "earth_environment.csv"


@st.cache_data
def load_data():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다.\n"
            f"찾는 위치: {CSV_PATH}"
        )

    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding="cp949")

    return df


try:
    df = load_data()

except Exception as e:
    st.error("데이터 파일을 불러오지 못했습니다.")
    st.code(str(e))

    st.info("""
    GitHub 파일 구조를 확인해 주세요.

    EARTH_FUTURE_AI/
    ├── earth_environment.csv
    ├── requirements.txt
    └── pages/
        └── app.py
    """)

    st.stop()


# --------------------------------------------------
# 3. 데이터 열 설정
# --------------------------------------------------

COLUMN_INFO = {
    "해수면 상승": {
        "column": "Sea_Level_mm_from_1993_2008_avg",
        "unit": "mm",
        "description": "1993~2008년 평균을 기준으로 한 해수면 높이 변화"
    },

    "이산화탄소 농도": {
        "column": "CO2_Global_Annual_Mean_ppm",
        "unit": "ppm",
        "description": "전 세계 연평균 이산화탄소 농도"
    },

    "기온 변화 참고 지표": {
        "column": "FAO_Area_Mean_Temp_Change_C",
        "unit": "℃",
        "description": "FAO 지역별 평균 기온 변화값의 단순 평균"
    }
}


# --------------------------------------------------
# 4. 데이터 전처리
# --------------------------------------------------

if "Year" not in df.columns:
    st.error("CSV 파일에 Year 열이 없습니다.")
    st.stop()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

for info in COLUMN_INFO.values():

    column = info["column"]

    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

df = df.dropna(subset=["Year"]).copy()
df["Year"] = df["Year"].astype(int)

df = df.sort_values("Year").reset_index(drop=True)


# --------------------------------------------------
# 5. 데이터 현황
# --------------------------------------------------

st.header("📊 환경 데이터 현황")

col1, col2, col3 = st.columns(3)

col1.metric("전체 데이터 행 수", f"{len(df):,}개")
col2.metric("데이터 시작 연도", f"{df['Year'].min()}년")
col3.metric("데이터 마지막 연도", f"{df['Year'].max()}년")

st.markdown("### 분석 가능한 환경 요소")

for name, info in COLUMN_INFO.items():

    column = info["column"]

    if column not in df.columns:
        st.warning(f"{name}: CSV에서 해당 열을 찾지 못했습니다.")
        continue

    valid = df.dropna(subset=[column])

    if len(valid) == 0:
        st.warning(f"{name}: 유효한 데이터가 없습니다.")
        continue

    st.write(
        f"**{name}** | "
        f"{valid['Year'].min()}~{valid['Year'].max()}년 | "
        f"데이터 {len(valid)}개 | "
        f"단위: {info['unit']}"
    )

st.divider()


# --------------------------------------------------
# 6. 사이드바 설정
# --------------------------------------------------

st.sidebar.title("⚙️ 분석 설정")

selected_factors = st.sidebar.multiselect(
    "분석할 환경 요소 선택",
    list(COLUMN_INFO.keys()),
    default=list(COLUMN_INFO.keys())
)

forecast_end = st.sidebar.slider(
    "미래 예측 종료 연도",
    min_value=2030,
    max_value=2200,
    value=2100,
    step=10
)

model_name = st.sidebar.selectbox(
    "예측에 사용할 인공지능 모델",
    [
        "선형 회귀",
        "랜덤 포레스트",
        "그래디언트 부스팅"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "EARTH FUTURE AI | Environmental Data Analysis"
)


# --------------------------------------------------
# 7. 머신러닝 모델 생성
# --------------------------------------------------

def make_models():

    models = {
        "선형 회귀": LinearRegression(),

        "랜덤 포레스트": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            max_depth=5
        ),

        "그래디언트 부스팅": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=2,
            random_state=42
        )
    }

    return models


# --------------------------------------------------
# 8. 모델 성능 평가
# --------------------------------------------------

def evaluate_models(data):

    results = []

    X = data[["Year"]].values
    y = data["Value"].values

    if len(data) < 10:
        return pd.DataFrame()

    split_index = int(len(data) * 0.8)

    X_train = X[:split_index]
    X_test = X[split_index:]

    y_train = y[:split_index]
    y_test = y[split_index:]

    if len(X_test) < 2:
        return pd.DataFrame()

    models = make_models()

    for name, model in models.items():

        try:
            model.fit(X_train, y_train)

            predictions = model.predict(X_test)

            mae = mean_absolute_error(
                y_test,
                predictions
            )

            rmse = np.sqrt(
                mean_squared_error(
                    y_test,
                    predictions
                )
            )

            r2 = r2_score(
                y_test,
                predictions
            )

            results.append({
                "모델": name,
                "MAE": mae,
                "RMSE": rmse,
                "R²": r2
            })

        except Exception:
            continue

    return pd.DataFrame(results)


# --------------------------------------------------
# 9. 미래 예측
# --------------------------------------------------

def fit_and_forecast(data, selected_model, end_year):

    X = data[["Year"]].values
    y = data["Value"].values

    models = make_models()
    model = models[selected_model]

    model.fit(X, y)

    last_year = int(data["Year"].max())

    future_years = np.arange(
        last_year + 1,
        end_year + 1
    )

    if len(future_years) == 0:
        return model, pd.DataFrame()

    future_X = future_years.reshape(-1, 1)

    predictions = model.predict(future_X)

    forecast_df = pd.DataFrame({
        "Year": future_years,
        "Predicted_Value": predictions
    })

    return model, forecast_df


# --------------------------------------------------
# 10. 환경 요소 분석
# --------------------------------------------------

if not selected_factors:

    st.info("사이드바에서 분석할 환경 요소를 선택해 주세요.")

else:

    for factor in selected_factors:

        st.header(f"🌱 {factor} 분석")

        info = COLUMN_INFO[factor]
        column = info["column"]
        unit = info["unit"]

        if column not in df.columns:

            st.warning(
                f"CSV에 {column} 열이 존재하지 않습니다."
            )

            continue

        # 해당 환경 요소의 데이터만 추출

        data = df[["Year", column]].dropna().copy()

        data = data.rename(
            columns={column: "Value"}
        )

        data = data.sort_values("Year")

        if len(data) < 5:

            st.warning(
                f"{factor}의 데이터가 부족하여 분석할 수 없습니다."
            )

            continue

        # 데이터 현황

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "데이터 개수",
            f"{len(data)}개"
        )

        col2.metric(
            "시작 연도",
            f"{int(data['Year'].min())}년"
        )

        col3.metric(
            "마지막 연도",
            f"{int(data['Year'].max())}년"
        )

        st.caption(info["description"])

        # ------------------------------------------
        # 10-1. 과거 환경 변화 그래프
        # ------------------------------------------

        st.subheader("과거 환경 변화")

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            data["Year"],
            data["Value"],
            marker="o",
            markersize=3,
            linewidth=2,
            label="Historical Data"
        )

        ax.set_title(
            f"{factor} - Historical Trend",
            fontsize=15
        )

        ax.set_xlabel("Year")
        ax.set_ylabel(unit)

        ax.grid(alpha=0.3)
        ax.legend()

        st.pyplot(fig)
        plt.close(fig)

        # ------------------------------------------
        # 10-2. 모델 성능 비교
        # ------------------------------------------

        st.subheader("인공지능 모델 성능 비교")

        evaluation = evaluate_models(data)

        if not evaluation.empty:

            st.dataframe(
                evaluation.style.format({
                    "MAE": "{:.4f}",
                    "RMSE": "{:.4f}",
                    "R²": "{:.4f}"
                }),
                use_container_width=True
            )

            st.caption(
                "과거 데이터의 앞 80%로 학습하고 "
                "뒤 20%로 성능을 평가했습니다."
            )

        else:

            st.warning(
                "모델 성능을 비교하기 위한 데이터가 부족합니다."
            )

        # ------------------------------------------
        # 10-3. 미래 예측
        # ------------------------------------------

        st.subheader("🔮 미래 환경 변화 예측")

        selected_model = model_name

        try:

            model, forecast_df = fit_and_forecast(
                data,
                selected_model,
                forecast_end
            )

            if forecast_df.empty:

                st.warning(
                    "마지막 관측 연도가 예측 종료 연도보다 늦습니다."
                )

                continue

            # 과거 + 미래 그래프

            fig, ax = plt.subplots(figsize=(12, 5))

            ax.plot(
                data["Year"],
                data["Value"],
                linewidth=2,
                label="Historical Data"
            )

            ax.plot(
                forecast_df["Year"],
                forecast_df["Predicted_Value"],
                linestyle="--",
                linewidth=2,
                label="AI Forecast"
            )

            ax.axvline(
                x=int(data["Year"].max()),
                linestyle=":",
                alpha=0.7,
                label="Forecast Start"
            )

            ax.set_title(
                f"{factor} Future Forecast",
                fontsize=15
            )

            ax.set_xlabel("Year")
            ax.set_ylabel(unit)

            ax.grid(alpha=0.3)
            ax.legend()

            st.pyplot(fig)
            plt.close(fig)

            # --------------------------------------
            # 10-4. 주요 연도 예측값
            # --------------------------------------

            st.subheader("주요 연도별 예측 결과")

            target_years = [
                2030,
                2050,
                2100,
                2200
            ]

            prediction_rows = []

            for year in target_years:

                if year > forecast_end:
                    continue

                prediction = model.predict(
                    np.array([[year]])
                )[0]

                prediction_rows.append({
                    "연도": year,
                    "예측값": prediction,
                    "단위": unit
                })

            if prediction_rows:

                prediction_table = pd.DataFrame(
                    prediction_rows
                )

                st.dataframe(
                    prediction_table.style.format({
                        "예측값": "{:.4f}"
                    }),
                    use_container_width=True
                )

            # --------------------------------------
            # 10-5. CSV 다운로드
            # --------------------------------------

            csv_data = forecast_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                label=f"{factor} 예측 데이터 다운로드",
                data=csv_data,
                file_name=f"{factor}_forecast.csv",
                mime="text/csv",
                key=f"download_{column}"
            )

        except Exception as e:

            st.error(
                f"{factor} 예측 과정에서 오류가 발생했습니다."
            )

            st.code(str(e))

        st.divider()


# --------------------------------------------------
# 11. 데이터 분석 안내
# --------------------------------------------------

st.header("📌 데이터 분석 시 주의사항")

st.warning("""
이 프로젝트는 실제 지구의 미래를 확정적으로 예측하는 프로그램이 아닙니다.

과거 데이터를 바탕으로 인공지능 모델이 환경 변화 추세를 학습하고
그 추세가 이어진다는 가정 아래 미래 값을 계산합니다.
""")

st.markdown("""
**분석 데이터 안내**

- 해수면 상승: 1993~2008년 평균을 기준으로 한 해수면 변화 데이터입니다.
- 이산화탄소 농도: 전 세계 연평균 이산화탄소 농도(ppm)입니다.
- 기온 변화 참고 지표: FAO 지역별 평균 기온 변화값의 단순 평균입니다. 공식적인 전 지구 평균 기온 자료가 아닙니다.

**인공지능 모델의 한계**

- 선형 회귀는 과거의 직선적인 추세가 미래에도 이어진다고 가정합니다.
- 랜덤 포레스트와 그래디언트 부스팅은 관측 범위를 크게 벗어난 미래를 예측할 때 값이 평평해지는 경향이 있습니다.
- 특히 2100년이나 2200년의 예측값은 불확실성이 매우 큽니다.
""")

st.divider()

st.caption(
    "EARTH FUTURE AI | Environmental Data Analysis & Forecasting"
)
