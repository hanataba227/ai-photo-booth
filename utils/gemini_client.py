import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API Key가 누락되었습니다. .env 파일을 확인하세요.")
    
    genai.configure(api_key=api_key)
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
- Person as detailed collectible figure/statue
- Placed on computer desk or shelf
- Retail box visible in background
- Product photography lighting
- Realistic shadows and reflections
- Fine details (texture, paint, joints)
- Depth of field (figure focused)
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
