import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 초기화
def init_supabase() -> Client:
    try:
        # 먼저 환경 변수에서 로드 (로컬 개발용)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        # Streamlit secrets 체크 (배포용) - lazy import로 set_page_config 이전 실행 방지
        if not url or not key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "supabase" in st.secrets:
                    url = st.secrets["supabase"]["url"]
                    key = st.secrets["supabase"]["key"]
            except:
                pass

        if not url or not key:
            raise ValueError("Supabase URL 또는 Key가 누락되었습니다. .env 파일을 확인하세요.")

        return create_client(url, key)
    except Exception as e:
        print(f"Supabase 초기화 실패: {str(e)}")
        raise e

supabase = init_supabase()

def upload_image(file_bytes, bucket_name: str, file_path: str) -> str:
    """
    이미지를 Supabase Storage에 업로드하고 경로를 반환합니다.
    """
    try:
        response = supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": "image/png"}
        )
        print(f"✅ 업로드 성공: {bucket_name}/{file_path} ({len(file_bytes)/1024:.1f}KB)")
        return file_path
    except Exception as e:
        print(f"업로드 오류: {e}")
        raise e

def get_image_url(bucket_name: str, file_path: str) -> str:
    """
    공개 버킷의 파일에 대한 공개 URL을 가져옵니다.
    """
    try:
        # 공개 버킷용
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        print(f"URL 가져오기 오류: {e}")
        return None

def create_booth_request(style_type: str, input_image_path: str) -> dict:
    """
    booth_requests 테이블에 새 레코드를 생성합니다.
    순번(queue_number)을 자동으로 할당합니다.
    """
    try:
        # 현재 최대 순번 조회 (오늘 날짜 기준 또는 전체)
        response = supabase.table("booth_requests")\
            .select("queue_number")\
            .order("queue_number", desc=True)\
            .limit(1)\
            .execute()
        
        # 다음 순번 계산
        next_number = 0
        if response.data and len(response.data) > 0 and response.data[0].get("queue_number") is not None:
            next_number = response.data[0]["queue_number"] + 1
        
        data = {
            "style_type": style_type,
            "input_image_url": input_image_path,
            "status": "pending",
            "queue_number": next_number
        }
        response = supabase.table("booth_requests").insert(data).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"DB 삽입 오류: {e}")
        raise e

def get_pending_requests():
    """
    상태가 'pending'인 모든 요청을 생성 시간순으로 가져옵니다.
    """
    try:
        response = supabase.table("booth_requests")\
            .select("*")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return response.data
    except Exception as e:
        print(f"조회 오류: {e}")
        return []

def update_request_status(request_id: str, status: str, output_url: str = None, error_msg: str = None):
    """
    요청의 상태와 결과를 업데이트합니다.
    """
    try:
        data = {"status": status}
        if output_url:
            data["output_image_url"] = output_url
        if error_msg:
            data["error_message"] = error_msg
            
        response = supabase.table("booth_requests")\
            .update(data)\
            .eq("id", request_id)\
            .execute()
        return response.data
    except Exception as e:
        print(f"업데이트 오류: {e}")
        raise e

def delete_request(request_id: str):
    """
    요청을 삭제합니다.
    """
    try:
        response = supabase.table("booth_requests")\
            .delete()\
            .eq("id", request_id)\
            .execute()
        return response.data
    except Exception as e:
        print(f"삭제 오류: {e}")
        raise e

def download_image(bucket_name: str, file_path: str) -> bytes:
    """
    Supabase Storage에서 이미지를 다운로드합니다.
    """
    try:
        response = supabase.storage.from_(bucket_name).download(file_path)
        print(f"✅ 다운로드 성공: {file_path} ({len(response)/1024:.1f}KB)")
        return response
    except Exception as e:
        print(f"다운로드 오류: {e}")
        raise e
