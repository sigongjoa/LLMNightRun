"""
요약 생성 모듈 - 논문 요약 생성 기능

추출적 요약(extractive) 및 LLM 기반 요약(abstractive) 방식을 지원
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import nltk
from nltk.tokenize import sent_tokenize
import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Summarizer:
    """논문 요약 생성 클래스"""
    
    def __init__(self):
        """Summarizer 초기화"""
        pass
        
    def get_extractive_summary(self, text: str, sentences: List[str], 
                              keywords: List[Dict[str, Any]], 
                              ratio: float = 0.2, 
                              max_sentences: int = 10) -> str:
        """
        추출적 요약 생성 (중요 문장 추출)
        
        Args:
            text (str): 원본 텍스트
            sentences (List[str]): 문장 목록
            keywords (List[Dict[str, Any]]): 추출된 키워드 목록
            ratio (float): 요약 비율 (0.0 ~ 1.0)
            max_sentences (int): 최대 문장 수
            
        Returns:
            str: 추출적 요약 텍스트
        """
        if not sentences:
            logger.warning("No sentences provided for extractive summarization")
            return ""
            
        # 문장 수가 너무 적은 경우
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
        
        try:
            # 키워드 리스트 추출
            keyword_list = [kw['keyword'] for kw in keywords]
            
            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer()
            sentence_vectors = vectorizer.fit_transform(sentences)
            
            # 문장 간 유사도 계산
            similarity_matrix = cosine_similarity(sentence_vectors)
            
            # TextRank 알고리즘 적용
            graph = nx.from_numpy_array(similarity_matrix)
            scores = nx.pagerank(graph)
            
            # 키워드 가중치 추가
            for i, sentence in enumerate(sentences):
                for keyword in keyword_list:
                    if keyword.lower() in sentence.lower():
                        # 키워드가 포함된 문장에 가중치 부여
                        scores[i] = scores[i] * 1.2
            
            # 추출할 문장 수 계산
            num_sentences = min(max_sentences, max(1, int(len(sentences) * ratio)))
            
            # 문장 인덱스와 점수로 정렬
            ranked_sentences = sorted(((i, score) for i, score in scores.items()), 
                                    key=lambda x: x[1], reverse=True)
            
            # 상위 N개 문장 선택 (원래 순서 유지)
            top_sentence_indices = sorted([idx for idx, _ in ranked_sentences[:num_sentences]])
            
            # 요약 생성
            summary = " ".join([sentences[i] for i in top_sentence_indices])
            
            logger.info(f"Generated extractive summary with {num_sentences} sentences")
            return summary
            
        except Exception as e:
            logger.error(f"Error in extractive summarization: {e}")
            return " ".join(sentences[:max_sentences])  # 오류 시 기본 요약 반환
    
    def get_llm_summary(self, text: str, title: str, keywords: List[Dict[str, Any]], 
                       api_url: Optional[str] = None, 
                       max_length: int = 500) -> Optional[str]:
        """
        LLM 기반 생성적 요약 생성
        
        Args:
            text (str): 원본 텍스트
            title (str): 논문 제목
            keywords (List[Dict[str, Any]]): 추출된 키워드 목록
            api_url (str, optional): LLM API URL
            max_length (int): 최대 요약 길이
            
        Returns:
            str: LLM 기반 요약 텍스트
        """
        # 로컬 LLM API URL 확인
        if not api_url:
            # 기본 로컬 LLM API URL 설정
            api_url = "http://localhost:8000/api/local-llm/chat"
        
        # 키워드 리스트 추출
        keyword_list = [kw['keyword'] for kw in keywords[:10]]
        keyword_str = ", ".join(keyword_list)
        
        # 입력 텍스트 길이 제한
        max_input_chars = 15000  # 토큰 한계에 따라 조정
        if len(text) > max_input_chars:
            logger.info(f"Truncating input text from {len(text)} to {max_input_chars} characters")
            text = text[:max_input_chars] + "..."
        
        # 요약 생성 프롬프트
        prompt = f"""다음은 제목이 "{title}"인 학술 논문의 내용입니다. 이 논문의 핵심 키워드는 다음과 같습니다: {keyword_str}

논문 내용:
{text}

위 논문의 주요 내용을 요약해주세요. 다음 사항을 포함하여 {max_length}자 이내로 작성해주세요:
1. 연구 목적
2. 주요 방법론
3. 핵심 결과 및 발견
4. 결론 및 의의

