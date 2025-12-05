import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Streamlit secrets에서 로드 시도
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "gemini" in st.secrets:
                api_key = st.secrets["gemini"]["api_key"]
        except:
            pass
    
    if not api_key:
        raise ValueError("Gemini API Key가 누락되었습니다. .env 파일을 확인하세요.")
    
    # API 키로만 인증 (메타데이터 서버 사용 안 함)
    genai.configure(
        api_key=api_key,
        transport='rest',  # REST API 사용 강제
        client_options={"api_endpoint": "generativelanguage.googleapis.com"}
    )
    return True

# 초기 설정
try:
    configure_gemini()
except Exception as e:
    print(f"Gemini 설정 실패: {str(e)}")

# 모델 설정
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image")

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# 스타일 프롬프트 (모두 2:3 세로 비율로 생성)
STYLE_PROMPTS = {
    "lego": """Transform this person into a LEGO minifigure character.
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
- Person as LEGO minifigure with yellow cylindrical head and round studs
- Classic LEGO face: dot eyes, curved smile
- Blocky body made of LEGO bricks
- Background: colorful LEGO brick world
- Bright, saturated LEGO colors
- Keep original hair color/style in LEGO form
- Maintain pose and composition""",
    
    "anime": """Convert this person into Studio Ghibli anime style.
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
- Large expressive anime eyes with highlights
- Soft hand-drawn aesthetic
- Flowing hair with anime shine
- Gentle cel-shading
- Vibrant but natural colors
- Dreamy atmospheric lighting
- Maintain person's features while stylizing
- Warm emotional atmosphere""",
    
    "pixel": """Recreate this person as 8-bit retro pixel art.
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
- Limited 16-24 color palette
- Clear square pixels, NO anti-aliasing
- Recognizable features in pixel blocks
- Dithering for gradients
- 1980s-90s arcade game style
- Bold pixel outlines
- Simple retro gaming background
- Clear readable composition""",
    
    "clay": """Transform this person into adorable clay figure (Wallace & Gromit style).
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
- Hand-sculpted from modeling clay
- Visible fingerprints and clay textures
- Very soft rounded shapes, no sharp edges
- Matte clay finish
- Simplified cute features
- Warm pastel colors
- Soft studio lighting
- Charming playful character""",

    "business": """Create professional dramatic studio portrait.
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
- Professional studio photography
- Shot from slightly low angle
- High-contrast dramatic lighting
- Dark professional attire (suit/formal)
- Solid deep crimson red background
- Sculptural cinematic lighting
- Maintain exact facial features
- Powerful commanding composition
- Fashion editorial style""",

    "figure": """Create hyper-realistic collectible figure product photo.
CRITICAL: Generate in 2:3 PORTRAIT aspect ratio (taller than wide).
CRITICAL: Show COMPLETE FULL BODY from head to toe, no cropping of legs or feet.
- Person as detailed collectible figure/statue
- FULL BODY visible: head, torso, legs, and feet completely shown
- Standing pose with proper proportions
- Placed on computer desk or shelf
- Retail box visible in background
- Product photography lighting with proper distance
- Realistic shadows and reflections
- Fine details (texture, paint, joints)
- Depth of field (figure focused)
- Camera positioned to capture entire figure
- Desk items for scale
- Maintain character likeness in figure form"""
}

