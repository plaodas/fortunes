from arq.connections import RedisSettings


class WorkerSettings:
    # list of task functions the worker should register
    functions = ["app.tasks.process_analysis"]

    # connect to redis service in docker-compose
    redis_settings = RedisSettings(host="redis")
