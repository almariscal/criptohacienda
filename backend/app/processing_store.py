import threading
from typing import Callable, Dict, Optional

from .models import ProcessingJob


class ProcessingStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, ProcessingJob] = {}
        self._lock = threading.Lock()

    def set(self, job_id: str, job: ProcessingJob) -> None:
        with self._lock:
            self._jobs[job_id] = job

    def get(self, job_id: str) -> Optional[ProcessingJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, updater: Callable[[ProcessingJob], None]) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            updater(job)


processing_store = ProcessingStore()
