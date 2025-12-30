import shutil
import subprocess
import sys


def main():
    """Start an Arq worker via the `arq` CLI, connecting to the `redis` host.

    Using the CLI avoids depending on the exact Python API signature of
    run_worker across arq versions.
    """
    arq_cmd = shutil.which("arq") or "arq"
    env = dict(**__import__("os").environ)
    # Set ARQ_REDIS_URL so arq CLI connects to the compose redis service
    env["ARQ_REDIS_URL"] = env.get("ARQ_REDIS_URL")
    # point the CLI to the settings class which registers functions
    args = [arq_cmd, "app.worker_settings.WorkerSettings"]
    return subprocess.call(args, env=env)


if __name__ == "__main__":
    sys.exit(main())