def generate_styled_image(input_image: Image.Image, style_type: str) -> Image.Image:
    """
    Gemini 2.5 Flash Image Preview를 사용하여 스타일이 적용된 이미지를 생성합니다.
    """
    if style_type not in STYLE_PROMPTS:
        raise ValueError(f"알 수 없는 스타일 유형: {style_type}")
        
    prompt = STYLE_PROMPTS[style_type]
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # 이미지 편집 프롬프트 (imagen 스타일)
        edit_prompt = f"""Generate a new image based on this input image with the following style:

{prompt}

Important: Generate a complete new image, not text description."""
        
        response = model.generate_content(
            [edit_prompt, input_image],
            generation_config=GENERATION_CONFIG
        )
        
        print(f"[이미지 생성 완료] Response has {len(response.parts) if hasattr(response, 'parts') else 0} parts")
        
        # 응답에 이미지가 포함되어 있는지 확인
        if not response.parts:
            raise ValueError("생성된 콘텐츠가 없습니다.")
             
        # 다양한 방식으로 이미지 추출 시도
        
        # 1. response.images 속성
        if hasattr(response, 'images') and response.images:
            print(f"[DEBUG] Found {len(response.images)} images in response.images")
            return response.images[0]
             
        # 2. parts 내에 inline_data가 있는 경우 (바이너리 이미지 데이터)
        for i, part in enumerate(response.parts):
            if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'data'):
                image_data = part.inline_data.data
                
                # 문자열이면 base64 디코딩
                if isinstance(image_data, str):
                    import base64
                    image_data = base64.b64decode(image_data)
                
                # bytes인지 확인
                if isinstance(image_data, bytes) and len(image_data) > 0:
                    try:
                        from io import BytesIO
                        img = Image.open(BytesIO(image_data))
                        print(f"✅ 이미지 생성 성공: {img.format}, {img.size}, {len(image_data)/1024:.1f}KB")
                        return img
                    except Exception as e:
                        print(f"❌ 이미지 열기 실패: {e}")
                        continue
        
        # 텍스트만 반환된 경우
        if hasattr(response, 'text'):
            print(f"⚠️ 텍스트 응답만 받음: {response.text[:200]}")
                
        raise ValueError(f"응답에서 이미지를 찾을 수 없습니다. Gemini 모델이 텍스트만 반환했을 수 있습니다.")

    except Exception as e:
        print(f"Gemini 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        raise e


# 4-cut 기능을 위한 병렬 생성 함수
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional

async def generate_multiple_styles_async(
    input_image: Image.Image, 
    style_types: List[str],
    max_retries: int = 3
) -> Dict[str, Tuple[Optional[Image.Image], Optional[Exception]]]:
    """
    여러 스타일의 이미지를 동시에 생성합니다 (asyncio + ThreadPoolExecutor 사용).
    
    Args:
        input_image: 입력 이미지
        style_types: 생성할 스타일 타입 리스트 (예: ["lego", "anime", "pixel", "clay"])
        max_retries: 실패 시 재시도 횟수
    
    Returns:
        Dict[style_type, (generated_image or None, error or None)]
        성공: {style: (Image, None)}
        실패: {style: (None, Exception)}
    """
    loop = asyncio.get_event_loop()
    
    async def generate_one_with_retry(style: str) -> Tuple[str, Optional[Image.Image], Optional[Exception]]:
        """단일 스타일 생성 (재시도 포함)"""
        for attempt in range(max_retries):
            try:
                print(f"🎨 [{style}] 생성 시작 (시도 {attempt + 1}/{max_retries})")
                
                # ThreadPoolExecutor를 사용하여 동기 함수를 비동기로 실행
                img = await loop.run_in_executor(
                    None,
                    generate_styled_image,
                    input_image,
                    style
                )
                
                print(f"✅ [{style}] 생성 완료")
                return style, img, None
                
            except Exception as e:
                print(f"❌ [{style}] 생성 실패 (시도 {attempt + 1}/{max_retries}): {str(e)[:100]}")
                if attempt == max_retries - 1:
                    # 마지막 시도 실패
                    return style, None, e
                # 재시도 전 잠시 대기
                await asyncio.sleep(1)
        
        return style, None, Exception("알 수 없는 오류")
    
    # 모든 스타일 동시 생성
    print(f"🚀 {len(style_types)}개 스타일 동시 생성 시작: {style_types}")
    tasks = [generate_one_with_retry(style) for style in style_types]
    results = await asyncio.gather(*tasks)
    
    # 결과를 딕셔너리로 변환
    result_dict = {}
    for style, img, error in results:
        result_dict[style] = (img, error)
    
    # 통계 출력
    success_count = sum(1 for img, err in result_dict.values() if img is not None)
    print(f"📊 생성 완료: {success_count}/{len(style_types)} 성공")
    
    return result_dict


def generate_multiple_styles_sync(
    input_image: Image.Image, 
    style_types: List[str],
    max_retries: int = 3
) -> Dict[str, Tuple[Optional[Image.Image], Optional[Exception]]]:
    """
    generate_multiple_styles_async의 동기 버전 (Streamlit에서 사용하기 쉽도록).
    
    Args:
        input_image: 입력 이미지
        style_types: 생성할 스타일 타입 리스트
        max_retries: 실패 시 재시도 횟수
    
    Returns:
        Dict[style_type, (generated_image or None, error or None)]
    """
    return asyncio.run(generate_multiple_styles_async(input_image, style_types, max_retries))
