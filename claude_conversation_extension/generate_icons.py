try:
    from PIL import Image, ImageDraw, ImageFont
    
    # 아이콘 크기들
    sizes = [16, 48, 128]
    
    # 각 크기별로 아이콘 생성
    for size in sizes:
        # 새 이미지 생성 (RGBA 모드, 보라색 배경)
        img = Image.new('RGB', (size, size), (103, 58, 183))
        draw = ImageDraw.Draw(img)
        
        # 가운데에 원 그리기
        draw.ellipse((size//4, size//4, size - size//4, size - size//4), fill=(255, 255, 255))
        
        # 이미지 저장
        output_file = f"icon{size}.png"
        img.save(output_file)
        print(f"Created {output_file}")
        
except ImportError:
    # PIL이 없는 경우 수동으로 간단한 아이콘 생성
    import base64
    
    # 간단한 16x16 PNG 이미지 (보라색 사각형)
    icon16_base64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAIUlEQVR42mNk+M/wn4GKgHHUAIZRAwgmhWH2M4waQJIBAJszCgoTnoGDAAAAAElFTkSuQmCC"
    
    # 간단한 48x48 PNG 이미지 (보라색 사각형)
    icon48_base64 = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAALElEQVR42u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAO8GRvAAATgk16AAAAAASUVORK5CYII="
    
    # 간단한 128x128 PNG 이미지 (보라색 사각형)
    icon128_base64 = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAMUlEQVR42u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEcGRvAAATF4qSUAAAAASUVORK5CYII="
    
    # 이미지 데이터를 파일로 저장
    with open("icon16.png", "wb") as f:
        f.write(base64.b64decode(icon16_base64))
    print("Created icon16.png")
    
    with open("icon48.png", "wb") as f:
        f.write(base64.b64decode(icon48_base64))
    print("Created icon48.png")
    
    with open("icon128.png", "wb") as f:
        f.write(base64.b64decode(icon128_base64))
    print("Created icon128.png")

print("All icons generated successfully!")
