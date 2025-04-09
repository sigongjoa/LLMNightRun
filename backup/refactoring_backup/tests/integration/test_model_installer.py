"""
GitHub 모델 자동 설치 시스템 테스트 스크립트
"""

import os
import sys
import json
from pathlib import Path

# 상위 디렉토리를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.model_installer.controller import ModelInstallerController


def test_controller_init():
    """컨트롤러 초기화 테스트"""
    print("=== 컨트롤러 초기화 테스트 ===")
    
    models_dir = os.path.join(os.getcwd(), "models")
    controller = ModelInstallerController(models_base_dir=models_dir)
    
    print(f"컨트롤러 초기화 성공: {controller}")
    print(f"모델 기본 디렉토리: {controller.models_base_dir}")
    
    return controller


def test_install_model(controller, repo_url):
    """모델 설치 테스트"""
    print(f"\n=== 모델 설치 테스트: {repo_url} ===")
    
    result = controller.install_model(repo_url)
    
    print(f"설치 상태: {result['status']}")
    
    if result['status'] == 'success':
        print(f"모델 이름: {result['model_name']}")
        print(f"모델 디렉토리: {result['model_dir']}")
        print(f"소요 시간: {result['elapsed_time']:.2f}초")
    else:
        print(f"설치 실패: {result.get('error', '알 수 없는 오류')}")
    
    print("\n설치 단계별 결과:")
    for i, step in enumerate(result.get('steps', []), 1):
        print(f"{i}. {step['name']}: {step['status']}")
        if step['status'] == 'failed' and 'error' in step:
            print(f"   오류: {step['error']}")
    
    return result


def test_list_models(controller):
    """설치된 모델 목록 조회 테스트"""
    print("\n=== 설치된 모델 목록 조회 테스트 ===")
    
    models = controller.list_installed_models()
    
    print(f"설치된 모델 수: {len(models)}")
    
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']} - 경로: {model['path']}")
    
    return models


def test_get_model_info(controller, model_name):
    """모델 정보 조회 테스트"""
    print(f"\n=== 모델 정보 조회 테스트: {model_name} ===")
    
    model_info = controller.get_model_info(model_name)
    
    if model_info:
        print(f"모델 이름: {model_info['name']}")
        print(f"모델 경로: {model_info['path']}")
        
        if 'error' in model_info:
            print(f"오류: {model_info['error']}")
        elif 'metadata' in model_info:
            metadata = model_info['metadata']
            print(f"생성일: {metadata.get('created_at', '알 수 없음')}")
            print(f"원본 저장소: {metadata.get('repo_url', '알 수 없음')}")
            
            # 모델 유형 정보
            if 'repo_analysis' in metadata and 'model_type' in metadata['repo_analysis']:
                model_type = metadata['repo_analysis']['model_type']
                print(f"모델 유형: {model_type.get('primary', '알 수 없음')}")
    else:
        print(f"모델 '{model_name}'을(를) 찾을 수 없습니다.")
    
    return model_info


def test_run_model(controller, model_name, script_name=None):
    """모델 실행 테스트"""
    print(f"\n=== 모델 실행 테스트: {model_name} ===")
    print(f"실행 스크립트: {script_name or '기본 런처'}")
    
    result = controller.run_model(model_name, script_name)
    
    print(f"실행 상태: {result['status']}")
    
    if result['status'] == 'success':
        print(f"프로세스 ID: {result.get('process_id', '알 수 없음')}")
        print(f"메시지: {result.get('message', '')}")
    else:
        print(f"실행 실패: {result.get('error', '알 수 없는 오류')}")
    
    return result


def test_analyze_error(controller, error_log):
    """에러 로그 분석 테스트"""
    print("\n=== 에러 로그 분석 테스트 ===")
    
    analysis = controller.analyze_error(error_log)
    
    if 'error' in analysis:
        print(f"분석 실패: {analysis['error']}")
    else:
        print(f"에러 유형: {analysis.get('error_type', '알 수 없음')}")
        print(f"심각도: {analysis.get('severity', '알 수 없음')}")
        print("\n분석 결과:")
        print(analysis.get('analysis', '분석 결과 없음'))
        
        print("\n해결 방법:")
        for i, solution in enumerate(analysis.get('solution', []), 1):
            print(f"{i}. {solution}")
    
    return analysis


def main():
    # 샘플 GitHub 저장소 URL (테스트용 작은 모델 저장소)
    repo_url = "https://github.com/karpathy/nanoGPT"
    
    # 컨트롤러 초기화
    controller = test_controller_init()
    
    # 모델 설치
    install_result = test_install_model(controller, repo_url)
    
    # 설치된 모델 목록 조회
    models = test_list_models(controller)
    
    # 모델 정보 조회 (설치에 성공한 경우)
    if install_result['status'] == 'success':
        model_name = install_result['model_name']
        model_info = test_get_model_info(controller, model_name)
        
        # 모델 실행
        # 주의: 실제로 모델이 실행됩니다. 테스트 환경에 따라 주석 처리하세요.
        # run_result = test_run_model(controller, model_name)
    
    # 에러 로그 분석 테스트 (샘플 에러 로그)
    sample_error_log = """
    Traceback (most recent call last):
      File "train.py", line 156, in <module>
        model = GPT(config).to(device)
      File "/usr/local/lib/python3.8/site-packages/torch/nn/modules/module.py", line 1182, in to
        return self._apply(convert)
    RuntimeError: CUDA error: out of memory
    CUDA kernel launch failure: out of memory
    """
    
    analysis = test_analyze_error(controller, sample_error_log)


if __name__ == "__main__":
    main()
