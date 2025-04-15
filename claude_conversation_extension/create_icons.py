from PIL import Image, ImageDraw, ImageFont
import os

# 아이콘 크기들
sizes = [16, 48, 128]

# 각 크기별로 아이콘 생성
for size in sizes:
    # 새 이미지 생성 (RGBA 모드, 보라색 배경)
    img = Image.new('RGBA', (size, size), (103, 58, 183, 255))
    draw = ImageDraw.Draw(img)
    
    # 텍스트 크기 계산 (아이콘 크기에 비례)
    font_size = int(size * 0.75)
    
    try:
        # 폰트 로드 시도
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # 폰트 로드 실패 시 기본 폰트 사용
        font = ImageFont.load_default()
    
    # 텍스트 위치 계산 (중앙 정렬)
    text = "C"
    text_width = font_size
    text_height = font_size
    position = ((size - text_width) // 2, (size - text_height) // 2)
    
    # 텍스트 그리기
    draw.text(position, text, font=font, fill=(255, 255, 255, 255))
    
    # 이미지 저장
    img.save(f"icon{size}.png")
    
print(f"Created icons: {', '.join([f'icon{size}.png' for size in sizes])}")
