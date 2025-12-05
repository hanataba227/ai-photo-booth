from PIL import Image, ImageOps
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
        img = Image.open(file)
        # EXIF 회전 정보 자동 적용
        img = ImageOps.exif_transpose(img)
        
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

def create_four_cut_template(images: list, layout="grid") -> Image.Image:
    """
    4개의 이미지를 2x2 그리드 템플릿으로 합성
    기존 4x6 비율(472x709)을 유지하여 각 셀은 세로가 더 긴 형태
    
    Args:
        images: 4개의 PIL Image 객체 리스트
        layout: "grid" (2x2) - 현재는 grid만 지원
    
    Returns:
        합성된 최종 이미지 (기존 4x6 비율 유지)
    """
    if len(images) != 4:
        raise ValueError(f"정확히 4개의 이미지가 필요합니다. (현재: {len(images)}개)")
    
    # 설정 - 기존 4x6 비율 유지 (TARGET_WIDTH=472, TARGET_HEIGHT=709)
    cell_width = TARGET_WIDTH   # 472px
    cell_height = TARGET_HEIGHT  # 709px
    margin = 10  # 이미지 사이 여백
    border = 0  # 외곽 테두리는 0으로 설정
    
    # 2x2 그리드 배치 - 전체 크기는 (472*2+10) x (709*2+10)
    canvas_width = (cell_width * 2) + margin
    canvas_height = (cell_height * 2) + margin
    
    # 흰색 배경 캔버스 생성
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    
    # 4개 위치 정의 (좌상, 우상, 좌하, 우하)
    positions = [
        (0, 0),  # 좌상
        (cell_width + margin, 0),  # 우상
        (0, cell_height + margin),  # 좌하
        (cell_width + margin, cell_height + margin)  # 우하
    ]
    
    for idx, (img, pos) in enumerate(zip(images, positions)):
        # 이미지 리사이즈 (비율 유지하며 크롭)
        img_ratio = img.width / img.height
        target_ratio = cell_width / cell_height
        
        if img_ratio > target_ratio:
            # 이미지가 더 넓음 - 높이 기준으로 리사이즈
            new_height = cell_height
            new_width = int(new_height * img_ratio)
        else:
            # 이미지가 더 높음 - 너비 기준으로 리사이즈
            new_width = cell_width
            new_height = int(new_width / img_ratio)
        
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 중앙 크롭
        left = (new_width - cell_width) / 2
        top = (new_height - cell_height) / 2
        right = (new_width + cell_width) / 2
        bottom = (new_height + cell_height) / 2
        cropped = resized.crop((left, top, right, bottom))
        
        # 캔버스에 붙이기
        canvas.paste(cropped, pos)
    
    return canvas
