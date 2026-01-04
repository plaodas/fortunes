from arq.connections import RedisSettings


class WorkerSettings:
    max_jobs = 1  # default: 5

    # list of task functions the worker should register
    functions = ["app.tasks.process_analysis"]

    # connect to redis service in docker-compose
    redis_settings = RedisSettings(host="redis")
