"""
A/B 테스트 탭 컴포넌트

A/B 테스트 설정 및 결과 분석을 위한 UI 탭 컴포넌트를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
import json
import random
import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.events import subscribe, publish
from core.config import get_config
from gui.components.modules.ab_test_utils import ABTestAnalyzer, create_result_plot

logger = get_logger("gui.components.ab_test_tab")

class ABTestTab(ttk.Frame):
    """A/B 테스트 탭"""
    
    def __init__(self, parent):
        """
        A/B 테스트 탭 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="10")
        
        # 설정 로드
        self.config = get_config()
        
        # 변수 초기화
        self.test_name = tk.StringVar()
        self.test_description = tk.StringVar()
        self.variant_a_name = tk.StringVar(value="A")
        self.variant_b_name = tk.StringVar(value="B")
        self.metric_name = tk.StringVar(value="응답 품질")
        self.threshold = tk.DoubleVar(value=0.05)
        self.active_test = None
        self.results_data = None
        self.status_text = tk.StringVar(value="준비 완료")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # 데이터 디렉토리 설정
        self.data_dir = os.path.join(self.config.get("core", "data_dir", "data"), "ab_tests")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # UI 구성
        self._create_widgets()
        
        logger.info("A/B 테스트 탭 초기화됨")
    
    def _create_widgets(self):
        """UI 구성요소 생성"""
        # 메인 영역 분할 (노트북)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # === 테스트 설정 탭 ===
        self.setup_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.setup_tab, text="테스트 설정")
        self._create_setup_tab()
        
        # === 테스트 실행 탭 ===
        self.run_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.run_tab, text="테스트 실행")
        self._create_run_tab()
        
        # === 결과 분석 탭 ===
        self.results_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.results_tab, text="결과 분석")
        self._create_results_tab()
        
        # 상태 바
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _create_setup_tab(self):
        """테스트 설정 탭 UI 생성"""
        # 테스트 설정 프레임
        test_frame = ttk.LabelFrame(self.setup_tab, text="테스트 정보", padding="10")
        test_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 테스트 이름
        ttk.Label(test_frame, text="테스트 이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(test_frame, textvariable=self.test_name, width=30).grid(
            row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 테스트 설명
        ttk.Label(test_frame, text="설명:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(test_frame, textvariable=self.test_description, width=30).grid(
            row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 변형 설정 프레임
        variant_frame = ttk.LabelFrame(self.setup_tab, text="변형 설정", padding="10")
        variant_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 변형 A 설정
        ttk.Label(variant_frame, text="변형 A 이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(variant_frame, textvariable=self.variant_a_name, width=20).grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 변형 A 프롬프트
        ttk.Label(variant_frame, text="변형 A 프롬프트:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.variant_a_prompt = scrolledtext.ScrolledText(variant_frame, wrap=tk.WORD, height=5, width=40)
        self.variant_a_prompt.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 변형 B 설정
        ttk.Label(variant_frame, text="변형 B 이름:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(variant_frame, textvariable=self.variant_b_name, width=20).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 변형 B 프롬프트
        ttk.Label(variant_frame, text="변형 B 프롬프트:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.variant_b_prompt = scrolledtext.ScrolledText(variant_frame, wrap=tk.WORD, height=5, width=40)
        self.variant_b_prompt.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 지표 설정 프레임
        metric_frame = ttk.LabelFrame(self.setup_tab, text="지표 설정", padding="10")
        metric_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 지표 이름
        ttk.Label(metric_frame, text="지표 이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(metric_frame, textvariable=self.metric_name, width=20).grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 유의성 임계값
        ttk.Label(metric_frame, text="유의성 임계값:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(metric_frame, from_=0.01, to=0.1, variable=self.threshold, orient=tk.HORIZONTAL).grid(
            row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(metric_frame, textvariable=self.threshold).grid(row=1, column=2, padx=5)
        
        # 테스트 방법 선택
        self.test_method = tk.StringVar(value="manual")
        ttk.Label(metric_frame, text="테스트 방법:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Radiobutton(metric_frame, text="수동 평가", value="manual", variable=self.test_method).grid(
            row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(metric_frame, text="자동 평가", value="auto", variable=self.test_method).grid(
            row=3, column=1, sticky=tk.W, pady=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.setup_tab)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 테스트 생성 버튼
        ttk.Button(button_frame, text="테스트 생성", command=self._create_test).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="테스트 로드", command=self._load_test).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="초기화", command=self._reset_form).pack(side=tk.LEFT, padx=5)
    
    def _create_run_tab(self):
        """테스트 실행 탭 UI 생성"""
        # 활성 테스트 정보 프레임
        self.active_test_frame = ttk.LabelFrame(self.run_tab, text="활성 테스트 정보", padding="10")
        self.active_test_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 테스트 정보 표시
        self.active_test_info = scrolledtext.ScrolledText(self.active_test_frame, wrap=tk.WORD, height=5, width=50)
        self.active_test_info.pack(fill=tk.X, expand=True)
        self.active_test_info.insert(tk.END, "활성 테스트가 없습니다. 테스트 설정 탭에서 테스트를 생성하거나 로드하세요.")
        self.active_test_info.configure(state=tk.DISABLED)
        
        # 테스트 실행 프레임
        test_run_frame = ttk.LabelFrame(self.run_tab, text="테스트 실행", padding="10")
        test_run_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 입력 텍스트
        ttk.Label(test_run_frame, text="입력 텍스트:").pack(anchor=tk.W, pady=(0, 5))
        self.input_text = scrolledtext.ScrolledText(test_run_frame, wrap=tk.WORD, height=5, width=50)
        self.input_text.pack(fill=tk.X, expand=True, pady=(0, 10))
        
        # 변형 A/B 응답 프레임
        responses_frame = ttk.Frame(test_run_frame)
        responses_frame.pack(fill=tk.X, expand=True)
        
        # 변형 A 응답
        variant_a_frame = ttk.LabelFrame(responses_frame, text="변형 A 응답", padding="5")
        variant_a_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.variant_a_response = scrolledtext.ScrolledText(variant_a_frame, wrap=tk.WORD, height=8, width=30)
        self.variant_a_response.pack(fill=tk.BOTH, expand=True)
        
        # 변형 B 응답
        variant_b_frame = ttk.LabelFrame(responses_frame, text="변형 B 응답", padding="5")
        variant_b_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.variant_b_response = scrolledtext.ScrolledText(variant_b_frame, wrap=tk.WORD, height=8, width=30)
        self.variant_b_response.pack(fill=tk.BOTH, expand=True)
        
        # 버튼 프레임
        run_button_frame = ttk.Frame(test_run_frame)
        run_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 실행 및 평가 버튼
        ttk.Button(run_button_frame, text="테스트 실행", command=self._run_test).pack(side=tk.LEFT, padx=5)
        
        # 평가 프레임
        rating_frame = ttk.LabelFrame(test_run_frame, text="응답 평가", padding="5")
        rating_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 평가 스케일 (1-5)
        rating_scale_frame = ttk.Frame(rating_frame)
        rating_scale_frame.pack(fill=tk.X, pady=5)
        
        self.rating_a = tk.IntVar(value=3)
        ttk.Label(rating_scale_frame, text="변형 A 평가:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        for i in range(1, 6):
            ttk.Radiobutton(rating_scale_frame, text=str(i), value=i, variable=self.rating_a).grid(
                row=0, column=i, padx=5)
        
        self.rating_b = tk.IntVar(value=3)
        ttk.Label(rating_scale_frame, text="변형 B 평가:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        for i in range(1, 6):
            ttk.Radiobutton(rating_scale_frame, text=str(i), value=i, variable=self.rating_b).grid(
                row=1, column=i, padx=5)
        
        # 평가 제출 버튼
        ttk.Button(rating_frame, text="평가 제출", command=self._submit_rating).pack(
            anchor=tk.E, pady=(5, 0))
    
    def _create_results_tab(self):
        """결과 분석 탭 UI 생성"""
        # 결과 요약 프레임
        self.summary_frame = ttk.LabelFrame(self.results_tab, text="결과 요약", padding="10")
        self.summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 결과 요약 텍스트
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD, height=5, width=50)
        self.summary_text.pack(fill=tk.X, expand=True)
        self.summary_text.insert(tk.END, "테스트 결과가 없습니다. 테스트를 실행하거나 결과를 로드하세요.")
        self.summary_text.configure(state=tk.DISABLED)
        
        # 그래프 프레임
        self.graph_frame = ttk.LabelFrame(self.results_tab, text="결과 그래프", padding="10")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 버튼 프레임
        result_button_frame = ttk.Frame(self.results_tab)
        result_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 결과 관리 버튼
        ttk.Button(result_button_frame, text="결과 로드", command=self._load_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(result_button_frame, text="보고서 생성", command=self._generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(result_button_frame, text="데이터 내보내기", command=self._export_data).pack(side=tk.LEFT, padx=5)
    
    def refresh(self):
        """데이터 새로고침"""
        # 활성 테스트가 있으면 정보 업데이트
        if self.active_test:
            self._update_active_test_info()
        
        # 결과 데이터가 있으면 업데이트
        if self.results_data:
            self._update_results_display()
    
    # 테스트 생성 및 로드 관련 메서드들은 ab_test_core.py로 이동

    def _create_test(self):
        """A/B 테스트 생성"""
        from gui.components.modules.ab_test_core import create_test
        self.active_test = create_test(
            self.test_name.get(),
            self.test_description.get(),
            self.variant_a_name.get(),
            self.variant_a_prompt.get("1.0", tk.END),
            self.variant_b_name.get(),
            self.variant_b_prompt.get("1.0", tk.END),
            self.metric_name.get(),
            self.threshold.get(),
            self.test_method.get(),
            self.data_dir
        )
        
        if self.active_test:
            # 활성 테스트 정보 업데이트
            self._update_active_test_info()
            
            # 테스트 실행 탭으로 전환
            self.notebook.select(1)
            
            # 메시지 표시
            messagebox.showinfo("테스트 생성", f"테스트가 생성되었습니다: {self.active_test['test_name']}")
            
            # 상태 업데이트
            self.status_text.set(f"테스트 생성됨: {self.active_test['test_name']}")
    
    def _validate_test_form(self):
        """테스트 양식 유효성 검사"""
        if not self.test_name.get().strip():
            messagebox.showinfo("알림", "테스트 이름을 입력하세요.")
            return False
        
        if not self.variant_a_prompt.get("1.0", tk.END).strip():
            messagebox.showinfo("알림", "변형 A 프롬프트를 입력하세요.")
            return False
        
        if not self.variant_b_prompt.get("1.0", tk.END).strip():
            messagebox.showinfo("알림", "변형 B 프롬프트를 입력하세요.")
            return False
        
        return True
    
    def _load_test(self):
        """저장된 테스트 로드"""
        # 테스트 선택 창
        file_path = filedialog.askopenfilename(
            title="테스트 파일 선택",
            filetypes=[("JSON 파일", "*.json")],
            initialdir=self.data_dir
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # 기본 구조 확인
            if not all(key in test_data for key in ["test_id", "test_name", "variants", "metric"]):
                messagebox.showerror("오류", "유효하지 않은 테스트 파일입니다.")
                return
            
            # 활성 테스트로 설정
            self.active_test = test_data
            
            # 폼 업데이트
            self._update_form_from_test(test_data)
            
            # 활성 테스트 정보 업데이트
            self._update_active_test_info()
            
            # 메시지 표시
            messagebox.showinfo("테스트 로드", f"테스트가 로드되었습니다: {test_data['test_name']}")
            
            # 결과 데이터가 있으면 결과 탭으로 전환
            if test_data.get("results") and len(test_data["results"]) > 0:
                self.results_data = test_data
                self._update_results_display()
                self.notebook.select(2)
            else:
                # 테스트 실행 탭으로 전환
                self.notebook.select(1)
        
        except Exception as e:
            logger.error(f"테스트 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"테스트 로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def _update_form_from_test(self, test_data):
        """테스트 데이터로 폼 업데이트"""
        self.test_name.set(test_data["test_name"])
        self.test_description.set(test_data.get("description", ""))
        
        self.variant_a_name.set(test_data["variants"]["A"]["name"])
        self.variant_a_prompt.delete("1.0", tk.END)
        self.variant_a_prompt.insert(tk.END, test_data["variants"]["A"]["prompt"])
        
        self.variant_b_name.set(test_data["variants"]["B"]["name"])
        self.variant_b_prompt.delete("1.0", tk.END)
        self.variant_b_prompt.insert(tk.END, test_data["variants"]["B"]["prompt"])
        
        self.metric_name.set(test_data["metric"]["name"])
        self.threshold.set(test_data["metric"]["threshold"])
        self.test_method.set(test_data["metric"]["method"])
    
    def _reset_form(self):
        """테스트 양식 초기화"""
        self.test_name.set("")
        self.test_description.set("")
        self.variant_a_name.set("A")
        self.variant_b_name.set("B")
        self.metric_name.set("응답 품질")
        self.threshold.set(0.05)
        self.test_method.set("manual")
        
        self.variant_a_prompt.delete("1.0", tk.END)
        self.variant_b_prompt.delete("1.0", tk.END)
    
    def _update_active_test_info(self):
        """활성 테스트 정보 업데이트"""
        if not self.active_test:
            self.active_test_info.configure(state=tk.NORMAL)
            self.active_test_info.delete("1.0", tk.END)
            self.active_test_info.insert(tk.END, "활성 테스트가 없습니다. 테스트 설정 탭에서 테스트를 생성하거나 로드하세요.")
            self.active_test_info.configure(state=tk.DISABLED)
            return
        
        # 정보 텍스트 생성
        test_info = f"테스트 이름: {self.active_test['test_name']}\n"
        test_info += f"설명: {self.active_test.get('description', '')}\n"
        test_info += f"변형 A: {self.active_test['variants']['A']['name']}, 변형 B: {self.active_test['variants']['B']['name']}\n"
        test_info += f"측정 지표: {self.active_test['metric']['name']}, 임계값: {self.active_test['metric']['threshold']}\n"
        
        # 샘플 수 추가
        sample_count = len(self.active_test.get("results", []))
        test_info += f"현재 샘플 수: {sample_count}"
        
        # 정보 업데이트
        self.active_test_info.configure(state=tk.NORMAL)
        self.active_test_info.delete("1.0", tk.END)
        self.active_test_info.insert(tk.END, test_info)
        self.active_test_info.configure(state=tk.DISABLED)
    
    def _run_test(self):
        """A/B 테스트 실행"""
        # 활성 테스트 확인
        if not self.active_test:
            messagebox.showinfo("알림", "활성 테스트가 없습니다. 먼저 테스트를 생성하거나 로드하세요.")
            return
        
        # 입력 텍스트 확인
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showinfo("알림", "입력 텍스트를 입력하세요.")
            return
        
        # 상태 업데이트
        self.status_text.set("응답 생성 중...")
        self.progress_var.set(10)
        
        # 변형 A, B 순서 랜덤화
        is_randomized = random.random() > 0.5
        
        def run_variants():
            try:
                # LLM 응답 생성
                from local_llm.api import chat as llm_chat
                
                # 변형 A 응답 생성
                a_prompt = self.active_test["variants"]["A"]["prompt"]
                a_messages = [
                    {"role": "system", "content": a_prompt},
                    {"role": "user", "content": input_text}
                ]
                a_response = llm_chat(a_messages)
                
                # 진행률 업데이트
                self.master.after(0, lambda: self.progress_var.set(50))
                
                # 변형 B 응답 생성
                b_prompt = self.active_test["variants"]["B"]["prompt"]
                b_messages = [
                    {"role": "system", "content": b_prompt},
                    {"role": "user", "content": input_text}
                ]
                b_response = llm_chat(b_messages)
                
                # UI 업데이트
                self.master.after(0, lambda: self._update_responses(
                    input_text, a_response, b_response, is_randomized))
            
            except Exception as e:
                logger.error(f"테스트 실행 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_test_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=run_variants, daemon=True).start()
    
    def _update_responses(self, input_text, a_response, b_response, is_randomized):
        """응답 업데이트"""
        # 응답 표시
        if is_randomized:
            # 순서 반전
            self.variant_a_response.delete("1.0", tk.END)
            self.variant_a_response.insert(tk.END, b_response)
            
            self.variant_b_response.delete("1.0", tk.END)
            self.variant_b_response.insert(tk.END, a_response)
        else:
            # 원래 순서
            self.variant_a_response.delete("1.0", tk.END)
            self.variant_a_response.insert(tk.END, a_response)
            
            self.variant_b_response.delete("1.0", tk.END)
            self.variant_b_response.insert(tk.END, b_response)
        
        # 상태 업데이트
        self.status_text.set("응답 생성 완료")
        self.progress_var.set(100)
        
        # 자동 평가인 경우 평가 실행
        if self.active_test["metric"]["method"] == "auto":
            self._auto_evaluate(input_text, a_response, b_response, is_randomized)
    
    def _handle_test_error(self, error_msg):
        """테스트 오류 처리"""
        self.status_text.set("테스트 실패")
        self.progress_var.set(0)
        messagebox.showerror("오류", f"테스트 실행 중 오류가 발생했습니다:\n{error_msg}")
    
    def _auto_evaluate(self, input_text, a_response, b_response, is_randomized):
        """자동으로 응답 평가"""
        # 이 구현에서는 간단하게 임의의 평가 생성
        # 실제 구현에서는 응답 품질 평가 모델 사용
        a_rating = random.uniform(3.0, 5.0)
        b_rating = random.uniform(3.0, 5.0)
        
        # 평가 결과 제출
        self._save_result(input_text, a_response, b_response, 
                         int(a_rating), int(b_rating), is_randomized)
    
    def _submit_rating(self):
        """평가 제출"""
        # 입력 및 응답 확인
        input_text = self.input_text.get("1.0", tk.END).strip()
        a_response = self.variant_a_response.get("1.0", tk.END).strip()
        b_response = self.variant_b_response.get("1.0", tk.END).strip()
        
        if not input_text or not a_response or not b_response:
            messagebox.showinfo("알림", "입력 및 응답을 먼저 생성해야 합니다.")
            return
        
        # 평가 저장
        self._save_result(input_text, a_response, b_response, 
                         self.rating_a.get(), self.rating_b.get())
    
    def _save_result(self, input_text, a_response, b_response, a_rating, b_rating, is_randomized=False):
        """결과 저장"""
        # 활성 테스트 확인
        if not self.active_test:
            return
        
        # 평가 결과 생성
        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "input": input_text,
            "variants": {
                "A": {
                    "response": a_response if not is_randomized else b_response,
                    "rating": a_rating if not is_randomized else b_rating
                },
                "B": {
                    "response": b_response if not is_randomized else a_response,
                    "rating": b_rating if not is_randomized else a_rating
                }
            },
            "randomized": is_randomized
        }
        
        # 결과 추가
        if "results" not in self.active_test:
            self.active_test["results"] = []
        
        self.active_test["results"].append(result)
        
        # 결과 분석 및 저장
        self._analyze_and_save_results()
        
        # 결과 화면으로 전환
        self.notebook.select(2)
    
    def _analyze_and_save_results(self):
        """결과 분석 및 저장"""
        from gui.components.modules.ab_test_utils import analyze_test_results
        
        # 결과 분석
        try:
            self.active_test["summary"] = analyze_test_results(self.active_test)
            
            # 활성 테스트 정보 업데이트
            self._update_active_test_info()
            
            # 결과 데이터 설정
            self.results_data = self.active_test
            
            # 결과 표시 업데이트
            self._update_results_display()
            
            # 테스트 저장
            test_id = self.active_test["test_id"]
            file_path = os.path.join(self.data_dir, f"{test_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.active_test, f, ensure_ascii=False, indent=2)
            
            # 상태 업데이트
            self.status_text.set(f"결과 저장됨: {len(self.active_test['results'])}개 샘플")
            
        except Exception as e:
            logger.error(f"결과 분석 및 저장 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"결과 분석 및 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def _update_results_display(self):
        """결과 표시 업데이트"""
        if not self.results_data:
            return
        
        # 요약 텍스트 생성
        summary = self.results_data.get("summary", {})
        
        summary_text = f"테스트: {self.results_data['test_name']}\n"
        summary_text += f"총 샘플 수: {summary.get('total_samples', 0)}\n"
        summary_text += f"변형 A 평균 점수: {summary.get('variant_a_avg', 0):.2f}\n"
        summary_text += f"변형 B 평균 점수: {summary.get('variant_b_avg', 0):.2f}\n"
        
        if summary.get("p_value") is not None:
            summary_text += f"p-값: {summary.get('p_value', 1.0):.4f}\n"
            
            if summary.get("significant", False):
                if summary.get("variant_a_avg", 0) > summary.get("variant_b_avg", 0):
                    winner = f"{self.results_data['variants']['A']['name']} (A)"
                else:
                    winner = f"{self.results_data['variants']['B']['name']} (B)"
                
                summary_text += f"결과: 통계적으로 유의미한 차이가 있음 (승자: {winner})"
            else:
                summary_text += "결과: 통계적으로 유의미한 차이가 없음"
        
        # 요약 업데이트
        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.configure(state=tk.DISABLED)
        
        # 그래프 업데이트
        from gui.components.modules.ab_test_utils import create_result_plot
        
        # 기존 위젯 제거
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # 새 그래프 생성
        figure = create_result_plot(self.results_data)
        if figure:
            # 캔버스 생성
            canvas = FigureCanvasTkAgg(figure, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _load_results(self):
        """결과 로드"""
        # 결과 파일 선택
        file_path = filedialog.askopenfilename(
            title="결과 파일 선택",
            filetypes=[("JSON 파일", "*.json")],
            initialdir=self.data_dir
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # 활성 테스트로 설정
            self.active_test = test_data
            
            # 결과 데이터 설정
            self.results_data = test_data
            
            # 활성 테스트 정보 업데이트
            self._update_active_test_info()
            
            # 결과 표시 업데이트
            self._update_results_display()
            
            # 메시지 표시
            messagebox.showinfo("결과 로드", "결과가 로드되었습니다.")
            
        except Exception as e:
            logger.error(f"결과 로드 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"결과 로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def _generate_report(self):
        """보고서 생성"""
        if not self.results_data:
            messagebox.showinfo("알림", "결과 데이터가 없습니다.")
            return
        
        # 저장 경로 선택
        save_path = filedialog.asksaveasfilename(
            title="보고서 저장",
            filetypes=[("Markdown", "*.md"), ("텍스트", "*.txt")],
            defaultextension=".md",
            initialdir=self.data_dir,
            initialfile=f"{self.results_data['test_name']}_report.md"
        )
        
        if not save_path:
            return
        
        try:
            # 보고서 생성
            from gui.components.modules.ab_test_utils import generate_report
            
            report_text = generate_report(self.results_data)
            
            # 파일 저장
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            # 메시지 표시
            messagebox.showinfo("보고서 생성", f"보고서가 저장되었습니다:\n{save_path}")
            
        except Exception as e:
            logger.error(f"보고서 생성 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"보고서 생성 중 오류가 발생했습니다:\n{str(e)}")
    
    def _export_data(self):
        """데이터 내보내기"""
        if not self.results_data:
            messagebox.showinfo("알림", "결과 데이터가 없습니다.")
            return
        
        # 저장 경로 선택
        save_path = filedialog.asksaveasfilename(
            title="데이터 내보내기",
            filetypes=[("JSON 파일", "*.json"), ("CSV 파일", "*.csv")],
            defaultextension=".json",
            initialdir=self.data_dir,
            initialfile=f"{self.results_data['test_name']}_data"
        )
        
        if not save_path:
            return
        
        try:
            ext = os.path.splitext(save_path)[1].lower()
            
            if ext == ".json":
                # JSON 형식으로 저장
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(self.results_data, f, ensure_ascii=False, indent=2)
            
            elif ext == ".csv":
                # CSV 형식으로 저장
                import csv
                
                with open(save_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    
                    # 헤더 작성
                    writer.writerow(["timestamp", "input", "variant_a_response", "variant_a_rating", 
                                    "variant_b_response", "variant_b_rating", "randomized"])
                    
                    # 데이터 작성
                    for result in self.results_data.get("results", []):
                        timestamp = result.get("timestamp", "")
                        input_text = result.get("input", "")
                        a_response = result.get("variants", {}).get("A", {}).get("response", "")
                        a_rating = result.get("variants", {}).get("A", {}).get("rating", 0)
                        b_response = result.get("variants", {}).get("B", {}).get("response", "")
                        b_rating = result.get("variants", {}).get("B", {}).get("rating", 0)
                        randomized = result.get("randomized", False)
                        
                        writer.writerow([timestamp, input_text, a_response, a_rating, 
                                       b_response, b_rating, randomized])
            
            # 메시지 표시
            messagebox.showinfo("데이터 내보내기", f"데이터가 저장되었습니다:\n{save_path}")
            
        except Exception as e:
            logger.error(f"데이터 내보내기 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"데이터 내보내기 중 오류가 발생했습니다:\n{str(e)}")
