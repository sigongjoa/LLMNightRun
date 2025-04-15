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
from PIL import Image, ImageTk
import threading

# 필요한 라이브러리 확인 및 설치
try:
    import pyautogui
except ImportError:
    print("pyautogui 라이브러리를 설치합니다...")
    os.system("pip install pyautogui")
    import pyautogui

class ClaudeConversationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude 대화 도구")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)
        
        # Tesseract 경로
        self.tesseract_path = tk.StringVar(value=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        try:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.get()
        except:
            print("Tesseract 경로를 확인하세요.")
        
        # 출력 폴더
        self.output_folder = tk.StringVar(value=os.path.join(os.path.dirname(os.path.abspath(__file__)), "captured_conversations"))
        os.makedirs(self.output_folder.get(), exist_ok=True)
        
        # 캡처 간격(초)
        self.capture_interval = tk.IntVar(value=5)
        
        # 캡처 영역
        self.capture_area = None
        
        # 자동 캡처 상태
        self.is_capturing = False
        self.capture_thread = None
        
        # 추출된 대화
        self.conversation_data = []
        self.last_processed_text = ""
        
        # 파일명
        self.filename = tk.StringVar(value=f"claude_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # UI 초기화
        self.setup_ui()
        
        # 설정 불러오기
        self.load_settings()
        
    def setup_ui(self):
        """UI 구성"""
        # 노트북(탭) 생성
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 자동 캡처 탭
        self.auto_capture_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.auto_capture_frame, text="자동 캡처")
        
        # 이미지 추출 탭
        self.image_extract_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_extract_frame, text="이미지에서 추출")
        
        # 설정 탭
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="설정")
        
        # 자동 캡처 탭 설정
        self.setup_auto_capture_tab()
        
        # 이미지 추출 탭 설정
        self.setup_image_extract_tab()
        
        # 설정 탭 설정
        self.setup_settings_tab()
        
        # 상태 표시줄
        self.status_var = tk.StringVar(value="준비됨")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_auto_capture_tab(self):
        """자동 캡처 탭 설정"""
        frame = self.auto_capture_frame
        
        # 캡처 영역 선택 프레임
        area_frame = ttk.LabelFrame(frame, text="캡처 영역", padding=10)
        area_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 영역 선택 버튼
        ttk.Button(area_frame, text="캡처 영역 선택", command=self.select_capture_area).pack(side=tk.LEFT, padx=5)
        
        # 현재 선택된 영역 표시
        self.area_label = ttk.Label(area_frame, text="선택된 영역: 없음")
        self.area_label.pack(side=tk.LEFT, padx=10)
        
        # 제어 버튼 프레임
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 시작/중지 버튼
        self.start_button = ttk.Button(control_frame, text="캡처 시작", command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="캡처 중지", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 저장 버튼
        ttk.Button(control_frame, text="대화 저장", command=self.save_conversation).pack(side=tk.LEFT, padx=5)
        
        # 미리보기 프레임
        preview_frame = ttk.LabelFrame(frame, text="캡처 미리보기", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 미리보기 캔버스
        self.preview_canvas = tk.Canvas(preview_frame, bg="white")
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 캔버스 스크롤바
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_canvas.configure(yscrollcommand=preview_scrollbar.set)
        
        # 추출된 텍스트 프레임
        text_frame = ttk.LabelFrame(frame, text="추출된 대화", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 추출된 텍스트 표시 텍스트 박스
        self.text_box = tk.Text(text_frame, wrap=tk.WORD, height=10)
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 텍스트 박스 스크롤바
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_box.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_box.configure(yscrollcommand=text_scrollbar.set)
    
    def setup_image_extract_tab(self):
        """이미지 추출 탭 설정"""
        frame = self.image_extract_frame
        
        # 이미지 선택 프레임
        file_frame = ttk.LabelFrame(frame, text="이미지 파일", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 이미지 경로
        self.image_path = tk.StringVar()
        
        # 이미지 파일 선택
        ttk.Label(file_frame, text="이미지 파일:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.image_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="찾아보기", command=self.browse_image).grid(row=0, column=2, padx=5, pady=5)
        
        # 추출 버튼
        ttk.Button(file_frame, text="대화 추출", command=self.extract_from_image).grid(row=1, column=1, padx=5, pady=10)
        
        # 미리보기 프레임
        preview_frame = ttk.LabelFrame(frame, text="이미지 미리보기", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 이미지 미리보기 캔버스
        self.image_preview_canvas = tk.Canvas(preview_frame, bg="white")
        self.image_preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 캔버스 스크롤바
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.image_preview_canvas.yview)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_preview_canvas.configure(yscrollcommand=preview_scrollbar.set)
        
        # 추출된 텍스트 프레임
        text_frame = ttk.LabelFrame(frame, text="추출된 대화", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 추출된 텍스트 표시 텍스트 박스
        self.image_text_box = tk.Text(text_frame, wrap=tk.WORD, height=10)
        self.image_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 텍스트 박스 스크롤바
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.image_text_box.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_text_box.configure(yscrollcommand=text_scrollbar.set)
    
    def setup_settings_tab(self):
        """설정 탭 설정"""
        frame = self.settings_frame
        
        # 설정 프레임
        settings_inner_frame = ttk.Frame(frame, padding=10)
        settings_inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tesseract 경로 설정
        ttk.Label(settings_inner_frame, text="Tesseract 경로:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(settings_inner_frame, textvariable=self.tesseract_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(settings_inner_frame, text="찾아보기", command=self.browse_tesseract_path).grid(row=0, column=2, padx=5, pady=5)
        
        # 출력 폴더 설정
        ttk.Label(settings_inner_frame, text="출력 폴더:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(settings_inner_frame, textvariable=self.output_folder, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(settings_inner_frame, text="찾아보기", command=self.browse_output_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # 파일명 설정
        ttk.Label(settings_inner_frame, text="파일명:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(settings_inner_frame, textvariable=self.filename, width=50).grid(row=2, column=1, padx=5, pady=5)
        
        # 캡처 간격 설정
        ttk.Label(settings_inner_frame, text="캡처 간격(초):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_inner_frame, from_=1, to=60, textvariable=self.capture_interval, width=5).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 설정 저장 버튼
        ttk.Button(settings_inner_frame, text="설정 저장", command=self.save_settings).grid(row=4, column=1, pady=20)
        
        # Tesseract 다운로드 링크
        download_link = ttk.Label(settings_inner_frame, text="Tesseract OCR 다운로드", foreground="blue", cursor="hand2")
        download_link.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        download_link.bind("<Button-1>", lambda e: self.open_url("https://github.com/UB-Mannheim/tesseract/wiki"))
        
        # 안내 텍스트
        info_text = """
        1. Tesseract OCR 설치:
           - 위 링크에서 Tesseract OCR을 다운로드하여 설치하세요.
           - '한국어' 및 '영어' 언어 패키지를 함께 설치하세요.
        
        2. 자동 캡처 사용법:
           - '자동 캡처' 탭에서 '캡처 영역 선택' 버튼을 클릭하여 Claude 대화 영역을 선택하세요.
           - '캡처 시작' 버튼을 클릭하면 선택된 영역이 주기적으로 캡처되어 대화가 추출됩니다.
           - '캡처 중지' 버튼으로 언제든지 중지할 수 있습니다.
           - '대화 저장' 버튼으로 추출된 대화를 파일로 저장합니다.
        
        3. 이미지 추출 사용법:
           - '이미지에서 추출' 탭에서 대화가 포함된 이미지 파일을 선택하세요.
           - '대화 추출' 버튼을 클릭하면 이미지에서 대화가 추출됩니다.
        """
        
        info_label = tk.Text(settings_inner_frame, wrap=tk.WORD, height=15, width=65, bg="#f0f0f0")
        info_label.grid(row=6, column=0, columnspan=3, padx=5, pady=5)
        info_label.insert(tk.END, info_text)
        info_label.config(state=tk.DISABLED)
    
    def browse_tesseract_path(self):
        """Tesseract 경로 찾아보기"""
        file_path = filedialog.askopenfilename(
            title="Tesseract 실행 파일 선택",
            filetypes=[("실행 파일", "*.exe"), ("모든 파일", "*.*")]
        )
        if file_path:
            self.tesseract_path.set(file_path)
            try:
                pytesseract.pytesseract.tesseract_cmd = file_path
                version = pytesseract.get_tesseract_version()
                self.status_var.set(f"Tesseract OCR 버전: {version}")
            except Exception as e:
                self.status_var.set(f"오류: Tesseract OCR을 로드할 수 없습니다. - {e}")
    
    def browse_output_folder(self):
        """출력 폴더 찾아보기"""
        folder_path = filedialog.askdirectory(title="출력 폴더 선택")
        if folder_path:
            self.output_folder.set(folder_path)
            os.makedirs(folder_path, exist_ok=True)
    
    def browse_image(self):
        """이미지 파일 찾아보기"""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.image_path.set(file_path)
            self.show_image_preview(file_path)
    
    def show_image_preview(self, image_path):
        """이미지 미리보기 표시"""
        try:
            # 이미지 로드
            img = Image.open(image_path)
            
            # 캔버스 크기에 맞게 조정
            canvas_width = self.image_preview_canvas.winfo_width()
            if canvas_width < 10:  # 초기화 단계인 경우
                canvas_width = 700
                
            # 비율 유지하며 크기 조정
            img_width, img_height = img.size
            new_width = min(img_width, canvas_width - 20)
            ratio = new_width / img_width
            new_height = int(img_height * ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Tkinter 이미지로 변환
            self.tk_img = ImageTk.PhotoImage(img)
            
            # 캔버스 크기 조정
            self.image_preview_canvas.config(scrollregion=(0, 0, new_width, new_height))
            
            # 이미지 표시
            self.image_preview_canvas.delete("all")
            self.image_preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
            
        except Exception as e:
            messagebox.showerror("이미지 로드 오류", f"이미지를 불러올 수 없습니다: {e}")
    
    def extract_from_image(self):
        """이미지에서 대화 추출"""
        if not self.image_path.get():
            messagebox.showerror("오류", "이미지 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.image_path.get()):
            messagebox.showerror("오류", "선택한 이미지 파일이 존재하지 않습니다.")
            return
        
        try:
            # Tesseract 경로 설정
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.get()
            
            # 이미지 로드
            img = cv2.imread(self.image_path.get())
            
            # 이미지 처리
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR 실행
            text = pytesseract.image_to_string(thresh, lang='kor+eng')
            
            # 대화 구조 분석
            self.image_text_box.delete(1.0, tk.END)
            
            # 대화 패턴 분석
            conversations = self.parse_conversations(text)
            
            # 결과 표시
            if conversations:
                for conv in conversations:
                    role = "Human" if conv["role"] == "user" else "Claude"
                    self.image_text_box.insert(tk.END, f"{role}: {conv['content']}\n\n")
                
                # 저장 여부 확인
                if messagebox.askyesno("저장", "추출된 대화를 파일로 저장하시겠습니까?"):
                    self.save_conversations_to_file(conversations)
            else:
                self.image_text_box.insert(tk.END, "대화를 추출하지 못했습니다. 다른 이미지를 시도해보세요.")
                
        except Exception as e:
            messagebox.showerror("추출 오류", f"대화 추출 중 오류가 발생했습니다: {e}")
    
    def select_capture_area(self):
        """캡처 영역 선택"""
        self.root.iconify()  # 메인 창 최소화
        time.sleep(0.5)  # 잠시 대기
        
        try:
            # 영역 선택 창
            select_root = tk.Toplevel()
            select_root.attributes('-fullscreen', True)
            select_root.attributes('-alpha', 0.3)  # 반투명 설정
            select_root.configure(bg='black')
            
            # 선택 상태 변수
            start_x = start_y = end_x = end_y = None
            is_selecting = False
            
            # 캔버스 생성
            canvas = tk.Canvas(select_root, bg='', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # 안내 텍스트
            canvas.create_text(
                select_root.winfo_screenwidth() // 2,
                select_root.winfo_screenheight() // 2,
                text="마우스로 Claude 대화 영역을 드래그하여 선택하세요.\nESC를 누르면 취소됩니다.",
                font=("Arial", 24),
                fill="white"
            )
            
            # 사각형 객체
            rect_id = None
            
            def on_mouse_down(event):
                nonlocal start_x, start_y, is_selecting, rect_id
                start_x, start_y = event.x, event.y
                is_selecting = True
                
                # 이전 사각형 삭제
                if rect_id:
                    canvas.delete(rect_id)
                
                # 새 사각형 생성
                rect_id = canvas.create_rectangle(
                    start_x, start_y, start_x, start_y,
                    outline='red', width=2
                )
            
            def on_mouse_move(event):
                nonlocal rect_id
                if is_selecting and rect_id:
                    canvas.coords(rect_id, start_x, start_y, event.x, event.y)
            
            def on_mouse_up(event):
                nonlocal is_selecting, end_x, end_y
                end_x, end_y = event.x, event.y
                is_selecting = False
                
                # 영역 설정 완료
                if abs(end_x - start_x) > 10 and abs(end_y - start_y) > 10:
                    # 좌표 정렬 (시작점이 항상 왼쪽 위)
                    x1, y1 = min(start_x, end_x), min(start_y, end_y)
                    x2, y2 = max(start_x, end_x), max(start_y, end_y)
                    
                    self.capture_area = (x1, y1, x2, y2)
                    select_root.destroy()
                    self.root.deiconify()  # 메인 창 복원
                    self.area_label.config(text=f"선택된 영역: ({x1}, {y1}, {x2}, {y2})")
            
            def on_key(event):
                if event.keysym == 'Escape':
                    select_root.destroy()
                    self.root.deiconify()  # 메인 창 복원
            
            # 이벤트 바인딩
            canvas.bind("<ButtonPress-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            select_root.bind("<Key>", on_key)
            
            # 창이 닫힐 때
            def on_close():
                self.root.deiconify()  # 메인 창 복원
                select_root.destroy()
            
            select_root.protocol("WM_DELETE_WINDOW", on_close)
            
        except Exception as e:
            self.root.deiconify()  # 메인 창 복원
            messagebox.showerror("오류", f"영역 선택 중 오류가 발생했습니다: {e}")
    
    def start_capture(self):
        """캡처 시작"""
        if not self.capture_area:
            messagebox.showerror("오류", "캡처 영역이 선택되지 않았습니다.")
            return
        
        # Tesseract 경로 확인
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.get()
        try:
            pytesseract.get_tesseract_version()
        except:
            messagebox.showerror("오류", "Tesseract OCR을 찾을 수 없습니다. 설정을 확인하세요.")
            return
        
        # 캡처 시작
        self.is_capturing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("캡처 중...")
        
        # 캡처 스레드 시작
        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
    
    def stop_capture(self):
        """캡처 중지"""
        self.is_capturing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("캡처 중지됨")
    
    def capture_loop(self):
        """캡처 루프"""
        try:
            # PyAutoGUI 안전 기능 비활성화
            pyautogui.FAILSAFE = False
            
            while self.is_capturing:
                # 화면 캡처
                x1, y1, x2, y2 = self.capture_area
                screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
                
                # 이미지 처리 및 OCR
                self.process_captured_image(screenshot)
                
                # 간격 대기
                for i in range(self.capture_interval.get()):
                    if not self.is_capturing:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            self.is_capturing = False
            self.root.after(0, lambda: self.status_var.set(f"오류: {e}"))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: messagebox.showerror("캡처 오류", f"캡처 중 오류가 발생했습니다: {e}"))
    
    def process_captured_image(self, screenshot):
        """캡처된 이미지 처리"""
        try:
            # 이미지 전처리
            img_np = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            # 노이즈 제거
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 이진화
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR 실행
            text = pytesseract.image_to_string(thresh, lang='kor+eng')
            
            # 결과가 이전과 동일하면 처리하지 않음
            if text.strip() == self.last_processed_text.strip():
                return
            
            self.last_processed_text = text
            
            # 대화 구조 분석
            new_conversations = self.parse_conversations(text)
            
            # 새 대화가 있으면 추가
            if new_conversations:
                # 기존 대화와 중복되지 않는 새 대화만 추가
                for new_conv in new_conversations:
                    is_duplicate = False
                    for existing_conv in self.conversation_data:
                        if new_conv["role"] == existing_conv["role"] and new_conv["content"] == existing_conv["content"]:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        self.conversation_data.append(new_conv)
                
                # 대화창 업데이트
                self.update_text_display()
                
                # 미리보기 업데이트
                self.update_preview_image(img_rgb)
            
        except Exception as e:
            print(f"이미지 처리 오류: {e}")
    
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
    
    def update_text_display(self):
        """텍스트 표시 업데이트"""
        self.text_box.delete(1.0, tk.END)
        
        for conv in self.conversation_data:
            role_display = "Human" if conv["role"] == "user" else "Claude"
            self.text_box.insert(tk.END, f"{role_display}: {conv['content']}\n\n")
            
        # 스크롤을 마지막으로 이동
        self.text_box.see(tk.END)
        
        # 상태 업데이트
        self.status_var.set(f"추출된 대화: {len(self.conversation_data)}개 메시지")
    
    def update_preview_image(self, image):
        """미리보기 이미지 업데이트"""
        try:
            # PIL 이미지로 변환
            img = Image.fromarray(image)
            
            # 캔버스 크기에 맞게 조정
            canvas_width = self.preview_canvas.winfo_width()
            if canvas_width < 10:  # 초기화 단계인 경우
                canvas_width = 400
                
            # 비율 유지하며 크기 조정
            img_width, img_height = img.size
            new_width = min(img_width, canvas_width - 20)
            ratio = new_width / img_width
            new_height = int(img_height * ratio)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Tkinter 이미지로 변환
            self.preview_img = ImageTk.PhotoImage(img)
            
            # 캔버스 크기 조정
            self.preview_canvas.config(scrollregion=(0, 0, new_width, new_height))
            
            # 이미지 표시
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_img)
            
        except Exception as e:
            print(f"미리보기 업데이트 오류: {e}")
    
    def save_conversation(self):
        """대화 저장"""
        if not self.conversation_data:
            messagebox.showinfo("알림", "저장할 대화가 없습니다.")
            return
        
        self.save_conversations_to_file(self.conversation_data)
    
    def save_conversations_to_file(self, conversations):
        """대화를 파일로 저장"""
        try:
            # 출력 폴더 생성
            os.makedirs(self.output_folder.get(), exist_ok=True)
            
            # 기본 파일명 설정
            if not self.filename.get():
                self.filename.set(f"claude_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # 출력 경로 설정
            output_path = os.path.join(self.output_folder.get(), self.filename.get())
            
            # 파일 확장자 확인
            ext = os.path.splitext(output_path)[1].lower()
            if not ext:
                output_path += '.json'
                ext = '.json'
            
            # 데이터 준비
            data = {
                "conversations": conversations,
                "timestamp": datetime.now().isoformat(),
                "source": "claude_conversation_tool"
            }
            
            # 파일 형식에 따라 저장
            if ext == '.json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            elif ext == '.txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for conv in conversations:
                        role = "Human" if conv["role"] == "user" else "Claude"
                        f.write(f"{role}: {conv['content']}\n\n")
            else:
                # 기본적으로 JSON으로 저장
                output_path = os.path.splitext(output_path)[0] + '.json'
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("저장 완료", f"대화가 {output_path}에 저장되었습니다.")
            
            # 새 파일명 생성 (타임스탬프 포함)
            self.filename.set(f"claude_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
        except Exception as e:
            messagebox.showerror("저장 오류", f"대화 저장 중 오류가 발생했습니다: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            settings = {
                "tesseract_path": self.tesseract_path.get(),
                "output_folder": self.output_folder.get(),
                "capture_interval": self.capture_interval.get(),
                "filename": self.filename.get()
            }
            
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_conversation_settings.json")
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
            # Tesseract 설정 적용
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.get()
            
            # 출력 폴더 생성
            os.makedirs(self.output_folder.get(), exist_ok=True)
            
            messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
            
            # Tesseract 버전 확인
            try:
                version = pytesseract.get_tesseract_version()
                self.status_var.set(f"Tesseract OCR 버전: {version}")
            except:
                self.status_var.set("오류: Tesseract OCR을 로드할 수 없습니다.")
                
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {e}")
    
    def load_settings(self):
        """설정 불러오기"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_conversation_settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "tesseract_path" in settings:
                    self.tesseract_path.set(settings["tesseract_path"])
                    
                if "output_folder" in settings:
                    self.output_folder.set(settings["output_folder"])
                    
                if "capture_interval" in settings:
                    self.capture_interval.set(settings["capture_interval"])
                    
                if "filename" in settings:
                    self.filename.set(settings["filename"])
                    
                # 출력 폴더 생성
                os.makedirs(self.output_folder.get(), exist_ok=True)
                
                # Tesseract 설정 적용
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.get()
                
                # Tesseract 버전 확인
                try:
                    version = pytesseract.get_tesseract_version()
                    self.status_var.set(f"Tesseract OCR 버전: {version}")
                except:
                    self.status_var.set("오류: Tesseract OCR을 로드할 수 없습니다.")
                    
        except Exception as e:
            print(f"설정 불러오기 오류: {e}")
    
    def open_url(self, url):
        """URL 열기"""
        import webbrowser
        webbrowser.open(url)
    
    def on_closing(self):
        """창 닫기 이벤트 처리"""
        if self.is_capturing:
            if messagebox.askyesno("종료 확인", "캡처가 진행 중입니다. 정말 종료하시겠습니까?"):
                self.is_capturing = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    # PyAutoGUI 안전 기능 비활성화 (전체 화면 캡처를 위해)
    pyautogui.FAILSAFE = False
    
    # 메인 창 생성
    root = tk.Tk()
    app = ClaudeConversationTool(root)
    
    # 창 닫기 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 실행
    root.mainloop()


if __name__ == "__main__":
    main()
