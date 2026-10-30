
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Seoul Top 10 Tourist Map",
    page_icon="🗺️",
    layout="wide"
)

# 관광지 데이터
spots = [
    {
        "rank": 1,
        "ko": "명동",
        "en": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9850,
        "category": "Shopping",
        "description": "쇼핑과 길거리 음식으로 유명한 번화가"
    },
    {
        "rank": 2,
        "ko": "N서울타워",
        "en": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "category": "Landmark",
        "description": "남산에서 서울의 전경을 볼 수 있는 랜드마크"
    },
    {
        "rank": 3,
        "ko": "코엑스·별마당도서관",
        "en": "COEX & Starfield Library",
        "lat": 37.5125,
        "lon": 127.0590,
        "category": "Shopping",
        "description": "쇼핑과 사진 촬영을 즐기기 좋은 명소"
    },
    {
        "rank": 4,
        "ko": "경복궁",
        "en": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "category": "Culture",
        "description": "조선 왕조의 대표 궁궐"
    },
    {
        "rank": 5,
        "ko": "북촌한옥마을",
        "en": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "category": "Culture",
        "description": "전통 한옥과 골목 풍경을 만날 수 있는 곳"
    },
    {
        "rank": 6,
        "ko": "광장시장",
        "en": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9995,
        "category": "Food",
        "description": "한국 전통시장과 다양한 길거리 음식"
    },
    {
        "rank": 7,
        "ko": "홍대거리",
        "en": "Hongdae Street",
        "lat": 37.5563,
        "lon": 126.9236,
        "category": "Culture",
        "description": "공연, 패션, 카페가 모여 있는 활기찬 거리"
    },
    {
        "rank": 8,
        "ko": "동대문디자인플라자",
        "en": "Dongdaemun Design Plaza",
        "lat": 37.5669,
        "lon": 127.0095,
        "category": "Landmark",
        "description": "독특한 건축 디자인과 전시 행사로 유명한 곳"
    },
    {
        "rank": 9,
        "ko": "남산골한옥마을",
        "en": "Namsangol Hanok Village",
        "lat": 37.5592,
        "lon": 126.9943,
        "category": "Culture",
        "description": "한국의 전통 가옥과 문화를 체험할 수 있는 곳"
    },
    {
        "rank": 10,
        "ko": "서울숲",
        "en": "Seoul Forest",
        "lat": 37.5444,
        "lon": 127.0374,
        "category": "Nature",
        "description": "산책과 휴식을 즐길 수 있는 도심 속 공원"
    }
]

st.title("🗺️ 서울 외국인 인기 관광지 TOP 10")
st.write(
    "서울을 방문하는 외국인 관광객을 위한 "
    "주요 관광지 지도입니다."
)

# 검색 및 필터
search = st.sidebar.text_input("관광지 검색")

categories = ["전체"] + sorted(
    set(place["category"] for place in spots)
)
category = st.sidebar.selectbox(
    "관광지 유형",
    categories
)

filtered_spots = []

for place in spots:
    if category != "전체" and place["category"] != category:
        continue

    if (
        search
        and search.lower() not in place["ko"].lower()
        and search.lower() not in place["en"].lower()
    ):
        continue

    filtered_spots.append(place)

# 지도 생성
st.subheader("📍 서울 관광지 지도")

map_seoul = folium.Map(
    location=[37.5665, 126.9850],
    zoom_start=12,
    tiles="OpenStreetMap"
)

for place in filtered_spots:
    google_maps_url = (
        "https://www.google.com/maps/search/?api=1"
        f"&query={place['lat']},{place['lon']}"
    )

    popup_html = f"""
    <div style="width:220px">
        <h4>#{place['rank']} {place['ko']}</h4>
        <p>{place['description']}</p>
        <a href="{google_maps_url}" target="_blank">
            Google 지도에서 보기
        </a>
    </div>
    """

    folium.Marker(
        location=[place["lat"], place["lon"]],
        tooltip=f"#{place['rank']} {place['ko']}",
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:#1f6feb;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:30px;
                height:30px;
                text-align:center;
                line-height:26px;
                font-weight:bold;
            ">{place['rank']}</div>
            """
        )
    ).add_to(map_seoul)

st_folium(
    map_seoul,
    height=550,
    use_container_width=True
)

# 관광지 목록
st.subheader("🏙️ 관광지 TOP 10")

for place in filtered_spots:
    with st.expander(
        f"#{place['rank']} {place['ko']} "
        f"({place['en']})"
    ):
        st.write(place["description"])
        st.write("유형:", place["category"])

        st.link_button(
            "Google 지도에서 보기",
            "https://www.google.com/maps/search/"
            f"?api=1&query={place['lat']},{place['lon']}"
        )

st.caption(
    "관광지 목록은 대표 명소를 바탕으로 구성한 추천 목록이며, "
    "공식적인 외국인 방문객 종합 순위는 아닙니다."
)
