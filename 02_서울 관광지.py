
import streamlit as st
import folium
from folium.plugins import PolyLineTextPath
from streamlit_folium import st_folium
import pandas as pd
from urllib.parse import quote_plus

# ==================================================
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="Seoul 2-Day Travel Planner",
    page_icon="🗺️",
    layout="wide"
)

st.title("🇰🇷 서울 1박 2일 여행 플래너")
st.write(
    "서울의 대표 관광지 10곳과 맛집, 호텔을 한눈에 확인하고 "
    "지도와 시간표를 이용해 여행을 계획해 보세요."
)

st.info(
    "여행 시간은 추천 일정입니다. 실제 이동 시간, "
    "대기 시간, 영업시간에 따라 조정해 주세요."
)


# ==================================================
# 2. 공통 링크 생성 함수
# ==================================================
def google_maps_search(place):
    query = quote_plus(place + " 서울")
    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={query}"
    )


def google_maps_directions(origin, destination, waypoints=None):
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote_plus(origin)}"
        f"&destination={quote_plus(destination)}"
        "&travelmode=transit"
    )

    if waypoints:
        url += "&waypoints=" + quote_plus("|".join(waypoints))

    return url


# ==================================================
# 3. 관광지 데이터
# ==================================================
places = [
    {
        "id": 1,
        "name": "경복궁",
        "en": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "day": 1,
        "time": "09:00–10:15",
        "category": "역사·문화",
        "description": "조선 왕조를 대표하는 궁궐과 한국 전통 건축",
        "transport": "도보 및 지하철"
    },
    {
        "id": 2,
        "name": "북촌한옥마을",
        "en": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "day": 1,
        "time": "10:30–11:30",
        "category": "역사·문화",
        "description": "전통 한옥과 골목 풍경",
        "transport": "도보"
    },
    {
        "id": 3,
        "name": "광장시장",
        "en": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9995,
        "day": 1,
        "time": "13:00–14:00",
        "category": "음식·시장",
        "description": "빈대떡, 김밥 등 한국 전통시장 먹거리",
        "transport": "대중교통"
    },
    {
        "id": 4,
        "name": "동대문디자인플라자",
        "en": "Dongdaemun Design Plaza",
        "lat": 37.5669,
        "lon": 127.0095,
        "day": 1,
        "time": "14:15–15:15",
        "category": "건축·문화",
        "description": "독특한 건축물과 전시 공간",
        "transport": "도보 및 지하철"
    },
    {
        "id": 5,
        "name": "명동",
        "en": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9850,
        "day": 1,
        "time": "15:45–17:00",
        "category": "쇼핑·먹거리",
        "description": "쇼핑, 화장품, 길거리 음식",
        "transport": "지하철"
    },
    {
        "id": 6,
        "name": "남산골한옥마을",
        "en": "Namsangol Hanok Village",
        "lat": 37.5592,
        "lon": 126.9943,
        "day": 2,
        "time": "09:00–09:45",
        "category": "역사·문화",
        "description": "전통 한옥과 한국의 생활문화",
        "transport": "도보 및 버스"
    },
    {
        "id": 7,
        "name": "N서울타워",
        "en": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "day": 2,
        "time": "10:15–11:45",
        "category": "전망·랜드마크",
        "description": "남산에서 즐기는 서울 전망",
        "transport": "버스 또는 케이블카"
    },
    {
        "id": 8,
        "name": "코엑스·별마당도서관",
        "en": "COEX Starfield Library",
        "lat": 37.5125,
        "lon": 127.0590,
        "day": 2,
        "time": "13:30–15:00",
        "category": "쇼핑·문화",
        "description": "대형 복합 쇼핑몰과 유명한 실내 도서관",
        "transport": "지하철"
    },
    {
        "id": 9,
        "name": "서울숲",
        "en": "Seoul Forest",
        "lat": 37.5444,
        "lon": 127.0374,
        "day": 2,
        "time": "15:30–16:15",
        "category": "공원·자연",
        "description": "도심 속 산책과 휴식",
        "transport": "지하철"
    },
    {
        "id": 10,
        "name": "홍대거리",
        "en": "Hongdae Street",
        "lat": 37.5563,
        "lon": 126.9236,
        "day": 2,
        "time": "17:15–19:00",
        "category": "문화·쇼핑",
        "description": "거리 공연, 패션, 카페와 다양한 상점",
        "transport": "지하철"
    }
]


