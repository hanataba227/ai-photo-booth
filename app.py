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
    "lego": {"name": "🧱 레고 스타일"},
    "anime": {"name": "🎨 일본 애니메이션 스타일"},
    "pixel": {"name": "🎮 픽셀아트 스타일"},
    "clay": {"name": "🪴 클레이(찰흙) 피규어 스타일"},
    "business": {"name": "👔 프로필 사진 스타일"},
    "figure": {"name": "🧸 책상 위 피규어 스타일"},
}

def main():
    # 세션 상태 초기화
    if 'selected_styles' not in st.session_state:
        st.session_state.selected_styles = []
    
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

        # 2. 스타일 선택 (4개 선택)
        st.markdown("#### 2. 스타일 선택")
        st.info("💡 **인생네컷 스타일**로 제작됩니다! 원하는 스타일을 **4개** 선택해주세요.")
        
        # 체크박스로 스타일 선택
        st.markdown("##### 스타일 목록:")
        
        # 2열로 배치
        col1, col2 = st.columns(2)
        style_keys = list(STYLES.keys())
        
        for idx, style_key in enumerate(style_keys):
            col = col1 if idx % 2 == 0 else col2
            with col:
                is_selected = style_key in st.session_state.selected_styles
                
                if st.checkbox(
                    STYLES[style_key]["name"],
                    value=is_selected,
                    key=f"cb_{style_key}",
                    disabled=len(st.session_state.selected_styles) >= 4 and not is_selected
                ):
                    # 체크된 경우
                    if style_key not in st.session_state.selected_styles:
                        if len(st.session_state.selected_styles) < 4:
                            st.session_state.selected_styles.append(style_key)
                            st.rerun()
                else:
                    # 체크 해제된 경우
                    if style_key in st.session_state.selected_styles:
                        st.session_state.selected_styles.remove(style_key)
                        st.rerun()
        
        # 선택 개수 검증
        num_selected = len(st.session_state.selected_styles)
        
        if num_selected < 4:
            st.warning(f"⚠️ {4 - num_selected}개 더 선택해주세요. (현재: {num_selected}/4)")
        elif num_selected == 4:
            st.success("✅ 4개 스타일 선택 완료!")
        
        # 선택 초기화 버튼
        if st.button("🔄 선택 초기화"):
            st.session_state.selected_styles = []
            st.rerun()

        # 3. 제출 버튼
        st.markdown("---")
        
        # 4개 선택 여부 확인
        can_submit = len(st.session_state.selected_styles) == 4
        
        if st.button("✨ 4컷 이미지 변환 요청하기", type="primary", use_container_width=True, disabled=not can_submit):
            if not can_submit:
                st.error("❌ 4개의 스타일을 선택해주세요!")
            else:
                with st.spinner("이미지를 업로드하고 요청을 등록 중입니다..."):
                    try:
                        # 파일 포인터 리셋
                        uploaded_file.seek(0)
                        file_bytes = uploaded_file.read()
                        
                        # 고유 파일명 생성
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        import uuid
                        file_uuid = str(uuid.uuid4())
                        ext = uploaded_file.name.split('.')[-1]
                        file_path = f"{file_uuid}_{timestamp}.{ext}"
                        
                        # 1. Storage에 업로드
                        uploaded_path = upload_image(file_bytes, "input_images", file_path)
                        
                        # 2. DB에 요청 등록 (4개 스타일 배열로)
                        request_data = create_booth_request(
                            style_types=st.session_state.selected_styles,
                            input_image_path=uploaded_path
                        )
                        
                        if request_data:
                            st.success("✅ 4컷 요청이 성공적으로 등록되었습니다!")
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
                                <p style="font-size: 16px;">곧 멋진 인생네컷 AI 이미지를 받아보실 수 있습니다!</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 선택 상태 초기화
                            st.session_state.selected_styles = []
                            
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
