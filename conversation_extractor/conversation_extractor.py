import cv2
import numpy as np
import pytesseract
import os
import argparse
from PIL import Image
import json
from datetime import datetime

# Tesseract 실행 파일 경로 설정 (설치 후 경로에 맞게 수정하세요)
# Windows 기준 기본 설치 경로
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ConversationExtractor:
    def __init__(self, tesseract_path=None):
        """
        대화 추출기 초기화
        
        Args:
            tesseract_path: Tesseract OCR 실행 파일 경로 (기본값 없음)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        # Tesseract가 설치되어 있는지 확인
        try:
            pytesseract.get_tesseract_version()
            print(f"Tesseract OCR 버전: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            print(f"Tesseract OCR을 찾을 수 없습니다. 설치 여부와 경로를 확인해주세요: {e}")
            print("다운로드: https://github.com/UB-Mannheim/tesseract/wiki")
            
    def preprocess_image(self, image):
        """
        OCR 정확도를 높이기 위한 이미지 전처리
        
        Args:
            image: 처리할 이미지
            
        Returns:
            전처리된 이미지
        """
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거를 위한 블러 적용
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 이진화
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 노이즈 제거
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return opening
    
    def extract_text_from_image(self, image_path, lang='kor+eng'):
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            lang: OCR 언어 (기본값: 한국어+영어)
            
        Returns:
            추출된 텍스트
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
            
            # 이미지 전처리
            processed_image = self.preprocess_image(image)
            
            # OCR 실행
            text = pytesseract.image_to_string(processed_image, lang=lang)
            return text
        
        except Exception as e:
            print(f"텍스트 추출 중 오류 발생: {e}")
            return ""
    
    def extract_conversations_from_image(self, image_path, output_file=None):
        """
        이미지에서 대화 추출 및 저장
        
        Args:
            image_path: 이미지 파일 경로
            output_file: 출력 파일 경로 (JSON 형식)
            
        Returns:
            추출된 대화 목록
        """
        text = self.extract_text_from_image(image_path)
        
        # 대화 구조 분석 (사용자와 AI 대화 구분)
        # 여기서는 간단한 예시로 구현합니다.
        # 실제로는 더 복잡한 패턴 매칭이 필요할 수 있습니다.
        
        lines = text.split('\n')
        conversations = []
        current_speaker = None
        current_message = []
        
        # Claude와 인간 대화 구분
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 대화 구분자 탐지 (예: 'Human:', 'Claude:' 등)
            if 'Human:' in line or '인간:' in line or '사용자:' in line:
                # 이전 메시지가 있으면 저장
                if current_speaker and current_message:
                    conversations.append({
                        "role": current_speaker,
                        "content": "\n".join(current_message)
                    })
                
                # 새 메시지 시작
                current_speaker = "user"
                current_message = [line.split(':', 1)[1].strip() if ':' in line else line]
            
            elif 'Claude:' in line or 'AI:' in line or '클로드:' in line:
                # 이전 메시지가 있으면 저장
                if current_speaker and current_message:
                    conversations.append({
                        "role": current_speaker,
                        "content": "\n".join(current_message)
                    })
                
                # 새 메시지 시작
                current_speaker = "assistant"
                current_message = [line.split(':', 1)[1].strip() if ':' in line else line]
            
            else:
                # 현재 진행 중인 메시지에 라인 추가
                if current_speaker:
                    current_message.append(line)
        
        # 마지막 메시지 처리
        if current_speaker and current_message:
            conversations.append({
                "role": current_speaker,
                "content": "\n".join(current_message)
            })
        
        # 결과 저장
        if output_file:
            result = {
                "conversations": conversations,
                "extracted_at": datetime.now().isoformat(),
                "source_image": os.path.basename(image_path)
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"대화를 {output_file}에 저장했습니다.")
        
        return conversations
    
    def generate_conversation_file(self, conversations, output_file):
        """
        추출된 대화로부터 새 대화 파일 생성
        
        Args:
            conversations: 대화 목록
            output_file: 출력 파일 경로 (JSON 또는 TXT)
        """
        # 파일 확장자에 따라 저장 형식 결정
        ext = os.path.splitext(output_file)[1].lower()
        
        if ext == '.json':
            # JSON 형식으로 저장
            data = {
                "conversations": conversations,
                "created_at": datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        elif ext == '.txt':
            # 텍스트 형식으로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                for conv in conversations:
                    role = "Human" if conv["role"] == "user" else "Claude"
                    f.write(f"{role}: {conv['content']}\n\n")
        
        print(f"대화를 {output_file}에 저장했습니다.")
    
    def import_conversation(self, file_path):
        """
        파일에서 대화 가져오기
        
        Args:
            file_path: 대화 파일 경로 (JSON 또는 TXT)
            
        Returns:
            가져온 대화 목록
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.json':
            # JSON 파일에서 가져오기
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'conversations' in data:
                return data['conversations']
            return []
            
        elif ext == '.txt':
            # 텍스트 파일에서 가져오기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 대화 파싱 (텍스트 파일 형식에 따라 조정 필요)
            conversations = []
            blocks = content.split('\n\n')
            
            for block in blocks:
                if not block.strip():
                    continue
                    
                if block.startswith('Human:'):
                    conversations.append({
                        "role": "user",
                        "content": block[6:].strip()
                    })
                elif block.startswith('Claude:'):
                    conversations.append({
                        "role": "assistant",
                        "content": block[7:].strip()
                    })
            
            return conversations
            
        return []


