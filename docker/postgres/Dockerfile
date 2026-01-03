FROM postgres:15

# Install locales and generate ja_JP.UTF-8 for database creation
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && localedef -i ja_JP -f UTF-8 ja_JP.UTF-8 || true \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=ja_JP.UTF-8
