import streamlit as st
from PIL import Image
from utils.supabase_client import upload_image, create_booth_request
from utils.image_processor import validate_image
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="COM-ART AI Photo Booth",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 스타일 정의
STYLES = {
    "lego": {"name": "🧱 레고 (Lego)", "desc": "레고 블럭으로 만든 세상"},
    "anime": {"name": "🎨 애니메이션 (Anime)", "desc": "일본 애니메이션 스타일"},
    "pixel": {"name": "🎮 픽셀아트 (Pixel)", "desc": "레트로 게임 스타일"},
    "clay": {"name": "🪴 클레이 (Clay)", "desc": "귀여운 클레이 피규어"},
    "business": {"name": "👔 비즈니스 (Business)", "desc": "세련된 스튜디오 프로필 사진"},
    "figure": {"name": "🧸 피규어 (Figure)", "desc": "책상 위 수집용 피규어"},
}

def main():
    # 헤더 섹션
    st.title("🎨 AI 인생네컷")
    st.markdown("### 나만의 특별한 AI 사진을 만들어보세요!")

    # 1. 이미지 업로드
    st.markdown("#### 1. 사진 업로드")
    uploaded_file = st.file_uploader("얼굴이 잘 나온 사진을 선택해주세요 (JPG, PNG)", type=['jpg', 'jpeg', 'png'])

    if uploaded_file is not None:
        # 이미지 유효성 검사
        if not validate_image(uploaded_file):
            st.error("❌ 올바르지 않은 이미지 파일입니다. JPG 또는 PNG 파일을 업로드해주세요.")
            return

        # 이미지 미리보기
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 사진", use_column_width=True)

        # 2. 스타일 선택
        st.markdown("#### 2. 스타일 선택")
        
        # 라디오 버튼을 위한 옵션 리스트 생성
        style_options = list(STYLES.keys())
        
        # 커스텀 포맷팅 함수
        def format_func(option):
            return STYLES[option]["name"]

        selected_style = st.radio(
            "원하는 스타일을 선택하세요:",
            options=style_options,
            format_func=format_func,
            help="변환하고 싶은 스타일을 선택해주세요."
        )
        
        # 선택한 스타일 설명 표시
        st.caption(f"💡 {STYLES[selected_style]['desc']}")

        # 3. 제출 버튼
        st.markdown("---")
        if st.button("✨ 이미지 변환 요청하기", type="primary", use_container_width=True):
            with st.spinner("이미지를 업로드하고 요청을 등록 중입니다..."):
                try:
                    # 파일 포인터 리셋
                    uploaded_file.seek(0)
                    file_bytes = uploaded_file.read()
                    
                    # 고유 파일명 생성 (UUID는 DB에서 생성하지만, 파일명은 여기서 지정)
                    # 간단하게 타임스탬프와 랜덤 문자열 조합 또는 그냥 타임스탬프
                    # 실제로는 supabase_client에서 처리하거나 여기서 생성
                    # 명세서 규칙: {uuid}_{timestamp}.{ext} -> UUID를 모르므로 timestamp_random 사용
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    import uuid
                    file_uuid = str(uuid.uuid4())
                    ext = uploaded_file.name.split('.')[-1]
                    file_path = f"{file_uuid}_{timestamp}.{ext}"
                    
                    # 1. Storage에 업로드
                    uploaded_path = upload_image(file_bytes, "input_images", file_path)
                    
                    # 2. DB에 요청 등록
                    # upload_image는 경로를 반환함.
                    request_data = create_booth_request(selected_style, uploaded_path)
                    
                    if request_data:
                        st.success("✅ 요청이 성공적으로 등록되었습니다!")
                        st.balloons()
                        
                        # 대기 번호 포맷팅
                        queue_num = request_data.get('queue_number', 0)
                        
                        # 결과 안내
                        st.markdown(f"""
                        <div style="padding: 30px; background-color: #f0f2f6; border-radius: 10px; margin-top: 20px; text-align: center;">
                            <h3>🎫 대기 번호</h3>
                            <div style="font-size: 72px; font-weight: bold; color: #FF4B4B; margin: 20px 0;">
                                {queue_num:03d}
                            </div>
                            <p style="font-size: 18px; margin-top: 20px;">부스 앞에서 잠시만 기다려주세요.</p>
                            <p style="font-size: 16px;">곧 멋진 AI 이미지를 받아보실 수 있습니다!</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("❌ 요청 등록에 실패했습니다. 다시 시도해주세요.")
                        
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                    # 개발 모드에서만 에러 상세 표시
                    # st.exception(e)

    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        Mokwon Univ. Computer Engineering
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
