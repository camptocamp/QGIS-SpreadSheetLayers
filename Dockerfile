FROM camptocamp/qgis-server:3.22-desktop

RUN pip3 install \
    psycopg2-binary \
    pydevd \
    pyyaml

RUN mkdir -p /app /home/user \
    && chmod 777 /home/user

# Keep QGIS settings in a volume
RUN mkdir -p /home/user/.local/share/QGIS/QGIS3/profiles/default \
    && chmod -R 777 /home/user/.local
VOLUME /home/user/.local/share/QGIS/QGIS3/profiles/default

ENV HOME=/home/user
