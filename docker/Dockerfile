FROM camptocamp/qgis-server:3.22-desktop

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        git \
        make \
        pyqt5-dev-tools \
        qttools5-dev-tools

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=/tmp/requirements-dev.txt

RUN curl -L -o /tmp/tx-linux-amd64.tar.gz https://github.com/transifex/cli/releases/download/v1.6.7/tx-linux-amd64.tar.gz \
    && tar -C /usr/local/bin -xf /tmp/tx-linux-amd64.tar.gz tx \
    && chmod +x /usr/local/bin/tx \
    && rm -f /tmp/tx-linux-amd64.tar.gz

RUN mkdir -p /app /home/user \
    && chmod 777 /home/user

# Keep QGIS settings in a volume
RUN mkdir -p /home/user/.local/share/QGIS/QGIS3/profiles/default \
    && chmod -R 777 /home/user/.local
VOLUME /home/user/.local/share/QGIS/QGIS3/profiles/default

WORKDIR /app

ENV DISPLAY=:99 \
    HOME=/home/user

RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
COPY /docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["pytest"]
