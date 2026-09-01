# NEXUS x CCOS production image
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NEXUS_HOME=/nexus \
    NEXUS_DATA=/nexus/data \
    PYTHONPATH=/opt/nexus

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin nexus

WORKDIR /opt/nexus

COPY deploy/docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY ccos /opt/nexus/ccos
COPY apps /opt/nexus/apps
COPY contracts /opt/nexus/contracts
COPY schemas /opt/nexus/schemas
COPY scripts /opt/nexus/scripts
COPY evals /opt/nexus/evals

RUN mkdir -p /nexus/data/workflows /nexus/logs \
    && chown -R nexus:nexus /nexus /opt/nexus

USER nexus
WORKDIR /opt/nexus
EXPOSE 8080
VOLUME ["/nexus"]
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "-m", "apps.launcher", "start", "--interval", "10"]
