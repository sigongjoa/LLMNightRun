"""
FinBERT 감정 분석 유틸리티 테스트

이 테스트 모듈은 FinBERT 기반 감정 분석 기능을 검증합니다.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import torch
import numpy as np

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 절대 경로
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
# 루트 디렉토리를 시스템 경로에 추가
sys.path.insert(0, project_root)

# 테스트 대상 모듈 임포트
from finbert_utils import estimate_sentiment, tokenizer, model, labels


class TestFinBERTUtils(unittest.TestCase):
    """FinBERT 감정 분석 유틸리티 테스트 클래스"""

    def setUp(self):
        """테스트 준비"""
        # 테스트 뉴스 텍스트
        self.positive_news = "markets responded positively to the earnings report"
        self.negative_news = "markets responded negatively to the news"
        self.neutral_news = "markets were unchanged today"
        
        # 여러 뉴스 항목 리스트
        self.news_list = [
            "markets responded positively to the earnings report",
            "traders were displeased with the Fed's decision"
        ]
        
        # 빈 뉴스 케이스
        self.empty_news = []
        self.none_news = None

    @patch('finbert_utils.tokenizer')
    @patch('finbert_utils.model')
    @patch('torch.nn.functional.softmax')
    @patch('torch.argmax')
    def test_estimate_sentiment_positive(self, mock_argmax, mock_softmax, mock_model, mock_tokenizer):
        """긍정적 감정 분석 테스트"""
        # Mock 설정
        mock_tokens = {"input_ids": torch.tensor([[1, 2, 3]]), "attention_mask": torch.tensor([[1, 1, 1]])}
        mock_tokenizer.return_value = mock_tokens
        
        mock_logits = torch.tensor([[0.1, 0.2, 0.7]])
        mock_model.return_value = {"logits": mock_logits}
        
        mock_sum_result = torch.tensor([0.1, 0.2, 0.7])
        mock_softmax_result = torch.tensor([0.1, 0.2, 0.7])
        mock_softmax.return_value = mock_softmax_result
        
        # argmax가 0을 반환하도록 설정 (positive 인덱스)
        mock_argmax.return_value = torch.tensor(0)
        
        # 함수 호출
        probability, sentiment = estimate_sentiment([self.positive_news])
        
        # 결과 검증
        self.assertEqual(sentiment, "positive")
        
        # Mock 호출 검증
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()
        mock_softmax.assert_called_once()
        mock_argmax.assert_called()

    @patch('finbert_utils.tokenizer')
    @patch('finbert_utils.model')
    @patch('torch.nn.functional.softmax')
    @patch('torch.argmax')
    def test_estimate_sentiment_negative(self, mock_argmax, mock_softmax, mock_model, mock_tokenizer):
        """부정적 감정 분석 테스트"""
        # Mock 설정
        mock_tokens = {"input_ids": torch.tensor([[1, 2, 3]]), "attention_mask": torch.tensor([[1, 1, 1]])}
        mock_tokenizer.return_value = mock_tokens
        
        mock_logits = torch.tensor([[0.7, 0.2, 0.1]])
        mock_model.return_value = {"logits": mock_logits}
        
        mock_sum_result = torch.tensor([0.7, 0.2, 0.1])
        mock_softmax_result = torch.tensor([0.7, 0.2, 0.1])
        mock_softmax.return_value = mock_softmax_result
        
        # argmax가 1을 반환하도록 설정 (negative 인덱스)
        mock_argmax.return_value = torch.tensor(1)
        
        # 함수 호출
        probability, sentiment = estimate_sentiment([self.negative_news])
        
        # 결과 검증
        self.assertEqual(sentiment, "negative")
        
        # Mock 호출 검증
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()
        mock_softmax.assert_called_once()
        mock_argmax.assert_called()

    @patch('finbert_utils.tokenizer')
    @patch('finbert_utils.model')
    @patch('torch.nn.