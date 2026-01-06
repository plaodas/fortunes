# app/services/job_service.py
import json
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job


def _safe_serialize(obj: Any) -> Any:
    """Return a JSON-serializable representation of obj.

    - If obj is an exception, return its type and message.
    - If obj is already JSON-serializable, return it as-is.
    - Otherwise, return its string representation.
    """
    if isinstance(obj, BaseException):
        return {"error_type": type(obj).__name__, "error": str(obj)}
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return repr(obj)


class JobService:
    def __init__(self, host: str = "redis"):
        self.host = host

    # TODO: job_id と user_id を照合して、他ユーザーのジョブ状況を取得できないようにする
    async def enqueue_analysis(self, *args: Any):
        pool = await create_pool(RedisSettings(host=self.host))
        try:
            job = await pool.enqueue_job("app.tasks.process_analysis", *args)
            return job
        finally:
            await pool.aclose()

    async def get_job_status(self, job_id: str):
        pool = await create_pool(RedisSettings(host=self.host))
        try:
            job = Job(job_id, pool)
            status = await job.status()

            result = None
            try:
                info = await job.result_info()
                if info:
                    result = _safe_serialize(info.result)
            except Exception:
                pass

            return {"status": str(status), "result": result}
        finally:
            await pool.aclose()