# ==================================================
# 4. 날짜별 상세 일정
# ==================================================
day1_schedule = [
    {
        "시간": "09:00–10:15",
        "일정": "경복궁",
        "내용": "궁궐 관람 및 사진 촬영",
        "이동": "여행 시작"
    },
    {
        "시간": "10:15–10:30",
        "일정": "이동",
        "내용": "북촌 방향으로 이동",
        "이동": "도보 약 15분"
    },
    {
        "시간": "10:30–11:30",
        "일정": "북촌한옥마을",
        "내용": "한옥과 골목 산책",
        "이동": "도보"
    },
    {
        "시간": "11:30–12:30",
        "일정": "점심",
        "내용": "토속촌 삼계탕 추천",
        "이동": "서촌 방향으로 이동"
    },
    {
        "시간": "12:30–13:00",
        "일정": "광장시장 이동",
        "내용": "지하철 또는 버스",
        "이동": "교통 상황에 따라 조정"
    },
    {
        "시간": "13:00–14:00",
        "일정": "광장시장",
        "내용": "전통시장 구경과 간식",
        "이동": "도보"
    },
    {
        "시간": "14:15–15:15",
        "일정": "동대문디자인플라자",
        "내용": "건축물과 전시 공간 구경",
        "이동": "도보 약 15분"
    },
    {
        "시간": "15:15–15:45",
        "일정": "명동 이동",
        "내용": "지하철 또는 택시",
        "이동": "교통 상황에 따라 조정"
    },
    {
        "시간": "15:45–17:00",
        "일정": "명동",
        "내용": "쇼핑과 길거리 음식",
        "이동": "도보"
    },
    {
        "시간": "17:00–19:00",
        "일정": "저녁 및 자유시간",
        "내용": "명동에서 식사 후 호텔 체크인",
        "이동": "숙소 위치에 따라 조정"
    }
]

day2_schedule = [
    {
        "시간": "09:00–09:45",
        "일정": "남산골한옥마을",
        "내용": "전통 한옥 관람",
        "이동": "호텔에서 출발"
    },
    {
        "시간": "09:45–10:15",
        "일정": "N서울타워 이동",
        "내용": "남산 방향으로 이동",
        "이동": "버스 또는 케이블카"
    },
    {
        "시간": "10:15–11:45",
        "일정": "N서울타워",
        "내용": "서울 전망과 사진 촬영",
        "이동": "도보"
    },
    {
        "시간": "11:45–12:30",
        "일정": "점심 장소로 이동",
        "내용": "명동 또는 강남 방향 이동",
        "이동": "대중교통"
    },
    {
        "시간": "12:30–13:30",
        "일정": "점심",
        "내용": "이동 경로에 맞춰 식사",
        "이동": "식당 링크 참고"
    },
    {
        "시간": "13:30–15:00",
        "일정": "코엑스·별마당도서관",
        "내용": "도서관과 쇼핑몰 구경",
        "이동": "지하철"
    },
    {
        "시간": "15:00–15:30",
        "일정": "서울숲 이동",
        "내용": "성수 방향으로 이동",
        "이동": "지하철"
    },
    {
        "시간": "15:30–16:15",
        "일정": "서울숲",
        "내용": "공원 산책",
        "이동": "도보"
    },
    {
        "시간": "16:15–17:15",
        "일정": "홍대 이동",
        "내용": "지하철로 홍대입구역 이동",
        "이동": "교통 상황에 따라 조정"
    },
    {
        "시간": "17:15–19:00",
        "일정": "홍대거리·저녁",
        "내용": "거리 구경 후 저녁 식사",
        "이동": "여행 종료"
    }
]