def main():
    """
    명령줄 인터페이스
    """
    parser = argparse.ArgumentParser(description='대화 추출 및 가져오기 도구')
    
    # 명령어 모드 그룹
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--extract', action='store_true', help='이미지에서 대화 추출')
    mode_group.add_argument('--import', dest='import_file', action='store_true', help='파일에서 대화 가져오기')
    
    # 공통 인자
    parser.add_argument('--tesseract', help='Tesseract OCR 실행 파일 경로')
    
    # 추출 모드 인자
    parser.add_argument('--image', help='처리할 이미지 파일 경로')
    parser.add_argument('--output', help='출력 파일 경로')
    parser.add_argument('--lang', default='kor+eng', help='OCR 언어 (기본값: kor+eng)')
    
    # 가져오기 모드 인자
    parser.add_argument('--file', help='가져올 대화 파일 경로')
    
    args = parser.parse_args()
    
    # 대화 추출기 초기화
    extractor = ConversationExtractor(args.tesseract)
    
    if args.extract:
        # 이미지에서 대화 추출
        if not args.image:
            parser.error("--extract 모드는 --image 인자가 필요합니다.")
        
        conversations = extractor.extract_conversations_from_image(args.image, args.output)
        
        # 결과 출력
        print(f"\n추출된 대화 ({len(conversations)}개):")
        for i, conv in enumerate(conversations):
            role = "Human" if conv["role"] == "user" else "Claude"
            content = conv["content"]
            if len(content) > 50:
                content = content[:50] + "..."
            print(f"{i+1}. {role}: {content}")
            
    elif args.import_file:
        # 파일에서 대화 가져오기
        if not args.file:
            parser.error("--import 모드는 --file 인자가 필요합니다.")
        
        conversations = extractor.import_conversation(args.file)
        
        # 결과 출력
        print(f"\n가져온 대화 ({len(conversations)}개):")
        for i, conv in enumerate(conversations):
            role = "Human" if conv["role"] == "user" else "Claude"
            content = conv["content"]
            if len(content) > 50:
                content = content[:50] + "..."
            print(f"{i+1}. {role}: {content}")
            
        # 새 파일로 저장
        if args.output:
            extractor.generate_conversation_file(conversations, args.output)


if __name__ == "__main__":
    main()
