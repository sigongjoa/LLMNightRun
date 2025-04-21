"""
텍스트 처리 모듈 - PDF에서 텍스트 추출 및 전처리 기능

PDF 파일에서 텍스트를 추출하고 전처리하는 기능 제공
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# 필요한 NLTK 데이터 다운로드
# NLTK 데이터는 메인 애플리케이션에서 관리 - nltk_setup.py 활용
# 이 경고는 로그를 줄이기 위해 잠재적 오류만 잡음
try:
    from nltk_setup import setup_nltk_data
    # 아직 설정되지 않았다면 설정
    if not hasattr(nltk.data, '_nltk_data_dir_set'):
        setup_nltk_data()
        nltk.data._nltk_data_dir_set = True
except ImportError:
    # 기본 설정 시도
    try:
        nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
        nltk.data.path.insert(0, nltk_data_dir)
    except Exception as e:
        logger.warning(f"NLTK 데이터 경로 설정 오류: {e}")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextProcessor:
    """PDF 텍스트 추출 및 전처리 클래스"""
    
    def __init__(self, language: str = 'english'):
        """
        TextProcessor 초기화
        
        Args:
            language (str): 텍스트 언어 (NLTK stopwords 언어)
        """
        self.language = language
        
        # 안전하게 stopwords 가져오기
        try:
            self.stop_words = set(stopwords.words(language))
        except Exception as e:
            logger.warning(f"Stopwords 로드 오류, 기본 영어 불용어 사용: {e}")
            # 기본 영어 불용어 사용
            self.stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 
                'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 
                'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 
                'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 
                'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 
                'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 
                'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 
                'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 
                'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 
                'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 
                'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
                'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 
                'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'])
        
        # 안전하게 lemmatizer 가져오기
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception as e:
            logger.warning(f"WordNetLemmatizer 로드 오류: {e}")
            # 기본 함수로 구현
            self.lemmatizer = None
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            
        Returns:
            str: 추출된 텍스트
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return ""
            
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # 각 페이지에서 텍스트 추출
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
            
    def clean_text(self, text: str) -> str:
        """
        텍스트 기본 정제
        
        Args:
            text (str): 원본 텍스트
            
        Returns:
            str: 정제된 텍스트
        """
        # 여러 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # LaTeX 수식 제거 ($ ... $ 또는 $$ ... $$ 형태)
        text = re.sub(r'\$\$(.*?)\$\$', ' ', text)
        text = re.sub(r'\$(.*?)\$', ' ', text)
        
        # 특수문자 정제
        text = re.sub(r'[^\w\s.,;:!?()]', ' ', text)
        
        # 참조 표기 제거 ([1], [2,3] 등)
        text = re.sub(r'\[\d+(,\s*\d+)*\]', ' ', text)
        
        return text.strip()
            
    def preprocess_text(self, text: str, remove_stopwords: bool = True, lemmatize: bool = True) -> Dict[str, Any]:
        """
        텍스트 전처리
        
        Args:
            text (str): 정제할 텍스트
            remove_stopwords (bool): 불용어 제거 여부
            lemmatize (bool): 표제어 추출 여부
            
        Returns:
            Dict[str, Any]: 전처리 결과 (문장, 토큰 등)
        """
        logger.info("Preprocessing text...")
        
        # 텍스트 정제
        clean_txt = self.clean_text(text)
        
        # 문장 분리
        try:
            sentences = sent_tokenize(clean_txt)
            logger.info(f"Extracted {len(sentences)} sentences")
        except Exception as e:
            logger.warning(f"NLTK sent_tokenize 오류: {e} - 간단한 문장 분리기 사용")
            # 간단한 문장 분리기 사용
            sentences = [s.strip() for s in re.split(r'[.!?]\s', clean_txt) if s.strip()]
            if clean_txt and not sentences:
                sentences = [clean_txt]  # 분리가 안되면 전체를 하나의 문장으로
            logger.info(f"Extracted {len(sentences)} sentences using fallback method")
        
        # 토큰화 및 전처리
        tokens = []
        processed_sentences = []
        
        for sentence in sentences:
            # 단어 토큰화
            try:
                words = word_tokenize(sentence.lower())
            except Exception as e:
                logger.warning(f"NLTK word_tokenize 오류: {e} - 간단한 단어 분리기 사용")
                # 간단한 단어 분리기 사용
                words = [w.strip().lower() for w in re.findall(r'\w+', sentence.lower())]
            
            # 불용어 제거
            if remove_stopwords:
                words = [word for word in words if word not in self.stop_words and len(word) > 1]
                
            # 표제어 추출
            if lemmatize and self.lemmatizer:
                try:
                    words = [self.lemmatizer.lemmatize(word) for word in words]
                except Exception as e:
                    logger.warning(f"NLTK lemmatize 오류: {e} - 표제어 추출 건너띀")
                    # 문제 발생 시 그냥 원본 단어 사용
                
            if words:  # 빈 문장 제외
                tokens.extend(words)
                processed_sentences.append(words)
                
        return {
            'original_text': text,
            'clean_text': clean_txt,
            'sentences': sentences,
            'processed_sentences': processed_sentences,
            'tokens': tokens
        }
        
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일 처리 (추출 및 전처리)
        
        Args:
            pdf_path (str): PDF 파일 경로
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        # PDF에서 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return {
                'success': False,
                'error': 'No text extracted',
                'pdf_path': pdf_path
            }
            
        # 텍스트 전처리
        result = self.preprocess_text(text)
        result['pdf_path'] = pdf_path
        result['success'] = True
        
        logger.info(f"Processed PDF {pdf_path}: {len(result['sentences'])} sentences, {len(result['tokens'])} tokens")
        
        return result

# 사용 예시
if __name__ == "__main__":
    processor = TextProcessor()
    
    # 예시 PDF 처리
    pdf_path = "papers/example.pdf"
    if os.path.exists(pdf_path):
        result = processor.process_pdf(pdf_path)
        
        if result['success']:
            print(f"원본 텍스트 일부: {result['original_text'][:200]}...")
            print(f"정제된 텍스트 일부: {result['clean_text'][:200]}...")
            print(f"문장 수: {len(result['sentences'])}")
            print(f"토큰 수: {len(result['tokens'])}")
    else:
        print(f"PDF 파일이 존재하지 않습니다: {pdf_path}")
