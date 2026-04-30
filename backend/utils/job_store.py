"""
File-backed job store. Each job is persisted as data/jobs/<job_id>.json
so backend restarts don't lose job state.
"""
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class JobStore:
    def __init__(self, jobs_dir: str):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        p = self._path(job_id)
        if not p.exists():
            return None
        with open(p) as f:
            return json.load(f)

    def set(self, job_id: str, data: Dict[str, Any]) -> None:
        with open(self._path(job_id), "w") as f:
            json.dump(data, f, default=str)

    def update(self, job_id: str, updates: Dict[str, Any]) -> None:
        job = self.get(job_id) or {}
        job.update(updates)
        self.set(job_id, job)

    def __contains__(self, job_id: str) -> bool:
        return self._path(job_id).exists()
