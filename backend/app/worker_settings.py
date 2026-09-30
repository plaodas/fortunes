from arq.connections import RedisSettings


class WorkerSettings:
    max_jobs = 1  # default: 5
    job_timeout = 1200  # CPU 上のローカル LLM は生成に数分かかることがある
    max_tries = 1

    # list of task functions the worker should register
    functions = ["app.tasks.process_analysis"]

    # connect to redis service in docker-compose
    redis_settings = RedisSettings(host="redis")
