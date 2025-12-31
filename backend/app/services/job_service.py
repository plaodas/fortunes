# app/services/job_service.py
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job


class JobService:
    def __init__(self, host: str = "redis"):
        self.host = host

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
                    result = info.result
            except Exception:
                pass

            return {"status": str(status), "result": result}
        finally:
            await pool.aclose()