요약:"""
        
        try:
            # LLM API 호출
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful research assistant. Summarize academic papers concisely and accurately."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # API 요청
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    summary = result.get('message', {}).get('content', '')
                    
                    if summary:
                        logger.info(f"Generated LLM summary: {len(summary)} characters")
                        return summary
                    else:
                        logger.error(f"Empty summary from LLM API")
                except Exception as e:
                    logger.error(f"Error parsing LLM API response: {e}")
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                
            return None
            
        except Exception as e:
            logger.error(f"Error in LLM summarization: {e}")
            return None
    
    def generate_summary(self, text_data: Dict[str, Any], 
                        keywords: List[Dict[str, Any]],
                        title: str = "", 
                        use_llm: bool = True,
                        extractive_ratio: float = 0.2) -> Dict[str, Any]:
        """
        텍스트 요약 생성 (추출적 + 생성적)
        
        Args:
            text_data (Dict[str, Any]): 텍스트 처리 결과 데이터
            keywords (List[Dict[str, Any]]): 추출된 키워드 목록
            title (str): 논문 제목
            use_llm (bool): LLM 사용 여부
            extractive_ratio (float): 추출적 요약 비율
            
        Returns:
            Dict[str, Any]: 요약 결과
        """
        if not text_data.get('success', False):
            logger.error("Invalid text data for summarization")
            return {
                'success': False,
                'error': 'Invalid text data'
            }
            
        result = {'success': True}
        
        try:
            # 추출적 요약 생성
            extractive_summary = self.get_extractive_summary(
                text_data['clean_text'],
                text_data['sentences'],
                keywords,
                ratio=extractive_ratio
            )
            result['extractive_summary'] = extractive_summary
            
            # LLM 기반 요약 시도
            if use_llm:
                with ThreadPoolExecutor() as executor:
                    # 비동기로 LLM 요약 요청
                    future = executor.submit(
                        self.get_llm_summary,
                        text_data['clean_text'],
                        title,
                        keywords
                    )
                    
                    # 최대 30초 대기
                    try:
                        llm_summary = future.result(timeout=30)
                        if llm_summary:
                            result['llm_summary'] = llm_summary
                    except Exception as e:
                        logger.error(f"Error or timeout in LLM summarization: {e}")
                        result['llm_error'] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            return {
                'success': False,
                'error': str(e),
                'extractive_summary': extractive_summary if 'extractive_summary' in locals() else None
            }

# 사용 예시
if __name__ == "__main__":
    from processor import TextProcessor
    from keyword_extractor import KeywordExtractor
    
    # 샘플 텍스트
    sample_text = """
    Transformer models have revolutionized natural language processing by enabling more efficient processing of sequential data and capturing long-range dependencies. Unlike recurrent neural networks (RNNs) that process data sequentially, transformers process the entire sequence simultaneously, leveraging self-attention mechanisms to weigh the importance of different parts of the input sequence.
    
    The key innovation in transformer architectures is the self-attention mechanism, which allows the model to focus on different parts of the input sequence when producing each element of the output. This mechanism computes attention weights between all pairs of positions in the sequence, enabling the model to capture complex relationships and dependencies.
    
    Transformer-based models like BERT, GPT, and T5, have achieved state-of-the-art results across various NLP tasks, including text classification, question answering, and machine translation. The success of these models can be attributed to their ability to pre-train on large corpora of text and then fine-tune on specific downstream tasks.
    
    Despite their success, transformers face challenges such as computational complexity, which scales quadratically with sequence length, and difficulties in modeling very long-range dependencies. Recent research has focused on addressing these limitations through efficient attention mechanisms, sparse transformers, and other architectural modifications.
    
    In conclusion, transformers have fundamentally changed the landscape of NLP and continue to be a driving force behind advancements in the field. Their ability to capture contextual information and process sequences in parallel has made them the architecture of choice for many state-of-the-art language models.
    """
    
    # 텍스트 처리
    processor = TextProcessor()
    processed_text = processor.preprocess_text(sample_text)
    processed_text['success'] = True
    
    # 키워드 추출
    extractor = KeywordExtractor()
    keywords = extractor.extract_keywords(processed_text, top_n=10)
    
    # 요약 생성
    summarizer = Summarizer()
    summary_result = summarizer.generate_summary(
        processed_text,
        keywords,
        title="Transformer Models in Natural Language Processing",
        use_llm=False  # LLM 없이 추출적 요약만 사용
    )
    
    if summary_result['success']:
        print("추출적 요약:")
        print(summary_result['extractive_summary'])
        
        if 'llm_summary' in summary_result:
            print("\nLLM 요약:")
            print(summary_result['llm_summary'])
    else:
        print(f"요약 생성 실패: {summary_result.get('error')}")
