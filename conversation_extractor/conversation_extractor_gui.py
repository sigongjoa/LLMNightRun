import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from conversation_extractor import ConversationExtractor
import threading
import json
from datetime import datetime

class ConversationExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude 대화 추출기")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Tesseract 경로
        self.tesseract_path = tk.StringVar()
        self.tesseract_path.set(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        
        # 이미지 파일 경로
        self.image_path = tk.StringVar()
        
        # 출력 파일 경로
        self.output_path = tk.StringVar()
        
        # 가져올 파일 경로
        self.import_path = tk.StringVar()
        
        # OCR 언어
        self.ocr_lang = tk.StringVar()
        self.ocr_lang.set("kor+eng")
        
        # 대화 추출기 초기화
        self.extractor = None
        
        # UI 구성
        self.create_widgets()
        
        # 추출기 초기화
        self.initialize_extractor()
        
    def create_widgets(self):
        """UI 위젯 생성"""
        # 노트북(탭) 생성
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 추출 탭
        extract_frame = ttk.Frame(notebook)
        notebook.add(extract_frame, text="이미지에서 추출")
        
        # 가져오기 탭
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="파일에서 가져오기")
        
        # 설정 탭
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="설정")
        
        # === 추출 탭 구성 ===
        # 이미지 파일 선택
        ttk.Label(extract_frame, text="이미지 파일:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(extract_frame, textvariable=self.image_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(extract_frame, text="찾아보기", command=self.browse_image).grid(row=0, column=2, padx=5, pady=5)
        
        # 출력 파일 선택
        ttk.Label(extract_frame, text="출력 파일:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(extract_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(extract_frame, text="찾아보기", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # 추출 버튼
        ttk.Button(extract_frame, text="대화 추출", command=self.extract_conversation).grid(row=2, column=1, padx=5, pady=10)
        
        # 미리보기 영역
        ttk.Label(extract_frame, text="추출된 대화 미리보기:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.extract_preview = tk.Text(extract_frame, width=80, height=20)
        self.extract_preview.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        # 스크롤바 추가
        extract_scrollbar = ttk.Scrollbar(extract_frame, orient=tk.VERTICAL, command=self.extract_preview.yview)
        extract_scrollbar.grid(row=4, column=3, sticky=tk.NS)
        self.extract_preview.config(yscrollcommand=extract_scrollbar.set)
        
        # === 가져오기 탭 구성 ===
        # 가져올 파일 선택
        ttk.Label(import_frame, text="가져올 파일:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(import_frame, textvariable=self.import_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(import_frame, text="찾아보기", command=self.browse_import).grid(row=0, column=2, padx=5, pady=5)
        
        # 출력 파일 선택
        ttk.Label(import_frame, text="출력 파일:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(import_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(import_frame, text="찾아보기", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # 가져오기 버튼
        ttk.Button(import_frame, text="대화 가져오기", command=self.import_conversation).grid(row=2, column=1, padx=5, pady=10)
        
        # 미리보기 영역
        ttk.Label(import_frame, text="가져온 대화 미리보기:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.import_preview = tk.Text(import_frame, width=80, height=20)
        self.import_preview.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        # 스크롤바 추가
        import_scrollbar = ttk.Scrollbar(import_frame, orient=tk.VERTICAL, command=self.import_preview.yview)
        import_scrollbar.grid(row=4, column=3, sticky=tk.NS)
        self.import_preview.config(yscrollcommand=import_scrollbar.set)
        
        # === 설정 탭 구성 ===
        # Tesseract 경로 설정
        ttk.Label(settings_frame, text="Tesseract 경로:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.tesseract_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="찾아보기", command=self.browse_tesseract).grid(row=0, column=2, padx=5, pady=5)
        
        # OCR 언어 설정
        ttk.Label(settings_frame, text="OCR 언어:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Combobox(settings_frame, textvariable=self.ocr_lang, values=["kor", "eng", "kor+eng"]).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 저장 버튼
        ttk.Button(settings_frame, text="설정 저장", command=self.save_settings).grid(row=2, column=1, padx=5, pady=10)
        
        # Tesseract 다운로드 링크
        ttk.Label(settings_frame, text="Tesseract OCR이 없으신가요?").grid(row=3, column=0, sticky=tk.W, padx=5, pady=20)
        download_link = ttk.Label(settings_frame, text="여기서 다운로드", foreground="blue", cursor="hand2")
        download_link.grid(row=3, column=1, sticky=tk.W, padx=5, pady=20)
        download_link.bind("<Button-1>", lambda e: self.open_url("https://github.com/UB-Mannheim/tesseract/wiki"))
        
        # 프레임 크기 조정
        for frame in [extract_frame, import_frame, settings_frame]:
            frame.columnconfigure(1, weight=1)
            frame.rowconfigure(4, weight=1)
        
    def initialize_extractor(self):
        """대화 추출기 초기화"""
        try:
            self.extractor = ConversationExtractor(self.tesseract_path.get())
        except Exception as e:
            messagebox.showerror("초기화 오류", f"추출기 초기화 중 오류가 발생했습니다: {e}")
    
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
    
    def browse_output(self):
        """출력 파일 찾아보기"""
        file_path = filedialog.asksaveasfilename(
            title="출력 파일 선택",
            filetypes=[
                ("JSON 파일", "*.json"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ],
            defaultextension=".json"
        )
        if file_path:
            self.output_path.set(file_path)
    
    def browse_import(self):
        """가져올 파일 찾아보기"""
        file_path = filedialog.askopenfilename(
            title="가져올 파일 선택",
            filetypes=[
                ("JSON 파일", "*.json"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.import_path.set(file_path)
    
    def browse_tesseract(self):
        """Tesseract 실행 파일 찾아보기"""
        file_path = filedialog.askopenfilename(
            title="Tesseract 실행 파일 선택",
            filetypes=[
                ("실행 파일", "*.exe"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.tesseract_path.set(file_path)
    
    def extract_conversation(self):
        """이미지에서 대화 추출"""
        # 입력 검증
        if not self.image_path.get():
            messagebox.showerror("입력 오류", "이미지 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.image_path.get()):
            messagebox.showerror("파일 오류", "선택한 이미지 파일이 존재하지 않습니다.")
            return
        
        # 로딩 표시
        self.extract_preview.delete(1.0, tk.END)
        self.extract_preview.insert(tk.END, "대화를 추출하는 중입니다. 잠시만 기다려주세요...")
        self.root.update()
        
        # 백그라운드에서 실행
        def run_extraction():
            try:
                # 대화 추출기 재초기화
                if not self.extractor:
                    self.initialize_extractor()
                
                # 대화 추출
                conversations = self.extractor.extract_conversations_from_image(
                    self.image_path.get(),
                    self.output_path.get() if self.output_path.get() else None
                )
                
                # 결과 표시
                self.extract_preview.delete(1.0, tk.END)
                if conversations:
                    for i, conv in enumerate(conversations):
                        role = "Human" if conv["role"] == "user" else "Claude"
                        self.extract_preview.insert(tk.END, f"{role}: {conv['content']}\n\n")
                else:
                    self.extract_preview.insert(tk.END, "추출된 대화가 없습니다.")
                
                # 성공 메시지
                if self.output_path.get():
                    messagebox.showinfo("추출 완료", f"대화를 성공적으로 추출하여 {self.output_path.get()}에 저장했습니다.")
                else:
                    messagebox.showinfo("추출 완료", "대화를 성공적으로 추출했습니다.")
                    
            except Exception as e:
                # 오류 메시지
                self.extract_preview.delete(1.0, tk.END)
                self.extract_preview.insert(tk.END, f"오류 발생: {e}")
                messagebox.showerror("추출 오류", f"대화 추출 중 오류가 발생했습니다: {e}")
        
        # 스레드 시작
        threading.Thread(target=run_extraction).start()
    
    def import_conversation(self):
        """파일에서 대화 가져오기"""
        # 입력 검증
        if not self.import_path.get():
            messagebox.showerror("입력 오류", "가져올 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.import_path.get()):
            messagebox.showerror("파일 오류", "선택한 파일이 존재하지 않습니다.")
            return
        
        try:
            # 대화 추출기 재초기화
            if not self.extractor:
                self.initialize_extractor()
            
            # 대화 가져오기
            conversations = self.extractor.import_conversation(self.import_path.get())
            
            # 결과 표시
            self.import_preview.delete(1.0, tk.END)
            if conversations:
                for i, conv in enumerate(conversations):
                    role = "Human" if conv["role"] == "user" else "Claude"
                    self.import_preview.insert(tk.END, f"{role}: {conv['content']}\n\n")
                
                # 출력 파일이 지정된 경우 저장
                if self.output_path.get():
                    self.extractor.generate_conversation_file(conversations, self.output_path.get())
                    messagebox.showinfo("가져오기 완료", f"대화를 {self.output_path.get()}에 저장했습니다.")
                else:
                    messagebox.showinfo("가져오기 완료", "대화를 성공적으로 가져왔습니다.")
            else:
                self.import_preview.insert(tk.END, "가져온 대화가 없습니다.")
                messagebox.showinfo("가져오기", "가져온 대화가 없습니다.")
                
        except Exception as e:
            # 오류 메시지
            self.import_preview.delete(1.0, tk.END)
            self.import_preview.insert(tk.END, f"오류 발생: {e}")
            messagebox.showerror("가져오기 오류", f"대화 가져오기 중 오류가 발생했습니다: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 설정 파일 저장
            settings = {
                "tesseract_path": self.tesseract_path.get(),
                "ocr_lang": self.ocr_lang.get(),
                "last_updated": datetime.now().isoformat()
            }
            
            settings_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # 추출기 재초기화
            self.initialize_extractor()
            
            messagebox.showinfo("설정 저장", "설정이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            messagebox.showerror("설정 저장 오류", f"설정 저장 중 오류가 발생했습니다: {e}")
    
    def load_settings(self):
        """설정 불러오기"""
        try:
            settings_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "tesseract_path" in settings:
                    self.tesseract_path.set(settings["tesseract_path"])
                
                if "ocr_lang" in settings:
                    self.ocr_lang.set(settings["ocr_lang"])
        except Exception as e:
            print(f"설정 불러오기 오류: {e}")
    
    def open_url(self, url):
        """URL 열기"""
        import webbrowser
        webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    app = ConversationExtractorGUI(root)
    app.load_settings()  # 설정 불러오기
    root.mainloop()
