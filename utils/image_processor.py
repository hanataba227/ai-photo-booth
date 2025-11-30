from PIL import Image
import io

# 4x6cm @ 118dpi 상수
TARGET_WIDTH = 472   # 4 cm * 118 dpi / 2.54 cm/inch
TARGET_HEIGHT = 709  # 6 cm * 118 dpi / 2.54 cm/inch
ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT

def validate_image(file) -> bool:
    """
    업로드된 이미지 파일을 검증합니다.
    형식과 크기를 확인합니다.
    """
    try:
        img = Image.open(file)
        img.verify() # 이미지인지 확인
        
        # 파일 포인터 초기화
        file.seek(0)
        
        # 형식 확인
        if img.format not in ['JPEG', 'PNG']:
            return False
            
        # 크기 확인 (선택 사항, 예: 최소 400x400)
        # if img.width < 400 or img.height < 400:
        #     return False
            
        return True
    except Exception:
        return False

def process_image_for_print(image: Image.Image) -> Image.Image:
    """
    이미지를 대상 인쇄 크기(472x709px)에 맞게 리사이징하고 자릅니다.
    비율을 유지하며 중앙을 기준으로 자릅니다.
    """
    # RGBA인 경우 RGB로 변환 (일부 형식 문제 방지)
    if image.mode == 'RGBA':
        image = image.convert('RGB')
        
    img_ratio = image.width / image.height
    
    if img_ratio > ASPECT_RATIO:
        # 이미지가 대상보다 넓은 경우
        new_height = TARGET_HEIGHT
        new_width = int(new_height * img_ratio)
    else:
        # 이미지가 대상보다 높은 경우
        new_width = TARGET_WIDTH
        new_height = int(new_width / img_ratio)
        
    # 리사이징
    resized_img = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 중앙 자르기 (Center Crop)
    left = (new_width - TARGET_WIDTH) / 2
    top = (new_height - TARGET_HEIGHT) / 2
    right = (new_width + TARGET_WIDTH) / 2
    bottom = (new_height + TARGET_HEIGHT) / 2
    
    cropped_img = resized_img.crop((left, top, right, bottom))
    
    return cropped_img

def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
    """
    PIL 이미지를 바이트로 변환합니다.
    """
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
