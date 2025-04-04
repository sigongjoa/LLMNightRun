import time
import threading
import logging
import schedule
from typing import Callable, Dict, Any, List, Optional
import json
import os
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """작업 스케줄링 관리 클래스"""
    
    def __init__(self):
        """스케줄러 초기화"""
        self.running = False
        self.thread = None
        self.scheduled_tasks = {}  # 태스크 ID -> 태스크 정보 매핑
        self.task_counter = 0
        
        # 상태 파일 로드
        self._load_state()
    
    def _get_state_file_path(self) -> str:
        """상태 파일 경로를 반환합니다."""
        return os.path.join(os.path.dirname(__file__), "..", "storage", "scheduler_state.json")
    
    def _load_state(self):
        """저장된 스케줄러 상태를 로드합니다."""
        state_file = self._get_state_file_path()
        
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.task_counter = state.get("task_counter", 0)
                tasks = state.get("tasks", {})
                
                # 작업 재스케줄링
                for task_id, task_info in tasks.items():
                    if task_info.get("active", False):
                        schedule_type = task_info.get("schedule_type")
                        schedule_value = task_info.get("schedule_value")
                        
                        # 작업 유형에 따라 함수 결정
                        target_func = self._placeholder_function
                        
                        # 작업 재스케줄링
                        self._schedule_task(
                            task_id=task_id,
                            name=task_info.get("name"),
                            description=task_info.get("description"),
                            target_func=target_func,
                            schedule_type=schedule_type,
                            schedule_value=schedule_value,
                            args=task_info.get("args", []),
                            kwargs=task_info.get("kwargs", {})
                        )
                
                logger.info(f"스케줄러 상태를 로드했습니다. 작업 수: {len(self.scheduled_tasks)}")
            except Exception as e:
                logger.error(f"스케줄러 상태 로드 중 오류 발생: {str(e)}")
    
    def _save_state(self):
        """현재 스케줄러 상태를 저장합니다."""
        state_file = self._get_state_file_path()
        
        # 상태 디렉토리 확인
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        # 작업 정보 모으기 (직렬화 가능한 형태로)
        tasks = {}
        for task_id, task_info in self.scheduled_tasks.items():
            tasks[task_id] = {
                "name": task_info["name"],
                "description": task_info["description"],
                "schedule_type": task_info["schedule_type"],
                "schedule_value": task_info["schedule_value"],
                "active": task_info["active"],
                "args": task_info.get("args", []),
                "kwargs": task_info.get("kwargs", {}),
                "last_run": task_info.get("last_run")
            }
        
        state = {
            "task_counter": self.task_counter,
            "tasks": tasks,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info("스케줄러 상태를 저장했습니다.")
        except Exception as e:
            logger.error(f"스케줄러 상태 저장 중 오류 발생: {str(e)}")
    
    def _placeholder_function(self, *args, **kwargs):
        """재시작 시 작업 함수의 자리 표시자"""
        logger.warning("실제 작업 함수가 정의되지 않았습니다.")
    
    def start(self):
        """스케줄러 스레드를 시작합니다."""
        if self.running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        logger.info("스케줄러가 시작되었습니다.")
    
    def stop(self):
        """스케줄러 스레드를 중지합니다."""
        if not self.running:
            logger.warning("스케줄러가 실행 중이 아닙니다.")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("스케줄러가 중지되었습니다.")
        
        # 상태 저장
        self._save_state()
    
    def _run_scheduler(self):
        """스케줄러 메인 루프를 실행합니다."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _task_wrapper(self, task_id: str, func: Callable, *args, **kwargs):
        """
        작업 실행 래퍼 함수
        
        Args:
            task_id: 작업 ID
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
        """
        try:
            logger.info(f"작업 실행 시작: {task_id}")
            
            # 작업 실행
            result = func(*args, **kwargs)
            
            # 마지막 실행 시간 업데이트
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id]["last_run"] = datetime.utcnow().isoformat()
                self.scheduled_tasks[task_id]["last_result"] = "성공"
            
            logger.info(f"작업 실행 완료: {task_id}")
            return result
        except Exception as e:
            logger.error(f"작업 실행 중 오류 발생: {task_id}, {str(e)}")
            
            # 오류 정보 업데이트
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id]["last_result"] = f"실패: {str(e)}"
            
            # 상태 저장
            self._save_state()
            
            # 예외 재발생
            raise
    
    def _schedule_task(
        self,
        task_id: str,
        name: str,
        description: str,
        target_func: Callable,
        schedule_type: str,
        schedule_value: Any,
        args: List = None,
        kwargs: Dict = None
    ):
        """
        스케줄러에 작업을 등록합니다.
        
        Args:
            task_id: 작업 ID
            name: 작업 이름
            description: 작업 설명
            target_func: 실행할 함수
            schedule_type: 스케줄 유형 ('interval', 'daily', 'weekly')
            schedule_value: 스케줄 값 (간격(초) 또는 시각)
            args: 함수 인자 (선택 사항)
            kwargs: 함수 키워드 인자 (선택 사항)
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        
        # 래핑된 작업 생성
        job_func = lambda: self._task_wrapper(task_id, target_func, *args, **kwargs)
        
        # 작업 스케줄링
        if schedule_type == 'interval':
            # 초 단위 간격으로 실행
            interval_seconds = int(schedule_value)
            job = schedule.every(interval_seconds).seconds.do(job_func)
        elif schedule_type == 'daily':
            # 매일 특정 시간에 실행
            job = schedule.every().day.at(schedule_value).do(job_func)
        elif schedule_type == 'weekly':
            # 매주 특정 요일과 시간에 실행
            day, time = schedule_value.split('/')
            day = day.lower()
            
            if day == 'monday':
                job = schedule.every().monday.at(time).do(job_func)
            elif day == 'tuesday':
                job = schedule.every().tuesday.at(time).do(job_func)
            elif day == 'wednesday':
                job = schedule.every().wednesday.at(time).do(job_func)
            elif day == 'thursday':
                job = schedule.every().thursday.at(time).do(job_func)
            elif day == 'friday':
                job = schedule.every().friday.at(time).do(job_func)
            elif day == 'saturday':
                job = schedule.every().saturday.at(time).do(job_func)
            elif day == 'sunday':
                job = schedule.every().sunday.at(time).do(job_func)
            else:
                raise ValueError(f"잘못된 요일: {day}")
        else:
            raise ValueError(f"지원되지 않는 스케줄 유형: {schedule_type}")
        
        # 작업 정보 저장
        self.scheduled_tasks[task_id] = {
            "name": name,
            "description": description,
            "schedule_type": schedule_type,
            "schedule_value": schedule_value,
            "job": job,
            "active": True,
            "args": args,
            "kwargs": kwargs,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 상태 저장
        self._save_state()
    
    def schedule_task(
        self,
        name: str,
        description: str,
        target_func: Callable,
        schedule_type: str,
        schedule_value: Any,
        args: List = None,
        kwargs: Dict = None
    ) -> str:
        """
        새 작업을 스케줄링합니다.
        
        Args:
            name: 작업 이름
            description: 작업 설명
            target_func: 실행할 함수
            schedule_type: 스케줄 유형 ('interval', 'daily', 'weekly')
            schedule_value: 스케줄 값 (간격(초) 또는 시각)
            args: 함수 인자 (선택 사항)
            kwargs: 함수 키워드 인자 (선택 사항)
            
        Returns:
            생성된 작업 ID
        """
        if not self.running:
            raise RuntimeError("스케줄러가 실행 중이 아닙니다. 먼저 start() 메서드를 호출하세요.")
        
        # 작업 ID 생성
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        # 작업 스케줄링
        self._schedule_task(
            task_id=task_id,
            name=name,
            description=description,
            target_func=target_func,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            args=args,
            kwargs=kwargs
        )
        
        return task_id
    
    def unschedule_task(self, task_id: str) -> bool:
        """
        작업을 스케줄러에서 제거합니다.
        
        Args:
            task_id: 작업 ID
            
        Returns:
            성공 여부를 나타내는 불리언 값
        """
        if task_id not in self.scheduled_tasks:
            logger.warning(f"작업을 찾을 수 없습니다: {task_id}")
            return False
        
        task_info = self.scheduled_tasks[task_id]
        
        # 스케줄러에서 작업 취소
        schedule.cancel_job(task_info["job"])
        
        # 작업 비활성화 표시
        task_info["active"] = False
        
        # 상태 저장
        self._save_state()
        
        return True
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 태스크 정보를 반환합니다.
        
        Returns:
            태스크 ID별 태스크 정보 매핑
        """
        result = {}
        
        for task_id, task_info in self.scheduled_tasks.items():
            # 직렬화 가능한 정보만 포함
            result[task_id] = {
                "name": task_info["name"],
                "description": task_info["description"],
                "schedule_type": task_info["schedule_type"],
                "schedule_value": task_info["schedule_value"],
                "active": task_info["active"],
                "created_at": task_info.get("created_at"),
                "last_run": task_info.get("last_run"),
                "last_result": task_info.get("last_result")
            }
        
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        특정 태스크 정보를 반환합니다.
        
        Args:
            task_id: 작업 ID
            
        Returns:
            태스크 정보 또는 None (존재하지 않는 경우)
        """
        if task_id not in self.scheduled_tasks:
            return None
        
        task_info = self.scheduled_tasks[task_id]
        
        return {
            "name": task_info["name"],
            "description": task_info["description"],
            "schedule_type": task_info["schedule_type"],
            "schedule_value": task_info["schedule_value"],
            "active": task_info["active"],
            "created_at": task_info.get("created_at"),
            "last_run": task_info.get("last_run"),
            "last_result": task_info.get("last_result")
        }

# 싱글톤 인스턴스
_scheduler_instance = None

def get_scheduler() -> TaskScheduler:
    """
    스케줄러 인스턴스를 가져옵니다. (싱글톤 패턴)
    
    Returns:
        TaskScheduler 인스턴스
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    
    return _scheduler_instance