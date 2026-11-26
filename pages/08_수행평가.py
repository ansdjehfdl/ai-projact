
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ==================================================
# 1. 페이지 기본 설정
# ==================================================

st.set_page_config(
    page_title="EARTH FUTURE AI",
    page_icon="🌍",
    layout="wide"
)


# ==================================================
# 2. 디자인
# ==================================================

st.markdown("""
<style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        color: #8A929E;
        font-size: 16px;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
    }

    div[data-testid="stPlotlyChart"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. 제목
# ==================================================

st.markdown(
    '<div class="main-title">🌍 EARTH FUTURE AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">AI 기반 지구 환경 변화 분석 및 미래 예측 시스템</div>',
    unsafe_allow_html=True
)

st.divider()


# ==================================================
# 4. CSV 파일 불러오기
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "earth_environment.csv"


@st.cache_data
def load_data():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}"
        )

    try:
        data = pd.read_csv(
            CSV_PATH,
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:
        data = pd.read_csv(
            CSV_PATH,
            encoding="cp949"
        )

    return data


try:
    df = load_data()

except Exception as e:

    st.error("환경 데이터 파일을 불러오지 못했습니다.")

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


# ==================================================
# 5. 환경 데이터 열 설정
# ==================================================

COLUMN_INFO = {

    "해수면 상승": {
        "column": "Sea_Level_mm_from_1993_2008_avg",
        "unit": "mm",
        "description": "1993~2008년 평균을 기준으로 한 해수면 변화"
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


# ==================================================
# 6. 데이터 전처리
# ==================================================

if "Year" not in df.columns:

    st.error("CSV 파일에 Year 열이 없습니다.")

    st.stop()


df["Year"] = pd.to_numeric(
    df["Year"],
    errors="coerce"
)

for name, info in COLUMN_INFO.items():

    column = info["column"]

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


df = df.dropna(
    subset=["Year"]
).copy()

df["Year"] = df["Year"].astype(int)

df = df.sort_values(
    "Year"
).reset_index(drop=True)


# ==================================================
# 7. 데이터 확인
# ==================================================

available_factors = []

for name, info in COLUMN_INFO.items():

    column = info["column"]

    if column in df.columns and df[column].notna().sum() >= 5:

        available_factors.append(name)


if not available_factors:

    st.error("분석할 수 있는 환경 데이터가 없습니다.")

    st.stop()


# ==================================================
# 8. 분석 설정 영역
# ==================================================

st.markdown(
    '<div class="section-title">⚙️ 분석 설정</div>',
    unsafe_allow_html=True
)

with st.container(border=True):

    setting_col1, setting_col2, setting_col3 = st.columns(3)

    with setting_col1:

        selected_factors = st.multiselect(
            "분석할 환경 요소",
            available_factors,
            default=available_factors,
            help="분석하고 싶은 환경 요소를 선택하세요."
        )

    with setting_col2:

        forecast_end = st.selectbox(
            "미래 예측 종료 연도",
            [2030, 2050, 2100, 2150, 2200],
            index=2
        )

    with setting_col3:

        model_name = st.selectbox(
            "인공지능 예측 모델",
            [
                "선형 회귀",
                "랜덤 포레스트",
                "그래디언트 부스팅"
            ]
        )

    st.caption(
        "선택한 설정은 아래의 모든 환경 분석과 미래 예측에 적용됩니다."
    )


if not selected_factors:

    st.info("분석할 환경 요소를 하나 이상 선택해 주세요.")

    st.stop()


st.divider()


# ==================================================
# 9. 전체 데이터 현황
# ==================================================

st.markdown(
    '<div class="section-title">📊 환경 데이터 현황</div>',
    unsafe_allow_html=True
)

info_col1, info_col2, info_col3 = st.columns(3)

info_col1.metric(
    "전체 데이터 행 수",
    f"{len(df):,}개"
)

info_col2.metric(
    "데이터 시작 연도",
    f"{df['Year'].min()}년"
)

info_col3.metric(
    "데이터 마지막 연도",
    f"{df['Year'].max()}년"
)


with st.expander("환경 요소별 데이터 상세 정보 확인"):

    detail_rows = []

    for name, info in COLUMN_INFO.items():

        column = info["column"]

        if column not in df.columns:
            continue

        valid = df.dropna(
            subset=[column]
        )

        if valid.empty:
            continue

        detail_rows.append({

            "환경 요소": name,

            "시작 연도": int(valid["Year"].min()),

            "마지막 연도": int(valid["Year"].max()),

            "데이터 개수": len(valid),

            "결측값": int(df[column].isna().sum()),

            "단위": info["unit"]

        })

    st.dataframe(
        pd.DataFrame(detail_rows),
        use_container_width=True,
        hide_index=True
    )


st.divider()


# ==================================================
# 10. 인공지능 모델 생성
# ==================================================

def make_models():

    return {

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


# ==================================================
# 11. 모델 성능 평가
# ==================================================

def evaluate_models(data):

    if len(data) < 10:

        return pd.DataFrame()

    X = data[["Year"]].values

    y = data["Value"].values

    split_index = int(len(data) * 0.8)

    X_train = X[:split_index]

    X_test = X[split_index:]

    y_train = y[:split_index]

    y_test = y[split_index:]

    if len(X_test) < 2:

        return pd.DataFrame()

    results = []

    for name, model in make_models().items():

        try:

            model.fit(
                X_train,
                y_train
            )

            predictions = model.predict(
                X_test
            )

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


# ==================================================
# 12. 미래 예측
# ==================================================

def fit_and_forecast(data, model_name, end_year):

    X = data[["Year"]].values

    y = data["Value"].values

    model = make_models()[model_name]

    model.fit(
        X,
        y
    )

    last_year = int(
        data["Year"].max()
    )

    future_years = np.arange(
        last_year + 1,
        end_year + 1
    )

    if len(future_years) == 0:

        return model, pd.DataFrame()

    future_X = future_years.reshape(
        -1,
        1
    )

    predictions = model.predict(
        future_X
    )

    forecast_df = pd.DataFrame({

        "Year": future_years,

        "Predicted_Value": predictions

    })

    return model, forecast_df


# ==================================================
# 13. Plotly 그래프 설정
# ==================================================

def make_chart(data, forecast_df, factor, unit):

    fig = go.Figure()

    # 과거 데이터

    fig.add_trace(

        go.Scatter(

            x=data["Year"],

            y=data["Value"],

            mode="lines",

            name="과거 관측 데이터",

            line=dict(
                width=3
            ),

            hovertemplate=
            "연도: %{x}년<br>"
            "관측값: %{y:.3f} " + unit +
            "<extra></extra>"

        )

    )

    # 미래 예측 데이터

    if not forecast_df.empty:

        fig.add_trace(

            go.Scatter(

                x=forecast_df["Year"],

                y=forecast_df["Predicted_Value"],

                mode="lines",

                name="AI 미래 예측",

                line=dict(
                    width=3,
                    dash="dash"
                ),

                hovertemplate=
                "연도: %{x}년<br>"
                "예측값: %{y:.3f} " + unit +
                "<extra></extra>"

            )

        )

        last_year = int(
            data["Year"].max()
        )

        fig.add_vline(

            x=last_year,

            line_dash="dot",

            annotation_text="예측 시작"

        )

    fig.update_layout(

        title=dict(
            text=f"{factor} 변화 및 미래 예측",
            x=0.02
        ),

        xaxis_title="연도",

        yaxis_title=f"측정값 ({unit})",

        template="plotly_white",

        hovermode="x unified",

        height=480,

        autosize=True,

        margin=dict(
            l=20,
            r=20,
            t=70,
            b=40
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )

    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(128,128,128,0.15)"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(128,128,128,0.15)"
    )

    return fig


# ==================================================
# 14. 환경 요소별 분석
# ==================================================

for factor in selected_factors:

    info = COLUMN_INFO[factor]

    column = info["column"]

    unit = info["unit"]

    st.markdown(
        f'<div class="section-title">🌱 {factor}</div>',
        unsafe_allow_html=True
    )

    data = df[
        ["Year", column]
    ].dropna().copy()

    data = data.rename(
        columns={
            column: "Value"
        }
    )

    data = data.sort_values(
        "Year"
    ).reset_index(drop=True)

    if len(data) < 5:

        st.warning(
            f"{factor}의 데이터가 부족합니다."
        )

        continue


    # ----------------------------------------------
    # 데이터 지표
    # ----------------------------------------------

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "데이터 개수",
        f"{len(data)}개"
    )

    metric2.metric(
        "시작 연도",
        f"{int(data['Year'].min())}년"
    )

    metric3.metric(
        "마지막 관측 연도",
        f"{int(data['Year'].max())}년"
    )

    st.caption(
        info["description"]
    )


    # ----------------------------------------------
    # 과거 데이터 그래프
    # ----------------------------------------------

    st.markdown("#### 📈 과거 환경 변화")

    historical_fig = go.Figure()

    historical_fig.add_trace(

        go.Scatter(

            x=data["Year"],

            y=data["Value"],

            mode="lines",

            name="과거 관측값",

            line=dict(
                width=3
            ),

            hovertemplate=
            "연도: %{x}년<br>"
            "측정값: %{y:.3f} " + unit +
            "<extra></extra>"

        )

    )

    historical_fig.update_layout(

        title=f"{factor} 과거 변화 추이",

        xaxis_title="연도",

        yaxis_title=f"측정값 ({unit})",

        template="plotly_white",

        hovermode="x unified",

        height=400,

        autosize=True,

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=40
        )

    )

    historical_fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(128,128,128,0.15)"
    )

    historical_fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(128,128,128,0.15)"
    )

    st.plotly_chart(
        historical_fig,
        use_container_width=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )


    # ----------------------------------------------
    # 모델 성능 평가
    # ----------------------------------------------

    st.markdown("#### 🤖 인공지능 모델 성능 비교")

    evaluation = evaluate_models(data)

    if not evaluation.empty:

        st.dataframe(

            evaluation.style.format({

                "MAE": "{:.4f}",

                "RMSE": "{:.4f}",

                "R²": "{:.4f}"

            }),

            use_container_width=True,

            hide_index=True

        )

        st.caption(
            "전체 시계열 데이터의 앞 80%를 학습에 사용하고 "
            "뒤 20%를 평가에 사용했습니다."
        )

    else:

        st.warning(
            "모델 성능 평가에 필요한 데이터가 부족합니다."
        )


    # ----------------------------------------------
    # 미래 예측
    # ----------------------------------------------

    st.markdown("#### 🔮 미래 환경 변화 예측")

    try:

        model, forecast_df = fit_and_forecast(

            data,

            model_name,

            forecast_end

        )

        if forecast_df.empty:

            st.warning(
                "선택한 예측 종료 연도가 마지막 관측 연도보다 빠릅니다."
            )

            continue


        forecast_fig = make_chart(

            data,

            forecast_df,

            factor,

            unit

        )

        st.plotly_chart(

            forecast_fig,

            use_container_width=True,

            config={

                "responsive": True,

                "displaylogo": False,

                "scrollZoom": True

            }

        )


        # ------------------------------------------
        # 주요 연도 예측 결과
        # ------------------------------------------

        st.markdown("#### 📋 주요 연도별 예측 결과")

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

                "연도": f"{year}년",

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

                use_container_width=True,

                hide_index=True

            )


        # ------------------------------------------
        # 예측 CSV 다운로드
        # ------------------------------------------

        csv_data = forecast_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(

            label=f"📥 {factor} 예측 데이터 다운로드",

            data=csv_data,

            file_name=f"{factor}_forecast.csv",

            mime="text/csv",

            key=f"download_{column}"

        )


    except Exception as e:

        st.error(
            f"{factor} 예측 중 오류가 발생했습니다."
        )

        st.code(str(e))


    st.divider()


# ==================================================
# 15. 분석 주의사항
# ==================================================

st.markdown(
    '<div class="section-title">📌 분석 시 주의사항</div>',
    unsafe_allow_html=True
)

with st.container(border=True):

    st.markdown("""
    **이 프로젝트는 실제 지구의 미래를 확정적으로 예측하는 프로그램이 아닙니다.**

    과거 환경 데이터를 기반으로 인공지능이 변화 추세를 학습하고,
    그 추세를 바탕으로 미래 값을 계산합니다.

    **데이터 설명**

    - 해수면: 1993~2008년 평균을 기준으로 한 해수면 높이 변화
    - 이산화탄소: 전 세계 연평균 이산화탄소 농도
    - 기온 변화 참고 지표: FAO 지역별 평균 기온 변화값의 단순 평균이며 공식적인 전 지구 평균 기온은 아닙니다.

    **인공지능 모델의 한계**

    - 선형 회귀는 과거의 직선적인 추세를 바탕으로 예측합니다.
    - 랜덤 포레스트와 그래디언트 부스팅은 관측 범위 밖의 미래를 예측할 때 변화가 제한될 수 있습니다.
    - 특히 2100년과 2200년의 예측 결과는 불확실성이 매우 큽니다.
    """)


st.divider()

st.caption(
    "EARTH FUTURE AI | Environmental Data Analysis & Future Forecasting"
)
