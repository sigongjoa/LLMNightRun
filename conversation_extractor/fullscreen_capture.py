import os
import sys
import time
import json
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageGrab
import pyautogui

class FullscreenCaptureTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude 대화 전체 화면 캡처 도구")
        self.root.geometry("800x600")
        
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
        ttk.Label(frame, text="Claude 대화 전체 화면 캡처 도구", font=("Arial", 16)).pack(pady=10)
        ttk.Label(frame, text="Tesseract OCR 없이도 작동합니다").pack(pady=5)
        
        # 전체 화면 캡처 프레임
        capture_frame = ttk.LabelFrame(frame, text="화면 캡처", padding=10)
        capture_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 옵션 프레임
        options_frame = ttk.Frame(capture_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 지연 시간 옵션
        ttk.Label(options_frame, text="캡처 전 대기 시간(초):").pack(side=tk.LEFT, padx=5)
        self.delay_var = tk.IntVar(value=5)
        ttk.Spinbox(options_frame, from_=1, to=10, textvariable=self.delay_var, width=3).pack(side=tk.LEFT, padx=5)
        
        # 캡처 버튼
        ttk.Button(capture_frame, text="전체 화면 캡처하기", command=self.capture_fullscreen, width=20).pack(pady=10)
        
        # 이미지 파일 선택 버튼
        ttk.Button(capture_frame, text="이미지 파일에서 추출", command=self.select_image, width=20).pack(pady=5)
        
        # 결과 프레임
        result_frame = ttk.LabelFrame(frame, text="추출 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 텍스트 입력 설명
        ttk.Label(result_frame, text="아래에 대화 내용을 직접 붙여넣거나 수정할 수 있습니다:").pack(anchor=tk.W)
        
        # 결과 텍스트 박스
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=15)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # 변환 및 저장 프레임
        convert_frame = ttk.Frame(frame)
        convert_frame.pack(fill=tk.X, pady=5)
        
        # 형식 변환 버튼
        ttk.Button(convert_frame, text="텍스트를 대화 형식으로 변환", command=self.convert_to_conversation).pack(side=tk.LEFT, padx=5)
        
        # 저장 버튼
        ttk.Button(convert_frame, text="대화 저장하기", command=self.save_conversation).pack(side=tk.LEFT, padx=5)
        
        # 상태 표시줄
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def capture_fullscreen(self):
        """전체 화면 캡처"""
        try:
            # 대기 시간 설정
            delay = self.delay_var.get()
            
            # 창 최소화
            self.root.iconify()
            
            # 카운트다운
            for i in range(delay, 0, -1):
                print(f"캡처 준비 중... {i}초 후 캡처됩니다.")
                time.sleep(1)
            
            # 전체 화면 캡처
            screenshot = pyautogui.screenshot()
            
            # 임시 파일로 저장
            temp_image_path = os.path.join(self.output_folder, "fullscreen_capture.png")
            screenshot.save(temp_image_path)
            
            # 창 복원
            self.root.deiconify()
            
            # 캡처 성공 메시지
            self.status_var.set(f"전체 화면이 {temp_image_path}에 저장되었습니다.")
            messagebox.showinfo("캡처 완료", "전체 화면이 캡처되었습니다.\n이미지가 파일로 저장되었습니다.")
            
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
            self.status_var.set(f"이미지 파일이 선택되었습니다: {file_path}")
            messagebox.showinfo("파일 선택 완료", "이미지 파일이 선택되었습니다.\n이제 대화 내용을 수동으로 입력하세요.")
    
    def convert_to_conversation(self):
        """텍스트를 대화 형식으로 변환"""
        text = self.result_text.get(1.0, tk.END)
        if not text.strip():
            messagebox.showinfo("알림", "변환할 텍스트가 없습니다.")
            return
        
        try:
            # 대화 패턴 분석
            conversations = self.parse_conversations(text)
            
            # 대화 데이터 업데이트
            self.conversation_data = conversations
            
            # 결과 다시 표시
            self.result_text.delete(1.0, tk.END)
            for conv in conversations:
                role = "Human" if conv["role"] == "user" else "Claude"
                self.result_text.insert(tk.END, f"{role}: {conv['content']}\n\n")
            
            self.status_var.set(f"변환 완료: {len(conversations)}개 메시지")
            
        except Exception as e:
            self.status_var.set(f"변환 오류: {e}")
            messagebox.showerror("오류", f"텍스트 변환 중 오류가 발생했습니다: {e}")
    
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
        # 텍스트 가져오기
        text = self.result_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("알림", "저장할 대화가 없습니다.")
            return
        
        # 대화 형식으로 변환
        if not self.conversation_data:
            self.convert_to_conversation()
            if not self.conversation_data:
                # 기본 포맷으로 변환 (텍스트가 대화 형식이 아닌 경우)
                self.conversation_data = [{
                    "role": "assistant",
                    "content": text
                }]
        
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
                "source": "fullscreen_capture_tool"
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
        app = FullscreenCaptureTool()
        app.run()
    except Exception as e:
        print(f"프로그램 실행 중 오류가 발생했습니다: {e}")
        input("계속하려면 아무 키나 누르세요...")
