
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --------------------------------
# 1. 페이지 설정
# --------------------------------

st.set_page_config(
    page_title="AI 붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 프로그램")

st.markdown("""
꽃잎의 길이와 너비를 입력하면
인공지능이 붓꽃의 품종을 예측합니다.
""")

st.divider()


# --------------------------------
# 2. 데이터 불러오기
# --------------------------------

@st.cache_data
def load_data():

    try:
        df = pd.read_csv("iris.csv", encoding="cp949")

    except UnicodeDecodeError:
        df = pd.read_csv("iris.csv", encoding="utf-8-sig")

    return df


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


# 컬럼명 확인
required_columns = ["꽃잎길이", "꽃잎 너비", "품종"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 컬럼명을 확인해주세요.")
    st.stop()


# 필요한 데이터만 추출
X = df[["꽃잎길이", "꽃잎 너비"]]
y = df["품종"]


# --------------------------------
# 3. 데이터 범위 확인
# --------------------------------

length_min = float(X["꽃잎길이"].min())
length_max = float(X["꽃잎길이"].max())

width_min = float(X["꽃잎 너비"].min())
width_max = float(X["꽃잎 너비"].max())


# --------------------------------
# 4. 모델 학습 및 정확도 평가
# --------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 평가용 모델
evaluation_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

evaluation_model.fit(X_train, y_train)

y_pred = evaluation_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)


# 전체 데이터로 최종 모델 학습
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X, y)


# --------------------------------
# 5. 데이터 입력
# --------------------------------

st.subheader("📌 꽃잎 정보 입력")

st.info(
    f"""
    입력 가능한 범위를 확인해주세요.

    - 꽃잎 길이: {length_min}cm ~ {length_max}cm
    - 꽃잎 너비: {width_min}cm ~ {width_max}cm
    """
)

col1, col2 = st.columns(2)

with col1:

    petal_length = st.number_input(
        "🌸 꽃잎 길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=5.0,
        step=0.1,
        format="%.1f"
    )

with col2:

    petal_width = st.number_input(
        "🌸 꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=1.5,
        step=0.1,
        format="%.1f"
    )


# --------------------------------
# 6. 품종 예측
# --------------------------------

user_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=["꽃잎길이", "꽃잎 너비"]
)

prediction = model.predict(user_data)[0]

probabilities = model.predict_proba(user_data)[0]

class_names = model.classes_


# --------------------------------
# 7. 예측 결과
# --------------------------------

st.divider()

st.subheader("🤖 AI 예측 결과")

result_col1, result_col2 = st.columns(2)

with result_col1:

    st.success(f"예측된 품종: {prediction}")

    st.metric(
        "예측 확률",
        f"{max(probabilities) * 100:.1f}%"
    )

with result_col2:

    st.metric(
        "모델 정확도",
        f"{accuracy * 100:.1f}%"
    )

    st.caption(
        "전체 데이터 중 20%를 테스트 데이터로 분리하여 평가한 결과입니다."
    )


# 품종별 예측 확률
st.markdown("### 품종별 예측 확률")

prob_df = pd.DataFrame({
    "품종": class_names,
    "예측 확률": probabilities
})

st.bar_chart(
    prob_df.set_index("품종")
)


# --------------------------------
# 8. 시각화
# --------------------------------

st.divider()

st.subheader("📊 붓꽃 품종 분류 시각화")

st.markdown("""
- 가로축: 꽃잎 길이
- 세로축: 꽃잎 너비
- 색상별 점: 실제 붓꽃 데이터
- 초록색 별: 사용자가 입력한 데이터
- 배경색: AI가 예측하는 품종별 분류 영역
""")

# 그래프 생성
fig, ax = plt.subplots(figsize=(11, 7))

# 품종별 색상
colors = {
    "Iris-setosa": "#3498db",
    "Iris-versicolor": "#f39c12",
    "Iris-virginica": "#e74c3c"
}

# 그래프 범위
x_min = length_min - 0.3
x_max = length_max + 0.3

y_min = width_min - 0.2
y_max = width_max + 0.2

# 분류 영역 생성
xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)

grid = pd.DataFrame({
    "꽃잎길이": xx.ravel(),
    "꽃잎 너비": yy.ravel()
})

Z = model.predict(grid)

# 품종별 숫자로 변환
class_to_number = {
    name: i for i, name in enumerate(class_names)
}

Z_number = np.array(
    [class_to_number[name] for name in Z]
).reshape(xx.shape)

# AI 분류 영역
ax.contourf(
    xx,
    yy,
    Z_number,
    alpha=0.13,
    levels=np.arange(len(class_names) + 1) - 0.5,
    cmap="Set1"
)

# 실제 데이터 표시
for species in class_names:

    subset = df[df["품종"] == species]

    ax.scatter(
        subset["꽃잎길이"],
        subset["꽃잎 너비"],
        color=colors.get(species, "#888888"),
        label=species,
        s=55,
        alpha=0.8,
        edgecolors="white",
        linewidths=0.5
    )


# 사용자가 입력한 데이터 표시
ax.scatter(
    petal_length,
    petal_width,
    color="lime",
    marker="*",
    s=450,
    edgecolors="black",
    linewidths=1.2,
    label="Your Input",
    zorder=10
)

# 입력 지점 설명
ax.annotate(
    f"Your Input\n({petal_length:.1f}, {petal_width:.1f})",
    xy=(petal_length, petal_width),
    xytext=(15, 15),
    textcoords="offset points",
    fontsize=11,
    fontweight="bold",
    arrowprops=dict(
        arrowstyle="->",
        color="green"
    )
)

ax.set_xlabel("Petal Length (cm)", fontsize=12)
ax.set_ylabel("Petal Width (cm)", fontsize=12)

ax.set_title(
    "Iris Classification - Random Forest",
    fontsize=16,
    fontweight="bold"
)

ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

ax.grid(alpha=0.2)

ax.legend(loc="best")

st.pyplot(fig)

plt.close(fig)


# --------------------------------
# 9. 분류 이유 분석
# --------------------------------

st.divider()

st.subheader("🔍 AI가 이렇게 분류한 이유")

st.write(
    f"입력한 꽃잎 길이는 {petal_length:.1f}cm이고, "
    f"꽃잎 너비는 {petal_width:.1f}cm입니다."
)

st.write(
    f"랜덤 포레스트 알고리즘은 여러 결정 트리의 "
    f"예측 결과를 종합하여 **{prediction}**으로 분류했습니다."
)

# 특성 중요도
importance = model.feature_importances_

importance_df = pd.DataFrame({
    "측정 항목": ["꽃잎 길이", "꽃잎 너비"],
    "중요도": importance
}).sort_values("중요도", ascending=False)

st.markdown("### 품종 분류에 사용된 특성의 중요도")

st.bar_chart(
    importance_df.set_index("측정 항목")
)

st.caption(
    "특성 중요도는 모델 전체에서 각 측정값이 분류에 기여한 정도를 나타냅니다. "
    "개별 예측의 직접적인 원인을 의미하지는 않습니다."
)


# --------------------------------
# 10. 데이터 정보
# --------------------------------

with st.expander("📁 데이터 정보 확인"):

    st.write("전체 데이터 개수:", len(df))

    st.write("품종별 데이터 개수")

    st.write(df["품종"].value_counts())

    st.write("전체 데이터")

    st.dataframe(df, use_container_width=True)


st.divider()

st.caption(
    "AI Iris Classification | Random Forest | Pandas & Scikit-learn"
)
