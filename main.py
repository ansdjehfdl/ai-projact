import streamlit as st
st.title('현식이 귀엽다')
a=st.text_input('이름을 입력해주세요!')
b=st.selectbox('좋아하는 음식을 선택해 임마',['곱창','마라탕','초콜'])
if st.button('인사말 생성'):
  st.write('반갑습니다!')
  st.info(a+'동무 반갑다우')
  st.warning(b+'를 좋아하는구만 기래')
  st.error('잘 지내보자우')
  st.ballins()
