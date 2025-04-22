"""
A/B 테스트 유틸리티

A/B 테스트 분석 및 시각화를 위한 유틸리티 함수를 제공합니다.
"""

import json
import datetime
import random
import math
from typing import Dict, List, Any, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # GUI 없이 사용 가능하도록 설정

from core.logging import get_logger

logger = get_logger("gui.components.ab_test_utils")

class ABTestAnalyzer:
    """A/B 테스트 분석기"""
    
    def __init__(self, test_data: Dict[str, Any]):
        """
        A/B 테스트 분석기 초기화
        
        Args:
            test_data: 테스트 데이터 딕셔너리
        """
        self.test_data = test_data
        self.results = test_data.get("results", [])
    
    def get_ratings(self) -> Tuple[List[float], List[float]]:
        """
        변형 A와 B의 평가 점수 목록 반환
        
        Returns:
            (A 점수 목록, B 점수 목록)
        """
        a_ratings = []
        b_ratings = []
        
        for result in self.results:
            a_rating = result.get("variants", {}).get("A", {}).get("rating", 0)
            b_rating = result.get("variants", {}).get("B", {}).get("rating", 0)
            
            a_ratings.append(float(a_rating))
            b_ratings.append(float(b_rating))
        
        return a_ratings, b_ratings
    
    def calculate_averages(self) -> Tuple[float, float]:
        """
        변형 A와 B의 평균 점수 계산
        
        Returns:
            (A 평균, B 평균)
        """
        a_ratings, b_ratings = self.get_ratings()
        
        if not a_ratings or not b_ratings:
            return 0.0, 0.0
        
        a_avg = sum(a_ratings) / len(a_ratings)
        b_avg = sum(b_ratings) / len(b_ratings)
        
        return a_avg, b_avg
    
    def calculate_p_value(self) -> Optional[float]:
        """
        A/B 테스트의 p-값 계산 (t-검정)
        
        Returns:
            p-값 또는 None (계산 불가능한 경우)
        """
        a_ratings, b_ratings = self.get_ratings()
        
        if len(a_ratings) < 2 or len(b_ratings) < 2:
            return None
        
        try:
            # scipy가 설치되어 있지 않을 수 있으므로 간단한 t-검정 구현
            return self._simple_t_test(a_ratings, b_ratings)
        except Exception as e:
            logger.error(f"p-값 계산 중 오류 발생: {str(e)}")
            return None
    
    def _simple_t_test(self, a_values: List[float], b_values: List[float]) -> float:
        """
        간단한 t-검정 구현
        
        Args:
            a_values: A 그룹 값 목록
            b_values: B 그룹 값 목록
        
        Returns:
            근사 p-값
        """
        # 평균 계산
        a_mean = sum(a_values) / len(a_values)
        b_mean = sum(b_values) / len(b_values)
        
        # 분산 계산
        a_variance = sum((x - a_mean) ** 2 for x in a_values) / (len(a_values) - 1)
        b_variance = sum((x - b_mean) ** 2 for x in b_values) / (len(b_values) - 1)
        
        # 풀드 표준 오차 계산
        pooled_se = math.sqrt(a_variance / len(a_values) + b_variance / len(b_values))
        
        # t-값 계산
        if pooled_se == 0:
            return 1.0
        
        t_value = abs(a_mean - b_mean) / pooled_se
        
        # 자유도 계산 (근사)
        df = len(a_values) + len(b_values) - 2
        
        # p-값 근사 계산 (정규 분포 사용)
        # 정확한 계산을 위해서는 t-분포 CDF가 필요하지만, 여기서는 근사값 사용
        # 정규 분포로 근사 (df가 클 때 적절)
        z = t_value
        p_value = 2 * (1 - self._normal_cdf(z))
        
        return p_value
    
    def _normal_cdf(self, x: float) -> float:
        """
        표준 정규 분포 CDF 근사값
        
        Args:
            x: 표준 점수
        
        Returns:
            CDF 값
        """
        # 오차 함수 근사
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        
        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2.0)
        
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        
        return 0.5 * (1 + sign * y)
    
    def is_significant(self, threshold: Optional[float] = None) -> bool:
        """
        결과가 통계적으로 유의미한지 확인
        
        Args:
            threshold: 유의성 임계값 (기본값: 테스트에 설정된 임계값)
        
        Returns:
            유의미성 여부
        """
        if threshold is None:
            threshold = self.test_data.get("metric", {}).get("threshold", 0.05)
        
        p_value = self.calculate_p_value()
        
        if p_value is None:
            return False
        
        return p_value < threshold

