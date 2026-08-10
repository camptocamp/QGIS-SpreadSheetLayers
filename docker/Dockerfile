ARG QGIS_VERSION=4.2
FROM qgis/qgis:${QGIS_VERSION}

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        curl \
        git \
        make \
        pyqt5-dev-tools \
        qttools5-dev-tools \
        rsync

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --break-system-packages --requirement=/tmp/requirements-dev.txt

RUN curl -L -o /tmp/tx-linux-amd64.tar.gz https://github.com/transifex/cli/releases/download/v1.6.7/tx-linux-amd64.tar.gz \
    && tar -C /usr/local/bin -xf /tmp/tx-linux-amd64.tar.gz tx \
    && chmod +x /usr/local/bin/tx \
    && rm -f /tmp/tx-linux-amd64.tar.gz

RUN mkdir -p /app /home/user \
    && chmod 777 /home/user

# Mounted as a volume by docker-compose to keep QGIS settings between runs.
# QGIS creates the QGIS3/ or QGIS4/ subdirectory itself, so settings of
# several QGIS versions can coexist in the same volume.
RUN mkdir -p /home/user/.local/share/QGIS \
    && chmod -R 777 /home/user/.local

WORKDIR /app

ENV DISPLAY=:99 \
    HOME=/home/user

RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
COPY /docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["pytest"]
