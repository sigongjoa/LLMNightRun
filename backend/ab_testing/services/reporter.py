"""
A/B 테스트 보고서 생성 서비스

실험 결과 보고서를 생성하고 내보내는 서비스를 제공합니다.
"""

import os
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.logger import get_logger
from backend.ab_testing import models
from backend.ab_testing.config import ab_testing_settings

# 로거 설정
logger = get_logger(__name__)


class Reporter:
    """보고서 생성 서비스 클래스"""
    
    def __init__(self, db: Session):
        """초기화"""
        self.db = db
        
    async def generate_report(
        self, 
        experiment_set_id: int, 
        format: str = "html",
        run_id: Optional[str] = None,
        report_id: Optional[str] = None
    ) -> str:
        """실험 세트 보고서를 생성합니다."""
        logger.info(f"보고서 생성 시작: experiment_set_id={experiment_set_id}, format={format}")
        
        # 결과 및 평가 데이터 수집
        data = await self._collect_report_data(experiment_set_id, run_id)
        
        # 보고서 ID 생성
        if not report_id:
            report_id = f"report_{experiment_set_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # 보고서 디렉토리 확인
        reports_dir = ab_testing_settings.reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
        # 형식에 따른 보고서 생성
        if format.lower() == "html":
            report_path = os.path.join(reports_dir, f"{report_id}.html")
            await self._generate_html_report(data, report_path)
        elif format.lower() == "pdf":
            report_path = os.path.join(reports_dir, f"{report_id}.pdf")
            await self._generate_pdf_report(data, report_path)
        elif format.lower() == "json":
            report_path = os.path.join(reports_dir, f"{report_id}.json")
            await self._generate_json_report(data, report_path)
        else:
            raise ValueError(f"지원되지 않는 보고서 형식: {format}")
        
        logger.info(f"보고서 생성 완료: path={report_path}")
        return report_path
    
    async def _collect_report_data(
        self, experiment_set_id: int, run_id: Optional[str]
    ) -> Dict[str, Any]:
        """보고서 데이터를 수집합니다."""
        # 실험 세트 정보 조회
        experiment_set = self.db.query(models.ExperimentSet).filter(
            models.ExperimentSet.id == experiment_set_id
        ).first()
        
        if not experiment_set:
            raise ValueError(f"실험 세트를 찾을 수 없음: id={experiment_set_id}")
        
        # 실험 목록 조회
        experiments = self.db.query(models.Experiment).filter(
            models.Experiment.experiment_set_id == experiment_set_id
        ).all()
        
        # 실험 결과 쿼리 기본 설정
        results_query = self.db.query(models.ExperimentResult).join(
            models.Experiment, 
            models.ExperimentResult.experiment_id == models.Experiment.id
        ).filter(
            models.Experiment.experiment_set_id == experiment_set_id
        )
        
        # run_id가 지정된 경우 필터링
        if run_id:
            results_query = results_query.filter(models.ExperimentResult.run_id == run_id)
        
        # 실험 결과 조회
        results = results_query.all()
        
        # 평가 결과 조회
        evaluations = self.db.query(models.Evaluation).join(
            models.ExperimentResult,
            models.Evaluation.result_id == models.ExperimentResult.id
        ).join(
            models.Experiment,
            models.ExperimentResult.experiment_id == models.Experiment.id
        ).filter(
            models.Experiment.experiment_set_id == experiment_set_id
        )
        
        # run_id가 지정된 경우 필터링
        if run_id:
            evaluations = evaluations.filter(models.ExperimentResult.run_id == run_id)
        
        evaluations = evaluations.all()
        
        # 실험별 데이터 수집
        experiment_data = []
        for experiment in experiments:
            # 실험 결과 필터링
            exp_results = [r for r in results if r.experiment_id == experiment.id]
            
            # 실험 평가 필터링
            exp_evaluations = []
            for result in exp_results:
                eval_items = [e for e in evaluations if e.result_id == result.id]
                exp_evaluations.extend(eval_items)
            
            # 결과 요약
            experiment_data.append({
                "id": experiment.id,
                "name": experiment.name,
                "model": experiment.model,
                "prompt": experiment.prompt,
                "parameters": experiment.params,
                "results": [
                    {
                        "id": r.id,
                        "output": r.output,
                        "status": r.status,
                        "execution_time": r.execution_time,
                        "token_usage": r.token_usage,
                        "created_at": r.created_at,
                        "evaluations": [
                            {
                                "metric": e.metric_name,
                                "score": e.score,
                                "details": e.details
                            }
                            for e in evaluations if e.result_id == r.id
                        ]
                    }
                    for r in exp_results
                ]
            })
        
        # 종합 데이터 수집
        return {
            "experiment_set": {
                "id": experiment_set.id,
                "name": experiment_set.name,
                "description": experiment_set.description,
                "created_at": experiment_set.created_at,
                "config": experiment_set.config
            },
            "run_id": run_id,
            "experiments": experiment_data,
            "report_generated_at": datetime.utcnow()
        }
    
    async def _generate_html_report(self, data: Dict[str, Any], output_path: str):
        """HTML 형식 보고서를 생성합니다."""
        # 간단한 HTML 템플릿
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>A/B 테스트 보고서: {data["experiment_set"]["name"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333366; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .container {{ margin-bottom: 30px; }}
                .experiment {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; }}
                .result {{ margin-top: 10px; padding: 10px; background-color: #f9f9f9; }}
                .eval {{ margin-left: 20px; }}
            </style>
        </head>
        <body>
            <h1>A/B 테스트 보고서</h1>
            <div class="container">
                <h2>{data["experiment_set"]["name"]}</h2>
                <p><strong>설명:</strong> {data["experiment_set"]["description"] or "설명 없음"}</p>
                <p><strong>생성일:</strong> {data["experiment_set"]["created_at"]}</p>
                <p><strong>보고서 생성일:</strong> {data["report_generated_at"]}</p>
                <p><strong>실행 ID:</strong> {data["run_id"] or "전체 실행"}</p>
            </div>
            
            <h2>실험 결과 요약</h2>
        """
        
        # 실험별 결과 추가
        for experiment in data["experiments"]:
            html += f"""
            <div class="experiment">
                <h3>실험 {experiment["id"]}: {experiment["name"]}</h3>
                <p><strong>모델:</strong> {experiment["model"]}</p>
                <p><strong>프롬프트:</strong> {experiment["prompt"]}</p>
                
                <h4>결과:</h4>
            """
            
            for result in experiment["results"]:
                html += f"""
                <div class="result">
                    <p><strong>상태:</strong> {result["status"]}</p>
                    <p><strong>실행 시간:</strong> {result["execution_time"]} 초</p>
                    <p><strong>토큰 사용량:</strong> {result["token_usage"]}</p>
                    <p><strong>출력:</strong></p>
                    <pre>{result["output"]}</pre>
                    
                    <h5>평가:</h5>
                    <table>
                        <tr>
                            <th>메트릭</th>
                            <th>점수</th>
                            <th>세부 정보</th>
                        </tr>
                """
                
                for eval_item in result["evaluations"]:
                    html += f"""
                    <tr>
                        <td>{eval_item["metric"]}</td>
                        <td>{eval_item["score"]}</td>
                        <td>{json.dumps(eval_item["details"], indent=2) if eval_item["details"] else "N/A"}</td>
                    </tr>
                    """
                
                html += """
                    </table>
                </div>
                """
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        # HTML 파일 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    async def _generate_pdf_report(self, data: Dict[str, Any], output_path: str):
        """PDF 형식 보고서를 생성합니다."""
        # 임시 HTML 파일 생성
        temp_html_path = output_path.replace(".pdf", "_temp.html")
        await self._generate_html_report(data, temp_html_path)
        
        # 추후 구현: HTML을 PDF로 변환하는 라이브러리 통합 (weasyprint, wkhtmltopdf 등)
        # 임시 구현: HTML 파일을 그대로 복사
        logger.warning("PDF 변환 기능은 아직 구현되지 않았습니다. HTML 파일을 대신 생성합니다.")
        
        # 임시 HTML 파일 삭제
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        
        # 대신 HTML 파일 생성
        html_path = output_path.replace(".pdf", ".html")
        await self._generate_html_report(data, html_path)
        
        return html_path
    
    async def _generate_json_report(self, data: Dict[str, Any], output_path: str):
        """JSON 형식 보고서를 생성합니다."""
        # 직렬화 가능한 형태로 변환
        serializable_data = self._prepare_serializable_data(data)
        
        # JSON 파일 저장
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, default=str)
    
    def _prepare_serializable_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터를 JSON 직렬화 가능한 형태로 변환합니다."""
        serializable = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                serializable[key] = self._prepare_serializable_data(value)
            elif isinstance(value, list):
                serializable[key] = [
                    self._prepare_serializable_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, (datetime, )):
                # datetime 객체를 문자열로 변환
                serializable[key] = value.isoformat()
            else:
                serializable[key] = value
        
        return serializable
    
    async def export_data(
        self,
        experiment_set_id: int,
        format: str = "json",
        run_id: Optional[str] = None,
        include_results: bool = True,
        include_evaluations: bool = True,
        export_id: Optional[str] = None
    ) -> str:
        """실험 세트 데이터를 내보냅니다."""
        logger.info(f"데이터 내보내기 시작: experiment_set_id={experiment_set_id}, format={format}")
        
        # 내보내기 ID 생성
        if not export_id:
            export_id = f"export_{experiment_set_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # 내보내기 디렉토리 확인
        exports_dir = ab_testing_settings.exports_dir
        os.makedirs(exports_dir, exist_ok=True)
        
        # 데이터 수집
        data = await self._collect_export_data(
            experiment_set_id, 
            run_id, 
            include_results,
            include_evaluations
        )
        
        # 형식에 따른 내보내기
        if format.lower() == "json":
            export_path = os.path.join(exports_dir, f"{export_id}.json")
            # JSON 직렬화 가능하게 변환
            serializable_data = self._prepare_serializable_data(data)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, indent=2, default=str)
        elif format.lower() in ["csv", "xlsx"]:
            logger.warning(f"{format.upper()} 내보내기 기능은 아직 구현되지 않았습니다. JSON으로 대체합니다.")
            export_path = os.path.join(exports_dir, f"{export_id}.json")
            serializable_data = self._prepare_serializable_data(data)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, indent=2, default=str)
        else:
            raise ValueError(f"지원되지 않는 내보내기 형식: {format}")
            
        logger.info(f"데이터 내보내기 완료: path={export_path}")
        return export_path
    
    async def _collect_export_data(
        self,
        experiment_set_id: int,
        run_id: Optional[str],
        include_results: bool,
        include_evaluations: bool
    ) -> Dict[str, Any]:
        """내보내기용 데이터를 수집합니다."""
        # 보고서 데이터 수집 기능을 재사용
        data = await self._collect_report_data(experiment_set_id, run_id)
        
        # 필요 없는 데이터 필터링
        if not include_results:
            for exp in data["experiments"]:
                exp["results"] = []
        elif not include_evaluations:
            for exp in data["experiments"]:
                for result in exp["results"]:
                    result["evaluations"] = []
        
        return data