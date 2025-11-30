import qrcode
from PIL import Image

def generate_qr_code(data: str) -> Image.Image:
    """
    주어진 데이터(URL)에 대한 QR 코드를 생성합니다.
    PIL 이미지를 반환합니다.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert('RGB')