# ==================================================
# 5. Folium 지도
# ==================================================
st.header("📍 관광지 10곳과 이동 경로")

selected_day = st.radio(
    "지도에 표시할 일정",
    ["전체 일정", "1일 차", "2일 차"],
    horizontal=True
)

if selected_day == "1일 차":
    map_places = [p for p in places if p["day"] == 1]
elif selected_day == "2일 차":
    map_places = [p for p in places if p["day"] == 2]
else:
    map_places = places

seoul_map = folium.Map(
    location=[37.5665, 126.9850],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)

day_colors = {
    1: "blue",
    2: "green"
}

for place in map_places:
    color = day_colors[place["day"]]

    popup_html = f"""
    <div style="width:230px">
        <h4>#{place['id']} {place['name']}</h4>
        <p>{place['en']}</p>
        <p>{place['description']}</p>
        <p><b>추천 시간:</b> {place['time']}</p>
        <a href="{google_maps_search(place['name'])}"
           target="_blank">Google 지도에서 보기</a>
    </div>
    """

    folium.Marker(
        location=[place["lat"], place["lon"]],
        tooltip=f"#{place['id']} {place['name']}",
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(
            color=color,
            icon="info-sign"
        )
    ).add_to(seoul_map)

# 날짜별 순서대로 선을 그린다.
for day in [1, 2]:
    if selected_day != "전체 일정" and (
        selected_day == "1일 차" and day != 1
        or selected_day == "2일 차" and day != 2
    ):
        continue

    route = [
        [p["lat"], p["lon"]]
        for p in places
        if p["day"] == day
    ]

    if len(route) > 1:
        folium.PolyLine(
            route,
            color=day_colors[day],
            weight=4,
            opacity=0.75,
            tooltip=f"{day}일 차 추천 이동 순서"
        ).add_to(seoul_map)

st_folium(
    seoul_map,
    height=570,
    use_container_width=True,
    returned_objects=[]
)

st.caption(
    "지도 경로 선은 방문 순서를 시각화한 직선이며 실제 도로·"
    "대중교통 경로가 아닙니다. 실제 길 찾기는 각 장소의 링크를 이용하세요."
)


# ==================================================
# 6. 지도 아래 일정표
# ==================================================
st.header("🗓️ 1박 2일 상세 일정표")

tab1, tab2 = st.tabs(["📅 1일 차", "📅 2일 차"])

with tab1:
    st.subheader("1일 차 | 고궁 · 전통시장 · 도심")
    st.dataframe(
        pd.DataFrame(day1_schedule),
        hide_index=True,
        use_container_width=True
    )

    st.link_button(
        "1일 차 Google 지도 길 찾기",
        google_maps_directions(
            "경복궁 서울",
            "명동 서울",
            [
                "북촌한옥마을 서울",
                "광장시장 서울",
                "동대문디자인플라자 서울"
            ]
        )
    )

with tab2:
    st.subheader("2일 차 | 남산 · 강남 · 자연 · 홍대")
    st.dataframe(
        pd.DataFrame(day2_schedule),
        hide_index=True,
        use_container_width=True
    )

    st.link_button(
        "2일 차 Google 지도 길 찾기",
        google_maps_directions(
            "남산골한옥마을 서울",
            "홍대거리 서울",
            [
                "N서울타워 서울",
                "코엑스 별마당도서관 서울",
                "서울숲 서울"
            ]
        )
    )


# ==================================================
# 7. 식당 추천
# ==================================================
st.header("🍽️ 동선에 맞는 식당 추천")

