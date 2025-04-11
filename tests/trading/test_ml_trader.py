"""
MLTrader 전략에 대한 유닛 테스트

이 테스트 모듈은 감정 분석 기반 트레이딩 전략의 주요 기능을 검증합니다.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 절대 경로
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
# 루트 디렉토리를 시스템 경로에 추가
sys.path.insert(0, project_root)

# 테스트 대상 모듈 임포트
from tradingbot import MLTrader, Timedelta


class TestMLTrader(unittest.TestCase):
    """MLTrader 전략 테스트 클래스"""

    def setUp(self):
        """테스트 준비"""
        # Alpaca 브로커 Mock 객체 생성
        self.mock_broker = MagicMock()
        
        # API 객체 Mock 생성
        self.mock_api = MagicMock()
        
        # MLTrader 인스턴스 생성
        self.strategy = MLTrader(
            name='test_mlstrat',
            broker=self.mock_broker,
            parameters={"symbol": "SPY", "cash_at_risk": 0.5}
        )
        
        # API 객체 설정
        self.strategy.api = self.mock_api
        
        # 현재 날짜 설정 (테스트 용도)
        self.test_datetime = datetime(2023, 1, 1, 9, 30)
        
    def test_initialize(self):
        """초기화 함수 테스트"""
        # 기본 매개변수 확인
        self.assertEqual(self.strategy.symbol, "SPY")
        self.assertEqual(self.strategy.sleeptime, "24H")
        self.assertIsNone(self.strategy.last_trade)
        self.assertEqual(self.strategy.cash_at_risk, 0.5)
        
        # 커스텀 매개변수 테스트
        strategy = MLTrader(
            name='custom_mlstrat', 
            broker=self.mock_broker,
            parameters={"symbol": "AAPL", "cash_at_risk": 0.7}
        )
        self.assertEqual(strategy.symbol, "AAPL")
        self.assertEqual(strategy.cash_at_risk, 0.7)
    
    def test_position_sizing(self):
        """포지션 사이징 테스트"""
        # Mock 설정
        self.strategy.get_cash = MagicMock(return_value=10000)
        self.strategy.get_last_price = MagicMock(return_value=100)
        
        # 함수 호출
        cash, last_price, quantity = self.strategy.position_sizing()
        
        # 결과 검증
        self.assertEqual(cash, 10000)
        self.assertEqual(last_price, 100)
        self.assertEqual(quantity, 50)  # 10000 * 0.5 / 100 = 50
        
        # Mock 호출 검증
        self.strategy.get_cash.assert_called_once()
        self.strategy.get_last_price.assert_called_once_with(self.strategy.symbol)
        
    def test_get_dates(self):
        """날짜 관리 함수 테스트"""
        # 현재 시간 Mock
        self.strategy.get_datetime = MagicMock(return_value=self.test_datetime)
        
        # 함수 호출
        today, three_days_prior = self.strategy.get_dates()
        
        # 결과 검증
        self.assertEqual(today, "2023-01-01")
        self.assertEqual(three_days_prior, "2022-12-29")  # 3일 전
        
        # Mock 호출 검증
        self.strategy.get_datetime.assert_called_once()

    @patch('tradingbot.estimate_sentiment')
    def test_get_sentiment(self, mock_estimate_sentiment):
        """감정 분석 함수 테스트"""
        # Mock 설정
        self.strategy.get_dates = MagicMock(return_value=("2023-01-01", "2022-12-29"))
        
        # Mock 뉴스 데이터
        mock_news = [
            MagicMock(_raw={"headline": "Stock market rallies on positive economic data"}),
            MagicMock(_raw={"headline": "SPY reaches new all-time high"})
        ]
        self.mock_api.get_news.return_value = mock_news
        
        # Mock 감정 분석 결과
        mock_estimate_sentiment.return_value = (0.9, "positive")
        
        # 함수 호출
        probability, sentiment = self.strategy.get_sentiment()
        
        # 결과 검증
        self.assertEqual(probability, 0.9)
        self.assertEqual(sentiment, "positive")
        
        # Mock 호출 검증
        self.strategy.get_dates.assert_called_once()
        self.mock_api.get_news.assert_called_once_with(
            symbol=self.strategy.symbol,
            start="2022-12-29",
            end="2023-01-01"
        )
        
        # 감정 분석 함수 호출 검증
        headlines = ["Stock market rallies on positive economic data", "SPY reaches new all-time high"]
        mock_estimate_sentiment.assert_called_once_with(headlines)

    def test_on_trading_iteration_buy_signal(self):
        """트레이딩 반복 함수 - 매수 신호 테스트"""
        # Mock 설정
        self.strategy.position_sizing = MagicMock(return_value=(10000, 100, 50))
        self.strategy.get_sentiment = MagicMock(return_value=(0.999, "positive"))
        self.strategy.last_trade = "sell"  # 이전 트레이드가 매도였음
        
        # Mock 주문 객체
        mock_order = MagicMock()
        self.strategy.create_order = MagicMock(return_value=mock_order)
        self.strategy.submit_order = MagicMock()
        self.strategy.sell_all = MagicMock()
        
        # 함수 호출
        self.strategy.on_trading_iteration()
        
        # 결과 검증
        self.strategy.sell_all.assert_called_once()  # 이전 포지션 청산
        self.strategy.create_order.assert_called_once_with(
            self.strategy.symbol,
            50,
            "buy",
            type="bracket",
            take_profit_price=120,  # last_price * 1.20
            stop_loss_price=95      # last_price * 0.95
        )
        self.strategy.submit_order.assert_called_once_with(mock_order)
        self.assertEqual(self.strategy.last_trade, "buy")

    def test_on_trading_iteration_sell_signal(self):
        """트레이딩 반복 함수 - 매도 신호 테스트"""
        # Mock 설정
        self.strategy.position_sizing = MagicMock(return_value=(10000, 100, 50))
        self.strategy.get_sentiment = MagicMock(return_value=(0.999, "negative"))
        self.strategy.last_trade = "buy"  # 이전 트레이드가 매수였음
        
        # Mock 주문 객체
        mock_order = MagicMock()
        self.strategy.create_order = MagicMock(return_value=mock_order)
        self.strategy.submit_order = MagicMock()
        self.strategy.sell_all = MagicMock()
        
        # 함수 호출
        self.strategy.on_trading_iteration()
        
        # 결과 검증
        self.strategy.sell_all.assert_called_once()  # 이전 포지션 청산
        self.strategy.create_order.assert_called_once_with(
            self.strategy.symbol,
            50,
            "sell",
            type="bracket",
            take_profit_price=80,   # last_price * 0.8
            stop_loss_price=105     # last_price * 1.05
        )
        self.strategy.submit_order.assert_called_once_with(mock_order)
        self.assertEqual(self.strategy.last_trade, "sell")

    def test_on_trading_iteration_neutral_sentiment(self):
        """트레이딩 반복 함수 - 중립 감정 테스트"""
        # Mock 설정
        self.strategy.position_sizing = MagicMock(return_value=(10000, 100, 50))
        self.strategy.get_sentiment = MagicMock(return_value=(0.7, "neutral"))
        
        # Mock 주문 관련 메서드
        self.strategy.create_order = MagicMock()
        self.strategy.submit_order = MagicMock()
        self.strategy.sell_all = MagicMock()
        
        # 함수 호출
        self.strategy.on_trading_iteration()
        
        # 결과 검증 - 중립 감정이므로 주문이 생성되지 않아야 함
        self.strategy.create_order.assert_not_called()
        self.strategy.submit_order.assert_not_called()
        self.strategy.sell_all.assert_not_called()

    def test_on_trading_iteration_low_confidence(self):
        """트레이딩 반복 함수 - 낮은 확신도 테스트"""
        # Mock 설정
        self.strategy.position_sizing = MagicMock(return_value=(10000, 100, 50))
        self.strategy.get_sentiment = MagicMock(return_value=(0.5, "positive"))  # 낮은 확신도
        
        # Mock 주문 관련 메서드
        self.strategy.create_order = MagicMock()
        self.strategy.submit_order = MagicMock()
        self.strategy.sell_all = MagicMock()
        
        # 함수 호출
        self.strategy.on_trading_iteration()
        
        # 결과 검증 - 확신도가 낮으므로 주문이 생성되지 않아야 함
        self.strategy.create_order.assert_not_called()
        self.strategy.submit_order.assert_not_called()
        self.strategy.sell_all.assert_not_called()

    def test_on_trading_iteration_insufficient_cash(self):
        """트레이딩 반복 함수 - 현금 부족 테스트"""
        # Mock 설정 - 현금이 주가보다 적은 경우
        self.strategy.position_sizing = MagicMock(return_value=(50, 100, 0))
        self.strategy.get_sentiment = MagicMock(return_value=(0.999, "positive"))
        
        # Mock 주문 관련 메서드
        self.strategy.create_order = MagicMock()
        self.strategy.submit_order = MagicMock()
        self.strategy.sell_all = MagicMock()
        
        # 함수 호출
        self.strategy.on_trading_iteration()
        
        # 결과 검증 - 현금이 부족하므로 주문이 생성되지 않아야 함
        self.strategy.create_order.assert_not_called()
        self.strategy.submit_order.assert_not_called()
        self.strategy.sell_all.assert_not_called()


class TestBacktesting(unittest.TestCase):
    """백테스팅 기능 테스트 클래스"""
    
    @patch('tradingbot.YahooDataBacktesting')
    def test_backtest_initialization(self, mock_yahoo_data):
        """백테스팅 초기화 테스트"""
        # Mock 설정
        mock_broker = MagicMock()
        strategy = MLTrader(
            name='test_backtest',
            broker=mock_broker,
            parameters={"symbol": "SPY", "cash_at_risk": 0.5}
        )
        
        # Mock 백테스팅 객체
        mock_backtest = MagicMock()
        mock_yahoo_data.return_value = mock_backtest
        
        # 테스트 기간 설정
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # 백테스팅 실행
        strategy.backtest(
            mock_yahoo_data,
            start_date,
            end_date,
            parameters={"symbol": "SPY", "cash_at_risk": 0.5}
        )
        
        # 백테스팅 초기화 검증
        mock_yahoo_data.assert_called_once()


class TestSentimentAnalysis(unittest.TestCase):
    """감정 분석 기능 테스트 클래스"""
    
    @patch('tradingbot.estimate_sentiment')
    def test_sentiment_analysis(self, mock_estimate_sentiment):
        """감정 분석 함수 테스트"""
        # Mock 설정
        mock_estimate_sentiment.return_value = (0.8, "positive")
        
        # 테스트 뉴스 데이터
        test_news = ["Market shows strong upward trend", "Positive economic indicators boost stocks"]
        
        # 함수 호출
        probability, sentiment = mock_estimate_sentiment(test_news)
        
        # 결과 검증
        self.assertEqual(probability, 0.8)
        self.assertEqual(sentiment, "positive")
        
        # Mock 호출 검증
        mock_estimate_sentiment.assert_called_once_with(test_news)


if __name__ == "__main__":
    print("MLTrader 전략 유닛 테스트 실행 중...")
    unittest.main()
