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
from PIL import Image, ImageGrab
import pyautogui

class VerySimpleCaptureTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude 대화 캡처 도구 (단순 버전)")
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
        ttk.Label(frame, text="Claude 대화 캡처 도구", font=("Arial", 16)).pack(pady=10)
        
        # 캡처 좌표 입력 프레임
        coords_frame = ttk.LabelFrame(frame, text="캡처 영역 좌표", padding=10)
        coords_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 좌표 입력 필드
        coords_inner_frame = ttk.Frame(coords_frame)
        coords_inner_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(coords_inner_frame, text="왼쪽 상단 X:").grid(row=0, column=0, padx=5, pady=5)
        self.x1_var = tk.IntVar(value=100)
        ttk.Entry(coords_inner_frame, textvariable=self.x1_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(coords_inner_frame, text="왼쪽 상단 Y:").grid(row=0, column=2, padx=5, pady=5)
        self.y1_var = tk.IntVar(value=100)
        ttk.Entry(coords_inner_frame, textvariable=self.y1_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(coords_inner_frame, text="오른쪽 하단 X:").grid(row=0, column=4, padx=5, pady=5)
        self.x2_var = tk.IntVar(value=500)
        ttk.Entry(coords_inner_frame, textvariable=self.x2_var, width=5).grid(row=0, column=5, padx=5, pady=5)
        
        ttk.Label(coords_inner_frame, text="오른쪽 하단 Y:").grid(row=0, column=6, padx=5, pady=5)
        self.y2_var = tk.IntVar(value=500)
        ttk.Entry(coords_inner_frame, textvariable=self.y2_var, width=5).grid(row=0, column=7, padx=5, pady=5)
        
        # 현재 마우스 위치 표시 버튼
        ttk.Button(coords_frame, text="현재 마우스 위치 가져오기", command=self.get_mouse_position).pack(pady=5)
        
        # 좌표 상태 표시
        self.coords_status = ttk.Label(coords_frame, text="")
        self.coords_status.pack(pady=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        # 캡처 버튼
        ttk.Button(button_frame, text="입력된 좌표로 캡처하기", command=self.capture_from_coords, width=20).pack(side=tk.LEFT, padx=5)
        
        # 이미지 파일 선택 버튼
        ttk.Button(button_frame, text="이미지 파일에서 추출", command=self.select_image, width=20).pack(side=tk.LEFT, padx=5)
        
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
        
        # 타이머 시작
        self.update_mouse_position()
    
    def update_mouse_position(self):
        """마우스 위치 실시간 업데이트"""
        try:
            x, y = pyautogui.position()
            self.coords_status.config(text=f"현재 마우스 위치: X={x}, Y={y}")
            self.root.after(100, self.update_mouse_position)
        except:
            pass
    
    def get_mouse_position(self):
        """현재 마우스 위치 가져오기"""
        try:
            # 윈도우 최소화
            self.root.iconify()
            messagebox.showinfo("안내", "지정하려는 위치로 마우스를 이동한 후 아무 키나 누르세요.")
            
            # 키 입력 대기
            os.system('pause')
            
            # 현재 마우스 위치 가져오기
            x, y = pyautogui.position()
            
            # 창 복원
            self.root.deiconify()
            
            # 선택된 타입에 따라 좌표 설정
            response = messagebox.askyesno("위치 선택", f"위치 X={x}, Y={y}를 왼쪽 상단 지점으로 설정하시겠습니까?\n'아니오'를 선택하면 오른쪽 하단 지점으로 설정됩니다.")
            
            if response:
                self.x1_var.set(x)
                self.y1_var.set(y)
            else:
                self.x2_var.set(x)
                self.y2_var.set(y)
                
        except Exception as e:
            messagebox.showerror("오류", f"마우스 위치를 가져오는 중 오류가 발생했습니다: {e}")
            self.root.deiconify()
    
    def capture_from_coords(self):
        """입력된 좌표로 화면 캡처"""
        try:
            # 좌표 가져오기
            x1 = self.x1_var.get()
            y1 = self.y1_var.get()
            x2 = self.x2_var.get()
            y2 = self.y2_var.get()
            
            # 좌표 유효성 검사
            if x1 >= x2 or y1 >= y2:
                messagebox.showerror("좌표 오류", "오른쪽 하단 좌표는 왼쪽 상단 좌표보다 커야 합니다.")
                return
            
            # 5초 카운트다운
            self.root.iconify()
            for i in range(5, 0, -1):
                print(f"캡처 준비 중... {i}초 후 캡처됩니다.")
                time.sleep(1)
            
            # 화면 캡처
            width = x2 - x1
            height = y2 - y1
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            
            # 임시 파일로 저장
            temp_image_path = os.path.join(self.output_folder, "temp_capture.png")
            screenshot.save(temp_image_path)
            
            # 이미지 처리 및 OCR
            self.process_image(temp_image_path)
            
            # 창 복원
            self.root.deiconify()
            
        except Exception as e:
            self.root.deiconify()
            self.status_var.set(f"캡처 오류: {e}")
            messagebox.showerror("오류", f"화면 캡처 중 오류가 발생했습니다: {e}")
    
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
    try:
        app = VerySimpleCaptureTool()
        app.run()
    except Exception as e:
        print(f"프로그램 실행 중 오류가 발생했습니다: {e}")
        input("계속하려면 아무 키나 누르세요...")