def analyze_test_results(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    테스트 결과 분석
    
    Args:
        test_data: 테스트 데이터 딕셔너리
    
    Returns:
        분석 결과 요약
    """
    analyzer = ABTestAnalyzer(test_data)
    
    a_avg, b_avg = analyzer.calculate_averages()
    p_value = analyzer.calculate_p_value()
    significant = analyzer.is_significant()
    
    summary = {
        "total_samples": len(test_data.get("results", [])),
        "variant_a_avg": a_avg,
        "variant_b_avg": b_avg,
        "p_value": p_value,
        "significant": significant
    }
    
    return summary

def create_result_plot(test_data: Dict[str, Any]) -> Optional[plt.Figure]:
    """
    테스트 결과 그래프 생성
    
    Args:
        test_data: 테스트 데이터 딕셔너리
    
    Returns:
        Matplotlib 그림 객체 또는 None (그래프 생성 실패 시)
    """
    analyzer = ABTestAnalyzer(test_data)
    a_ratings, b_ratings = analyzer.get_ratings()
    
    if not a_ratings or not b_ratings:
        return None
    
    try:
        # 그림 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # 첫 번째 서브플롯: 평균 점수 비교 막대 그래프
        a_avg, b_avg = analyzer.calculate_averages()
        
        ax1.bar([test_data["variants"]["A"]["name"], test_data["variants"]["B"]["name"]], 
               [a_avg, b_avg], color=['#3498db', '#e74c3c'])
        
        ax1.set_title("평균 점수 비교")
        ax1.set_ylim(0, 5.5)
        ax1.set_ylabel("평균 점수")
        
        # 두 번째 서브플롯: 분포 히스토그램
        ax2.hist(a_ratings, alpha=0.5, bins=5, range=(0.5, 5.5), color='#3498db', 
                label=test_data["variants"]["A"]["name"])
        ax2.hist(b_ratings, alpha=0.5, bins=5, range=(0.5, 5.5), color='#e74c3c',
                label=test_data["variants"]["B"]["name"])
        
        ax2.set_title("점수 분포")
        ax2.set_xlabel("점수")
        ax2.set_ylabel("빈도")
        ax2.legend()
        
        # 레이아웃 조정
        fig.tight_layout()
        
        return fig
    
    except Exception as e:
        logger.error(f"결과 그래프 생성 중 오류 발생: {str(e)}")
        return None

def generate_report(test_data: Dict[str, Any]) -> str:
    """
    테스트 결과 보고서 생성
    
    Args:
        test_data: 테스트 데이터 딕셔너리
    
    Returns:
        마크다운 형식의 보고서 문자열
    """
    # 기본 정보
    report = f"# A/B 테스트 보고서: {test_data['test_name']}\n\n"
    report += f"생성 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 테스트 설명
    report += "## 테스트 정보\n\n"
    report += f"- 설명: {test_data.get('description', '')}\n"
    report += f"- 측정 지표: {test_data['metric']['name']}\n"
    report += f"- 유의성 임계값: {test_data['metric']['threshold']}\n\n"
    
    # 변형 정보
    report += "## 변형 정보\n\n"
    report += f"### 변형 A: {test_data['variants']['A']['name']}\n\n"
    report += "```\n" + test_data['variants']['A']['prompt'] + "\n```\n\n"
    
    report += f"### 변형 B: {test_data['variants']['B']['name']}\n\n"
    report += "```\n" + test_data['variants']['B']['prompt'] + "\n```\n\n"
    
    # 결과 요약
    summary = test_data.get("summary", {})
    report += "## 결과 요약\n\n"
    report += f"- 총 샘플 수: {summary.get('total_samples', 0)}\n"
    report += f"- 변형 A 평균 점수: {summary.get('variant_a_avg', 0):.2f}\n"
    report += f"- 변형 B 평균 점수: {summary.get('variant_b_avg', 0):.2f}\n"
    
    if summary.get("p_value") is not None:
        report += f"- p-값: {summary.get('p_value', 1.0):.4f}\n\n"
        
        if summary.get("significant", False):
            if summary.get("variant_a_avg", 0) > summary.get("variant_b_avg", 0):
                winner = f"{test_data['variants']['A']['name']} (A)"
            else:
                winner = f"{test_data['variants']['B']['name']} (B)"
            
            report += f"**결과**: 통계적으로 유의미한 차이가 있음 (승자: {winner})\n\n"
        else:
            report += "**결과**: 통계적으로 유의미한 차이가 없음\n\n"
    
    # 데이터 샘플
    report += "## 데이터 샘플\n\n"
    
    # 샘플 5개 또는 전체 (더 적은 것)
    sample_count = min(5, len(test_data.get("results", [])))
    
    if sample_count > 0:
        report += "| 입력 | 변형 A 평가 | 변형 B 평가 |\n"
        report += "|------|----------|----------|\n"
        
        for i in range(sample_count):
            result = test_data["results"][i]
            input_short = result.get("input", "")[:50] + "..." if len(result.get("input", "")) > 50 else result.get("input", "")
            a_rating = result.get("variants", {}).get("A", {}).get("rating", 0)
            b_rating = result.get("variants", {}).get("B", {}).get("rating", 0)
            
            report += f"| {input_short} | {a_rating} | {b_rating} |\n"
    else:
        report += "*데이터 없음*\n\n"
    
    # 결론 및 권장 사항
    report += "## 결론 및 권장 사항\n\n"
    
    if summary.get("significant", False):
        if summary.get("variant_a_avg", 0) > summary.get("variant_b_avg", 0):
            report += f"변형 A ({test_data['variants']['A']['name']})가 변형 B ({test_data['variants']['B']['name']})보다 "
            report += f"통계적으로 유의미하게 우수한 성능을 보입니다. "
            report += "따라서 변형 A를 적용하는 것을 권장합니다.\n\n"
        else:
            report += f"변형 B ({test_data['variants']['B']['name']})가 변형 A ({test_data['variants']['A']['name']})보다 "
            report += f"통계적으로 유의미하게 우수한 성능을 보입니다. "
            report += "따라서 변형 B를 적용하는 것을 권장합니다.\n\n"
    else:
        report += "두 변형 간에 통계적으로 유의미한 차이가 없습니다. "
        
        if summary.get("total_samples", 0) < 30:
            report += "더 많은 샘플을 수집하여 테스트를 계속 진행하는 것을 권장합니다.\n\n"
        else:
            report += "충분한 샘플이 수집되었으므로, 개인 선호도나 구현 복잡성 등 다른 요소를 기준으로 선택하는 것을 권장합니다.\n\n"
    
    return report
