import os
import sys
import cv2
import numpy as np
import pytesseract
import time
import json
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
import threading

# 캡처 영역 선택 및 OCR 추출 도구
class SimpleCaptureTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude 대화 캡처 도구")
        self.root.geometry("800x600")
        
        # Tesseract 경로
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # 출력 폴더
        self.output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captured_conversations")
        os.makedirs(self.output_folder, exist_ok=True)
        
        # 대화 데이터
        self.conversation_data = []
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 안내 텍스트
        ttk.Label(frame, text="화면 캡처 후 OCR 추출 도구", font=("Arial", 16)).pack(pady=10)
        
        # 버튼 프레임
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        # 캡처 버튼
        ttk.Button(button_frame, text="화면 캡처하기", command=self.capture_screen, width=20).pack(pady=5)
        
        # 이미지 파일 선택 버튼
        ttk.Button(button_frame, text="이미지 파일에서 추출", command=self.select_image, width=20).pack(pady=5)
        
        # 결과 프레임
        result_frame = ttk.LabelFrame(frame, text="추출 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 결과 텍스트 박스
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=15)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # 저장 버튼
        ttk.Button(frame, text="대화 저장하기", command=self.save_conversation).pack(pady=10)
        
        # 상태 표시줄
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def capture_screen(self):
        """화면 캡처"""
        # 최소화
        self.root.iconify()
        time.sleep(0.5)
        
        # 메시지
        messagebox.showinfo("안내", "캡처할 영역을 마우스로 드래그하여 선택하세요.")
        
        # PIL의 ImageGrab 사용
        try:
            # 사용자가 직접 드래그하여 캡처하도록 명령 프롬프트 창 열기
            os.system('cls' if os.name == 'nt' else 'clear')
            print("화면을 캡처합니다. 캡처할 영역을 선택하세요...")
            
            # 시스템 스크린샷 도구 호출 (Windows)
            import pyautogui
            
            # 클릭 스크린샷 모드 알림
            print("화면에서 캡처할 Claude 대화 영역을 클릭하세요...")
            time.sleep(1)
            
            # 사용자에게 선택 안내
            print("1. 먼저 왼쪽 상단 지점을 클릭하세요")
            x1, y1 = pyautogui.position()
            while not pyautogui.mouseDown():
                x1, y1 = pyautogui.position()
                time.sleep(0.1)
            
            pyautogui.mouseUp()
            print(f"왼쪽 상단 위치: ({x1}, {y1})")
            time.sleep(0.5)
            
            print("2. 이제 오른쪽 하단 지점을 클릭하세요")
            x2, y2 = pyautogui.position()
            while not pyautogui.mouseDown():
                x2, y2 = pyautogui.position()
                time.sleep(0.1)
                
            print(f"오른쪽 하단 위치: ({x2}, {y2})")
            time.sleep(0.5)
            
            # 좌표 정렬
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # 영역 캡처
            screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
            
            # 임시 파일로 저장
            temp_image_path = os.path.join(self.output_folder, "temp_capture.png")
            screenshot.save(temp_image_path)
            
            # 이미지 처리 및 OCR
            self.process_image(temp_image_path)
            
        except Exception as e:
            self.status_var.set(f"캡처 오류: {e}")
            messagebox.showerror("오류", f"화면 캡처 중 오류가 발생했습니다: {e}")
        
        # 창 복원
        self.root.deiconify()
    
    def select_image(self):
        """이미지 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), 
                ("모든 파일", "*.*")
            ]
        )
        
        if file_path:
            self.process_image(file_path)
    
    def process_image(self, image_path):
        """이미지 처리 및 OCR"""
        try:
            self.status_var.set("이미지 처리 중...")
            
            # Tesseract 설정
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            # 이미지 로드
            img = cv2.imread(image_path)
            
            # 이미지 처리
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR 실행
            text = pytesseract.image_to_string(thresh, lang='kor+eng')
            
            # 대화 구조 분석
            conversations = self.parse_conversations(text)
            
            # 결과 표시
            self.result_text.delete(1.0, tk.END)
            if conversations:
                for conv in conversations:
                    self.conversation_data.append(conv)
                    role = "Human" if conv["role"] == "user" else "Claude"
                    self.result_text.insert(tk.END, f"{role}: {conv['content']}\n\n")
                
                self.status_var.set(f"추출 완료: {len(conversations)}개 메시지")
            else:
                self.result_text.insert(tk.END, "대화를 추출하지 못했습니다. 다른 이미지를 시도해보세요.")
                self.status_var.set("추출 실패")
            
        except Exception as e:
            self.status_var.set(f"처리 오류: {e}")
            messagebox.showerror("오류", f"이미지 처리 중 오류가 발생했습니다: {e}")
    
    def parse_conversations(self, text):
        """대화 텍스트 파싱"""
        # Claude 웹 인터페이스의 대화 패턴 분석
        lines = text.split('\n')
        current_message = []
        human_pattern = re.compile(r'(Human|사용자|인간)\s*:')
        claude_pattern = re.compile(r'(Claude|AI|클로드)\s*:')
        
        conversations = []
        current_role = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 사용자 메시지 시작
            if human_pattern.search(line):
                # 이전 메시지 저장
                if current_role and current_message:
                    conversations.append({
                        "role": current_role,
                        "content": '\n'.join(current_message)
                    })
                
                # 새 메시지 시작
                current_role = "user"
                # 프롬프트 부분 제거
                message_start = human_pattern.search(line).end()
                current_message = [line[message_start:].strip()]
                
            # Claude 메시지 시작
            elif claude_pattern.search(line):
                # 이전 메시지 저장
                if current_role and current_message:
                    conversations.append({
                        "role": current_role,
                        "content": '\n'.join(current_message)
                    })
                
                # 새 메시지 시작
                current_role = "assistant"
                # 프롬프트 부분 제거
                message_start = claude_pattern.search(line).end()
                current_message = [line[message_start:].strip()]
                
            else:
                # 현재 진행 중인 메시지에 라인 추가
                if current_role:
                    current_message.append(line)
        
        # 마지막 메시지 저장
        if current_role and current_message:
            conversations.append({
                "role": current_role,
                "content": '\n'.join(current_message)
            })
        
        return conversations
    
    def save_conversation(self):
        """대화 저장"""
        if not self.conversation_data:
            messagebox.showinfo("알림", "저장할 대화가 없습니다.")
            return
        
        # 파일 경로 선택
        file_path = filedialog.asksaveasfilename(
            title="대화 저장",
            defaultextension=".json",
            filetypes=[
                ("JSON 파일", "*.json"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 파일 확장자 확인
            ext = os.path.splitext(file_path)[1].lower()
            
            # 데이터 준비
            data = {
                "conversations": self.conversation_data,
                "timestamp": datetime.now().isoformat(),
                "source": "claude_capture_tool"
            }
            
            # 파일 형식에 따라 저장
            if ext == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            elif ext == '.txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    for conv in self.conversation_data:
                        role = "Human" if conv["role"] == "user" else "Claude"
                        f.write(f"{role}: {conv['content']}\n\n")
            else:
                # 기본적으로 JSON으로 저장
                if not ext:
                    file_path += '.json'
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            
            self.status_var.set(f"대화가 {file_path}에 저장되었습니다.")
            messagebox.showinfo("저장 완료", f"대화가 {file_path}에 저장되었습니다.")
            
        except Exception as e:
            self.status_var.set(f"저장 오류: {e}")
            messagebox.showerror("저장 오류", f"대화 저장 중 오류가 발생했습니다: {e}")
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SimpleCaptureTool()
    app.run()
