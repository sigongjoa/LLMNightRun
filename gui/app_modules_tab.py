#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
모듈 통합 탭 인터페이스

각 모듈 UI 탭을 통합하는 노트북 인터페이스를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

from core.logging import get_logger
from gui.components.modules.arxiv_tab import ArxivTab
from gui.components.modules.github_ai_setup_tab import GitHubAISetupTab
from gui.components.modules.github_docs_tab import GitHubDocsTab
# 추가 모듈 탭 컴포넌트 임포트
from gui.components.modules.vector_db_tab import VectorDBTab
from gui.components.modules.ab_test_tab import ABTestTab

logger = get_logger("gui.modules_tab")

class ModulesTabInterface(ttk.Frame):
    """모듈 통합 탭 인터페이스"""
    
    def __init__(self, parent):
        """
        모듈 통합 탭 인터페이스 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="5")
        
        # 노트북 인터페이스 생성
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 탭 컴포넌트 초기화
        self._initialize_tabs()
        
        # 이벤트 바인딩
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        logger.info("모듈 통합 탭 인터페이스 초기화됨")
    
    def _initialize_tabs(self):
        """탭 컴포넌트 초기화"""
        # 모듈 탭 컴포넌트
        self.tab_components = {}
        
        # GitHub 문서 자동 생성 탭
        self.tab_components["github_docs"] = GitHubDocsTab(self.notebook)
        self.notebook.add(self.tab_components["github_docs"], text="GitHub 문서 생성")
        
        # GitHub AI 설정 탭
        self.tab_components["github_ai_setup"] = GitHubAISetupTab(self.notebook)
        self.notebook.add(self.tab_components["github_ai_setup"], text="GitHub AI 설정")
        
        # Arxiv 논문 탭
        self.tab_components["arxiv"] = ArxivTab(self.notebook)
        self.notebook.add(self.tab_components["arxiv"], text="Arxiv 논문")
        
        # 벡터 DB 검색 탭
        self.tab_components["vector_db"] = VectorDBTab(self.notebook)
        self.notebook.add(self.tab_components["vector_db"], text="벡터 검색")
        
        # A/B 테스트 탭
        self.tab_components["ab_test"] = ABTestTab(self.notebook)
        self.notebook.add(self.tab_components["ab_test"], text="A/B 테스트")
        
        # TODO: 추가 모듈 탭 구현 및 통합
    
    def _on_tab_changed(self, event):
        """탭 변경 이벤트 처리"""
        current_tab = self.notebook.select()
        tab_id = self.notebook.index(current_tab)
        
        # 현재 선택된 탭 컴포넌트 가져오기
        tab_names = list(self.tab_components.keys())
        if tab_id < len(tab_names):
            current_tab_name = tab_names[tab_id]
            current_component = self.tab_components[current_tab_name]
            
            # 탭 새로고침 메서드 호출 (있는 경우)
            if hasattr(current_component, 'refresh') and callable(current_component.refresh):
                current_component.refresh()
    
    def refresh_all(self):
        """모든 탭 컴포넌트 새로고침"""
        for component in self.tab_components.values():
            if hasattr(component, 'refresh') and callable(component.refresh):
                component.refresh()
