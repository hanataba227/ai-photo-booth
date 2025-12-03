# 페이지 설정 (반드시 첫 번째로 호출)
import streamlit as st
st.set_page_config(page_title="Admin Dashboard - COM-ART", page_icon="🛠️", layout="wide")

from streamlit_autorefresh import st_autorefresh
from utils.supabase_client import (
    get_pending_requests,
    get_all_active_requests,
    update_request_status,
    download_image,
    upload_image,
    get_image_url,
    delete_request,
    supabase
)
from utils.gemini_client import generate_styled_image, generate_multiple_styles_sync
from utils.image_processor import process_image_for_print, image_to_bytes, create_four_cut_template
from utils.qr_generator import generate_qr_code
from PIL import Image
import io
import time

# 세션 상태 초기화
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# 관리자 비밀번호 확인 (.env 파일에서만 로드)
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # 기본값

# 로그인 페이지
if not st.session_state.admin_authenticated:
    st.title("🔐 관리자 로그인")
    st.markdown("### COM-ART AI Photo Booth")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password = st.text_input("관리자 비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            
            if submitted:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.success("✅ 로그인 성공!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
    
    st.stop()

# 자동 새로고침 (작업 중이 아닐 때만)
if 'selected_request' not in st.session_state and 'generated_result' not in st.session_state:
    count = st_autorefresh(interval=10000, limit=None, key="fizzbuzzcounter")

st.title("🛠️ COM-ART 관리자 대시보드")

# 사이드바: 상태 모니터링 및 설정
with st.sidebar:
    st.header("상태 모니터링")
    
    # 로그아웃 버튼
    if st.button("🚪 로그아웃"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    if st.button("🔄 지금 새로고침"):
        st.rerun()
    
    st.divider()
    
    # 통계 (간단한 카운트)
    try:
        active_reqs = get_all_active_requests()
        pending_count = len([r for r in active_reqs if r['status'] == 'pending'])
        completed_count = len([r for r in active_reqs if r['status'] == 'completed'])
        st.metric("대기 중", pending_count)
        st.metric("완료됨", completed_count)
    except Exception as e:
        st.error(f"통계 오류: {e}")

# 메인 콘텐츠
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 대기열 (Queue)")
    
    all_requests = get_all_active_requests()
    
    if not all_requests:
        st.info("요청이 없습니다.")
    else:
        # 대기열 리스트 표시
        for req in all_requests:
            queue_num = req.get('queue_number', 0)
            status = req.get('status', 'pending')
            
            # 상태별 표시
            if status == 'completed':
                border_color = "border: 2px solid #00cc00;"
                status_emoji = "✅"
            elif status == 'processing':
                border_color = "border: 2px solid #ffaa00;"
                status_emoji = "⏳"
            else:  # pending
                border_color = ""
                status_emoji = "⏸️"
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"{status_emoji} **번호:** `{queue_num:03d}`")
                    
                    # 4-cut 요청인지 확인
                    if req.get('style_types') and isinstance(req['style_types'], list):
                        styles = " → ".join(req['style_types'])
                        st.markdown(f"**스타일:** `[4컷] {styles}`")
                    else:
                        st.markdown(f"**스타일:** `{req['style_type']}`")
                    
                    st.caption(f"상태: {status} | 요청 시간: {req['created_at']}")
                with c2:
                    button_label = "확인" if status == 'completed' else "처리"
                    if st.button(button_label, key=f"btn_{req['id']}", use_container_width=True):
                        st.session_state.selected_request = req
                        # 완료된 요청인 경우 결과를 바로 로드
                        if status == 'completed' and req.get('output_image_url'):
                            try:
                                output_data = download_image("output_images", req['output_image_url'])
                                output_image = Image.open(io.BytesIO(output_data))
                                is_four_cut = req.get('style_types') is not None and isinstance(req['style_types'], list)
                                st.session_state.generated_result = {
                                    "image": output_image,
                                    "url": get_image_url("output_images", req['output_image_url']),
                                    "req": req,
                                    "is_four_cut": is_four_cut
                                }
                            except Exception as e:
                                st.error(f"결과 이미지 로드 실패: {e}")
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_{req['id']}", use_container_width=True, help="삭제"):
                        try:
                            delete_request(req['id'])
                            if 'selected_request' in st.session_state and st.session_state.selected_request['id'] == req['id']:
                                del st.session_state.selected_request
                            st.success("삭제되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")

with col2:
    st.subheader("🎨 작업 스테이션")
    
    # 결과가 있으면 결과 먼저 표시
    if 'generated_result' in st.session_state:
        # 결과 표시 섹션으로 건너뜀 (아래에서 처리)
        pass
    elif 'selected_request' in st.session_state:
        req = st.session_state.selected_request
        
        # 1. 원본 이미지 로드
        try:
            with st.spinner("원본 이미지를 다운로드 중입니다..."):
                img_data = download_image("input_images", req['input_image_url'])
                original_image = Image.open(io.BytesIO(img_data))
                
            c1, c2 = st.columns(2)
            with c1:
                st.image(original_image, caption="원본 이미지", use_column_width=True)
            with c2:
                # 4-cut 요청인지 확인
                is_four_cut = req.get('style_types') is not None and isinstance(req['style_types'], list)
                
                if is_four_cut:
                    style_types = req['style_types']
                    st.markdown(f"### 4컷 요청 (스타일: {len(style_types)}개)")
                    styles_display = " → ".join(style_types)
                    st.info(f"📸 {styles_display}")
                else:
                    st.markdown(f"### 단일 스타일: **{req['style_type']}**")
                
                st.markdown("AI 생성을 시작하려면 아래 버튼을 누르세요.")
                
                # 2. 생성 버튼
                button_label = "✨ 4컷 이미지 생성 시작" if is_four_cut else "✨ AI 이미지 생성 시작"
                
                if st.button(button_label, type="primary", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # 상태 업데이트: Processing
                        status_text.text("상태 업데이트 중...")
                        update_request_status(req['id'], "processing")
                        progress_bar.progress(5)
                        
                        if is_four_cut:
                            # === 4-CUT 모드 ===
                            status_text.text(f"4개 스타일 동시 생성 시작... (약 30-60초 소요)")
                            
                            # 병렬 생성
                            results = generate_multiple_styles_sync(original_image, style_types, max_retries=3)
                            progress_bar.progress(60)
                            
                            # 성공/실패 분류
                            generated_images = []
                            failed_styles = []
                            
                            for style in style_types:
                                img, error = results.get(style, (None, None))
                                if img is not None:
                                    generated_images.append(img)
                                    st.success(f"✅ {style} 생성 완료")
                                else:
                                    failed_styles.append(style)
                                    st.error(f"❌ {style} 생성 실패: {str(error)[:100] if error else '알 수 없는 오류'}")
                            
                            # 성공 개수 확인
                            if len(generated_images) != 4:
                                st.error(f"⚠️ {len(generated_images)}/4 개만 생성 완료. 실패한 스타일: {', '.join(failed_styles)}")
                                raise Exception(f"4개 중 {len(generated_images)}개만 생성됨")
                            
                            # 4개 모두 성공: 템플릿 생성
                            status_text.text("4컷 템플릿 생성 중...")
                            final_image = create_four_cut_template(generated_images)
                            progress_bar.progress(70)
                            
                        else:
                            # === 기존 단일 스타일 모드 ===
                            status_text.text(f"{req['style_type']} 스타일로 생성 중... (약 30초 소요)")
                            generated_image = generate_styled_image(original_image, req['style_type'])
                            progress_bar.progress(60)
                            
                            # 이미지 후처리 (리사이징/크롭)
                            status_text.text("인쇄용 규격으로 변환 중...")
                            final_image = process_image_for_print(generated_image)
                            progress_bar.progress(70)
                        
                        # 결과 업로드
                        status_text.text("결과 이미지 업로드 중...")
                        timestamp = int(time.time())
                        output_filename = f"result_{req['id']}_{timestamp}.png"
                        
                        img_bytes = image_to_bytes(final_image)
                        print(f"📤 output_images 버킷에 업로드 시작: {output_filename}")
                        output_path = upload_image(img_bytes, "output_images", output_filename)
                        progress_bar.progress(90)
                        
                        # 공개 URL 가져오기
                        public_url = get_image_url("output_images", output_path)
                        print(f"🔗 공개 URL 생성: {public_url}")
                        
                        # DB 업데이트: 파일 경로만 저장, 상태는 processing 유지
                        status_text.text("결과 저장 중...")
                        # 상태는 "완료" 버튼을 눌러야만 completed로 변경
                        response = supabase.table('booth_requests').update({
                            'output_image_url': output_path
                        }).eq('id', req['id']).execute()
                        progress_bar.progress(100)
                        
                        mode_text = "4컷 이미지" if is_four_cut else "이미지"
                        st.success(f"✅ {mode_text} 생성이 완료되었습니다!")
                        
                        # 결과를 세션 상태에 저장 (URL은 공개 URL 사용)
                        st.session_state.generated_result = {
                            "image": final_image,
                            "url": public_url,
                            "req": req,
                            "is_four_cut": is_four_cut
                        }
                        # 작업 완료 후에도 selected_request는 유지 (삭제 버튼으로만 제거)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
                        update_request_status(req['id'], "failed", error_msg=str(e))
        
        except Exception as e:
            st.error(f"원본 이미지 로드 실패: {e}")

    # 결과 표시 (생성 완료 후)
    if 'generated_result' in st.session_state:
        res = st.session_state.generated_result
        
        st.divider()
        is_four_cut = res.get('is_four_cut', False)
        title = "✅ 최종 4컷 결과 확인" if is_four_cut else "✅ 최종 결과 확인"
        st.subheader(title)
        
        r_col1, r_col2 = st.columns([1, 1])
        
        with r_col1:
            caption = "최종 결과물 (4컷 템플릿)" if is_four_cut else "최종 결과물 (4x6인치)"
            st.image(res['image'], caption=caption, use_column_width=True)
            
        with r_col2:
            st.markdown("#### 📱 다운로드용 QR 코드")
            # QR 코드 생성
            qr_img = generate_qr_code(res['url'])
            st.image(qr_img, width=200)
            
            st.markdown(f"🔗 [이미지 직접 다운로드]({res['url']})")
            
        # 버튼은 컬럼 밖에 배치
        col_done1, col_done2 = st.columns(2)
        with col_done1:
            if st.button("✅ 완료 표시", type="primary", use_container_width=True):
                # 상태를 completed로 변경 (대기열에는 계속 표시)
                try:
                    # DB에는 파일 경로만 저장되어 있으므로 그대로 유지
                    update_request_status(res['req']['id'], "completed", output_url=res['req'].get('output_image_url'))
                    # 세션 상태 초기화
                    del st.session_state.generated_result
                    if 'selected_request' in st.session_state:
                        del st.session_state.selected_request
                    st.success("완료 표시되었습니다! 대기열에서 ✅로 표시됩니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"완료 처리 실패: {e}")
        with col_done2:
            if st.button("🗑️ 요청 삭제", use_container_width=True):
                try:
                    delete_request(res['req']['id'])
                    del st.session_state.generated_result
                    if 'selected_request' in st.session_state:
                        del st.session_state.selected_request
                    st.success("요청이 삭제되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {e}")
