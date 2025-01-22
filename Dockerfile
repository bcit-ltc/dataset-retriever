FROM python:3.13.1-slim AS base
LABEL org.opencontainers.image.source https://github.com/BCIT-LTC/dataset-retriever
ENV PYTHONUNBUFFERED=1
ENV PATH=/code:/opt/venv/bin:$PATH

RUN set -ex; \
        apt-get update; \
        apt-get install -y --no-install-recommends \
                build-essential \
                libmemcached-dev \
                zlib1g-dev;

COPY requirements.txt ./

RUN set -ex; \
        python -m venv /opt/venv; \
        pip install --upgrade pip; \
        pip install -r requirements.txt;

# ============================================ Release

FROM python:3.13.1-slim AS release
ENV PYTHONUNBUFFERED=1
ENV PATH=/code:/opt/venv/bin:$PATH
WORKDIR /code
ARG VERSION
ENV VERSION=${VERSION:-1.0.0}
RUN echo $VERSION > .env

# RUN set -ex; \
#         apt-get update; \
#         apt-get install -y --no-install-recommends \
#             ffmpeg \
#             curl \ 
#             gpg;



COPY --from=base /root/.cache /root/.cache
COPY --from=base /opt/venv /opt/venv

# COPY manage.py ./
COPY docker-entrypoint.sh /usr/local/bin

# COPY api api

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

EXPOSE 9000

# CMD ["tail", "-f", "/dev/null"]

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:9000", "--forwarded-allow-ips=*", \
"--log-level", "info", "--timeout", "120", "--graceful-timeout", "120", "retriever.wsgi"]