restaurants = [
    {
        "day": "1일 차 아침",
        "name": "명동 주변 카페·토스트",
        "menu": "토스트, 샌드위치, 커피",
        "reason": "출발 전 간단히 먹고 경복궁으로 이동",
        "link": google_maps_search("명동 토스트 아침 식사")
    },
    {
        "day": "1일 차 점심",
        "name": "토속촌 삼계탕",
        "menu": "삼계탕",
        "reason": "경복궁과 서촌에서 접근하기 좋은 유명 식당",
        "link": google_maps_search("토속촌 삼계탕")
    },
    {
        "day": "1일 차 저녁",
        "name": "명동교자",
        "menu": "칼국수, 만두",
        "reason": "명동 관광 후 식사하기 편리한 식당",
        "link": google_maps_search("명동교자")
    },
    {
        "day": "2일 차 아침",
        "name": "호텔 조식 또는 충무로 주변 카페",
        "menu": "조식 뷔페, 빵, 샌드위치",
        "reason": "남산골한옥마을 방문 전에 간단히 식사",
        "link": google_maps_search("충무로 아침 식사 카페")
    },
    {
        "day": "2일 차 점심",
        "name": "코엑스몰 식당가",
        "menu": "한식, 면 요리, 다양한 식사",
        "reason": "코엑스 관광 중 이동을 줄여 식사 가능",
        "link": google_maps_search("스타필드 코엑스몰 식당")
    },
    {
        "day": "2일 차 저녁",
        "name": "일편등심 홍대본점",
        "menu": "한우 구이",
        "reason": "홍대 관광을 마무리하며 먹는 한국식 고기 요리",
        "link": google_maps_search("일편등심 홍대본점")
    }
]

for meal in restaurants:
    with st.container(border=True):
        st.markdown(f"### {meal['day']} · {meal['name']}")
        st.write(f"**추천 메뉴:** {meal['menu']}")
        st.write(meal["reason"])
        st.link_button(
            "📍 식당 위치·영업 정보 확인",
            meal["link"]
        )

st.warning(
    "식당의 영업시간, 휴무일, 대기 시간은 방문 전에 확인하세요. "
    "아침 식당은 숙소 위치와 당일 영업 여부에 따라 선택하면 좋습니다."
)


# ==================================================
# 8. 호텔 추천
# ==================================================
st.header("🏨 추천 호텔")

st.write(
    "이 일정은 명동이나 을지로 인근에 숙박하면 첫날 관광과 "
    "둘째 날 남산 이동을 편하게 시작할 수 있어."
)

hotels = [
    {
        "name": "롯데호텔 서울",
        "type": "고급 호텔",
        "reason": "시청·을지로·명동 접근성이 좋은 중심부 숙소",
        "link": google_maps_search("롯데호텔 서울")
    },
    {
        "name": "르메르디앙 서울 명동",
        "type": "럭셔리 호텔",
        "reason": "명동 중심부에서 쇼핑과 식사를 즐기기 편리",
        "link": google_maps_search("르메르디앙 서울 명동")
    },
    {
        "name": "호텔 피제이 명동",
        "type": "중급 호텔 후보",
        "reason": "충무로·을지로 쪽 관광 동선을 고려할 때 비교할 만한 숙소",
        "link": google_maps_search("호텔 피제이 명동")
    }
]

for hotel in hotels:
    with st.container(border=True):
        st.subheader(hotel["name"])
        st.caption(hotel["type"])
        st.write(hotel["reason"])
        st.link_button(
            "🏨 호텔 위치·가격·예약 정보 확인",
            hotel["link"]
        )

st.caption(
    "호텔 링크는 지도 검색 페이지입니다. 날짜별 객실 가격과 예약 가능 여부는 "
    "여행 날짜를 입력해 별도로 확인하세요."
)


# ==================================================
# 9. 유용한 공식 관광 정보
# ==================================================
st.header("ℹ️ 여행 준비 링크")

st.markdown(
    "- [서울 공식 관광정보](https://english.visitseoul.net/)\n"
    "- [서울 관광지도](https://map.seoul.go.kr/global/)\n"
    "- [한국관광공사](https://english.visitkorea.or.kr/)\n"
    "- [서울 지하철·길 찾기 Google 지도](https://www.google.com/maps)"
)

st.divider()

st.caption(
    "관광지 10곳은 대표 명소를 바탕으로 구성한 추천 목록입니다. "
    "공식적인 외국인 방문객 인기 순위와는 다를 수 있습니다."
)
