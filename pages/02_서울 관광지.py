
import streamlit as st
import folium
from streamlit_folium import st_folium

# -----------------------------
# 1. 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="서울 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ 서울 외국인 인기 관광지 TOP 10")
st.write(
    "Folium 지도를 이용해 서울의 주요 관광지를 확인하고 "
    "각 장소의 위치와 정보를 살펴보세요."
)

# -----------------------------
# 2. 관광지 데이터
# -----------------------------
places = [
    {
        "rank": 1,
        "name": "명동",
        "english": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9850,
        "category": "쇼핑",
        "description": "쇼핑, 화장품 매장, 길거리 음식으로 유명한 거리."
    },
    {
        "rank": 2,
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "category": "랜드마크",
        "description": "남산에서 서울의 전경을 감상할 수 있는 전망 명소."
    },
    {
        "rank": 3,
        "name": "코엑스·별마당도서관",
        "english": "COEX & Starfield Library",
        "lat": 37.5125,
        "lon": 127.0590,
        "category": "쇼핑",
        "description": "대형 쇼핑몰과 사진 명소인 별마당도서관."
    },
    {
        "rank": 4,
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "category": "역사·문화",
        "description": "조선 왕조를 대표하는 궁궐."
    },
    {
        "rank": 5,
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "category": "역사·문화",
        "description": "전통 한옥과 한국의 골목 풍경을 볼 수 있는 곳."
    },
    {
        "rank": 6,
        "name": "광장시장",
        "english": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9995,
        "category": "음식·시장",
        "description": "한국 전통시장과 다양한 길거리 음식을 즐길 수 있는 곳."
    },
    {
        "rank": 7,
        "name": "홍대거리",
        "english": "Hongdae Street",
        "lat": 37.5563,
        "lon": 126.9236,
        "category": "문화·쇼핑",
        "description": "거리 공연, 패션, 카페로 유명한 활기찬 거리."
    },
    {
        "rank": 8,
        "name": "동대문디자인플라자",
        "english": "Dongdaemun Design Plaza",
        "lat": 37.5669,
        "lon": 127.0095,
        "category": "랜드마크",
        "description": "독특한 건축물과 전시, 행사를 즐길 수 있는 공간."
    },
    {
        "rank": 9,
        "name": "남산골한옥마을",
        "english": "Namsangol Hanok Village",
        "lat": 37.5592,
        "lon": 126.9943,
        "category": "역사·문화",
        "description": "한국의 전통 가옥과 문화를 살펴볼 수 있는 마을."
    },
    {
        "rank": 10,
        "name": "서울숲",
        "english": "Seoul Forest",
        "lat": 37.5444,
        "lon": 127.0374,
        "category": "공원·자연",
        "description": "산책과 휴식을 즐길 수 있는 도심 속 공원."
    }
]

# -----------------------------
# 3. 검색 및 카테고리 필터
# -----------------------------
st.sidebar.header("🔎 관광지 검색")

keyword = st.sidebar.text_input(
    "관광지 이름 검색",
    placeholder="예: 명동, 경복궁"
)

categories = ["전체"] + sorted(
    set(place["category"] for place in places)
)

selected_category = st.sidebar.selectbox(
    "관광지 유형",
    categories
)

filtered_places = []

for place in places:
    if (
        selected_category != "전체"
        and place["category"] != selected_category
    ):
        continue

    if (
        keyword
        and keyword.lower() not in place["name"].lower()
        and keyword.lower() not in place["english"].lower()
    ):
        continue

    filtered_places.append(place)

st.caption(
    f"현재 표시 중인 관광지: {len(filtered_places)}곳"
)

# -----------------------------
# 4. Folium 지도 생성
# -----------------------------
st.subheader("📍 서울 관광지 지도")

seoul_map = folium.Map(
    location=[37.5665, 126.9850],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)

# 관광지 마커 추가
for place in filtered_places:
    google_maps_url = (
        "https://www.google.com/maps/search/?api=1"
        f"&query={place['lat']},{place['lon']}"
    )

    popup_html = f"""
    <div style="width:230px; font-family:Arial;">
        <h3>#{place['rank']} {place['name']}</h3>
        <p><b>영어 이름:</b> {place['english']}</p>
        <p><b>유형:</b> {place['category']}</p>
        <p>{place['description']}</p>
        <a href="{google_maps_url}" target="_blank">
            Google 지도에서 길 찾기
        </a>
    </div>
    """

    folium.Marker(
        location=[place["lat"], place["lon"]],
        tooltip=f"#{place['rank']} {place['name']}",
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background-color:#1769ff;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:30px;
                height:30px;
                line-height:26px;
                text-align:center;
                font-weight:bold;
                box-shadow:0 1px 4px #777;
            ">{place['rank']}</div>
            """
        )
    ).add_to(seoul_map)

# 지도 화면에 출력
st_folium(
    seoul_map,
    width=None,
    height=600,
    use_container_width=True,
    returned_objects=[]
)

# -----------------------------
# 5. 관광지 목록 표시
# -----------------------------
st.subheader("🏙️ 관광지 목록")

if not filtered_places:
    st.warning("검색 결과가 없습니다.")

for place in filtered_places:
    with st.expander(
        f"#{place['rank']} {place['name']} "
        f"({place['english']})"
    ):
        st.write(place["description"])
        st.write("관광지 유형:", place["category"])
        st.write(
            f"위도: {place['lat']}, "
            f"경도: {place['lon']}"
        )

        st.link_button(
            "Google 지도에서 열기",
            "https://www.google.com/maps/search/"
            f"?api=1&query={place['lat']},{place['lon']}"
        )

# -----------------------------
# 6. 하단 안내
# -----------------------------
st.divider()

st.caption(
    "이 목록은 서울의 대표 관광지를 선정한 추천 목록이며, "
    "공식적인 외국인 방문객 종합 순위는 아닙니다."
)

st.caption(
    "지도 제공: OpenStreetMap | 지도 표시: Folium"
)
