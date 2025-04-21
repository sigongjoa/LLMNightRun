"""
키워드 추출 모듈 - 텍스트에서 핵심 키워드 추출 기능

TF-IDF 및 TextRank 알고리즘을 사용하여 핵심 키워드를 추출
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx
from collections import Counter
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KeywordExtractor:
    """텍스트에서 핵심 키워드 추출 클래스"""
    
    def __init__(self, min_word_length: int = 3, ngram_range: Tuple[int, int] = (1, 2)):
        """
        KeywordExtractor 초기화
        
        Args:
            min_word_length (int): 최소 단어 길이
            ngram_range (Tuple[int, int]): n-gram 범위 (min, max)
        """
        self.min_word_length = min_word_length
        self.ngram_range = ngram_range
        
    def extract_tfidf_keywords(self, text: str, processed_tokens: List[str], 
                              top_n: int = 10) -> List[Tuple[str, float]]:
        """
        TF-IDF 기반 키워드 추출
        
        Args:
            text (str): 원본 텍스트
            processed_tokens (List[str]): 전처리된 토큰 목록
            top_n (int): 추출할 상위 키워드 수
            
        Returns:
            List[Tuple[str, float]]: (키워드, 점수) 튜플 목록
        """
        logger.info(f"Extracting TF-IDF keywords (top {top_n})...")
        
        # 토큰을 문장으로 변환
        document = ' '.join(processed_tokens)
        
        # TF-IDF 벡터화
        tfidf_vectorizer = TfidfVectorizer(
            min_df=1, 
            max_df=0.9,
            ngram_range=self.ngram_range,
            stop_words='english'
        )
        
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform([document])
            feature_names = tfidf_vectorizer.get_feature_names_out()
            
            # 결과를 (단어, 점수) 형태로 변환
            tfidf_scores = zip(feature_names, tfidf_matrix.toarray()[0])
            
            # 길이 필터링 및 정렬
            sorted_keywords = sorted(
                [(word, score) for word, score in tfidf_scores if len(word) >= self.min_word_length],
                key=lambda x: x[1],
                reverse=True
            )
            
            return sorted_keywords[:top_n]
            
        except Exception as e:
            logger.error(f"Error in TF-IDF keyword extraction: {e}")
            return []
        
    def extract_textrank_keywords(self, processed_sentences: List[List[str]], 
                                 top_n: int = 10) -> List[Tuple[str, float]]:
        """
        TextRank 알고리즘 기반 키워드 추출
        
        Args:
            processed_sentences (List[List[str]]): 전처리된 문장별 토큰 목록
            top_n (int): 추출할 상위 키워드 수
            
        Returns:
            List[Tuple[str, float]]: (키워드, 점수) 튜플 목록
        """
        logger.info(f"Extracting TextRank keywords (top {top_n})...")
        
        # 단어 간 동시 발생 행렬 생성
        word_freq = Counter()
        for sentence in processed_sentences:
            word_freq.update(sentence)
            
        # 최소 빈도수 기준으로 필터링
        min_freq = 2
        filtered_words = {word for word, freq in word_freq.items() 
                         if freq >= min_freq and len(word) >= self.min_word_length}
        
        # 그래프 생성
        graph = nx.Graph()
        for sentence in processed_sentences:
            # 문장 내 존재하는 단어만 필터링
            filtered_sentence = [word for word in sentence if word in filtered_words]
            
            # 문장 내 단어 간 엣지 추가
            for i, word1 in enumerate(filtered_sentence):
                for word2 in filtered_sentence[i+1:]:
                    if word1 != word2:
                        if graph.has_edge(word1, word2):
                            graph[word1][word2]['weight'] += 1.0
                        else:
                            graph.add_edge(word1, word2, weight=1.0)
        
        # 빈 그래프인 경우
        if not graph.nodes():
            logger.warning("TextRank graph is empty. Returning empty results.")
            return []
            
        try:
            # TextRank 알고리즘 적용
            scores = nx.pagerank(graph, weight='weight')
            
            # 결과 정렬
            sorted_keywords = sorted(
                [(word, score) for word, score in scores.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            return sorted_keywords[:top_n]
            
        except Exception as e:
            logger.error(f"Error in TextRank keyword extraction: {e}")
            return []
    
    def combine_keywords(self, tfidf_keywords: List[Tuple[str, float]], 
                         textrank_keywords: List[Tuple[str, float]],
                         top_n: int = 15) -> List[Dict[str, Any]]:
        """
        TF-IDF와 TextRank 결과 결합 및 정규화
        
        Args:
            tfidf_keywords (List[Tuple[str, float]]): TF-IDF 키워드 목록
            textrank_keywords (List[Tuple[str, float]]): TextRank 키워드 목록
            top_n (int): 최종 키워드 수
            
        Returns:
            List[Dict[str, Any]]: 결합된 키워드 목록
        """
        # 두 방식의 키워드 집합
        tfidf_words = {word: score for word, score in tfidf_keywords}
        textrank_words = {word: score for word, score in textrank_keywords}
        
        # 모든 단어 집합
        all_words = set(tfidf_words.keys()) | set(textrank_words.keys())
        
        # 점수 정규화 함수
        def normalize_scores(scores):
            if not scores:
                return {}
            max_score = max(scores.values())
            min_score = min(scores.values())
            if max_score == min_score:
                return {word: 1.0 for word in scores}
            return {word: (score - min_score) / (max_score - min_score) 
                    for word, score in scores.items()}
        
        # 점수 정규화
        if tfidf_words:
            norm_tfidf = normalize_scores(tfidf_words)
        else:
            norm_tfidf = {}
            
        if textrank_words:
            norm_textrank = normalize_scores(textrank_words)
        else:
            norm_textrank = {}
        
        # 결합 점수 계산
        combined_scores = []
        for word in all_words:
            tfidf_score = norm_tfidf.get(word, 0.0)
            textrank_score = norm_textrank.get(word, 0.0)
            
            # 방법 1: 단순 평균
            combined_score = (tfidf_score + textrank_score) / 2
            
            # 방법 2: 가중 평균 (필요시 사용)
            # tfidf_weight, textrank_weight = 0.6, 0.4
            # combined_score = tfidf_score * tfidf_weight + textrank_score * textrank_weight
            
            combined_scores.append({
                'keyword': word,
                'score': combined_score,
                'tfidf_score': tfidf_score,
                'textrank_score': textrank_score
            })
        
        # 결합 점수 기준 정렬 및 상위 N개 선택
        combined_scores.sort(key=lambda x: x['score'], reverse=True)
        return combined_scores[:top_n]
    
    def extract_keywords(self, text_data: Dict[str, Any], top_n: int = 15) -> List[Dict[str, Any]]:
        """
        텍스트 데이터에서 키워드 추출 (TF-IDF + TextRank)
        
        Args:
            text_data (Dict[str, Any]): 텍스트 처리 결과 데이터
            top_n (int): 최종 키워드 수
            
        Returns:
            List[Dict[str, Any]]: 추출된 키워드 목록
        """
        if not text_data.get('success', False):
            logger.error("Invalid text data for keyword extraction")
            return []
        
        try:
            # TF-IDF 기반 키워드 추출
            tfidf_keywords = self.extract_tfidf_keywords(
                text_data['clean_text'], 
                text_data['tokens'],
                top_n=top_n
            )
            
            # TextRank 기반 키워드 추출
            textrank_keywords = self.extract_textrank_keywords(
                text_data['processed_sentences'],
                top_n=top_n
            )
            
            # 결과 결합
            combined_keywords = self.combine_keywords(
                tfidf_keywords,
                textrank_keywords,
                top_n=top_n
            )
            
            logger.info(f"Extracted {len(combined_keywords)} keywords")
            return combined_keywords
            
        except Exception as e:
            logger.error(f"Error in keyword extraction: {e}")
            return []

# 사용 예시
if __name__ == "__main__":
    from processor import TextProcessor
    
    processor = TextProcessor()
    extractor = KeywordExtractor()
    
    # 예시 텍스트
    sample_text = """
    Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.
    Deep-learning architectures such as deep neural networks, deep belief networks, deep reinforcement learning, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, machine translation, bioinformatics, drug design, medical image analysis, climate science, material inspection and board game programs, where they have produced results comparable to and in some cases surpassing human expert performance.
    Artificial neural networks (ANNs) were inspired by information processing and distributed communication nodes in biological systems. ANNs have various differences from biological brains. Specifically, neural networks tend to be static and symbolic, while the biological brain of most living organisms is dynamic (plastic) and analog.
    """
    
    # 텍스트 전처리
    processed_text = processor.preprocess_text(sample_text)
    
    # 키워드 추출
    keywords = extractor.extract_keywords(
        {'success': True, **processed_text}, 
        top_n=10
    )
    
    # 결과 출력
    for i, keyword in enumerate(keywords):
        print(f"{i+1}. {keyword['keyword']} (Score: {keyword['score']:.4f})")
