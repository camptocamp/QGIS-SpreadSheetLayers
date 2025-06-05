# Arguments to customize build

FROM ghcr.io/qgis/qgis-qt6-unstable:main

LABEL org.opencontainers.image.title="PyQGIS 4 Checker image" \
    org.opencontainers.image.description="QGIS based on Qt6 with the PyQGIS migration script" \
    org.opencontainers.image.source="https://github.com/qgis/pyqgis4-checker" \
    org.opencontainers.image.licenses="GPL-2.0-or-later"

USER root

# TEMPORARY: GET THE LATEST SCRIPT VERSION WAITING FOR SOURCE IMAGE TO BE UPDATED
# COPY --from=build /root/QGIS/scripts/pyqt5_to_pyqt6/* /usr/local/bin/
ADD --chmod=755 https://github.com/qgis/QGIS/raw/refs/heads/master/scripts/pyqt5_to_pyqt6/pyqt5_to_pyqt6.py /usr/local/bin/

# # Create non-root user dedicated to PyQGIS development
# # -m -> Create the user's home directory
# # -s /bin/bash -> Set as the user's
# RUN sudo useradd -ms /bin/bash pyqgisdev \
#     && sudo groupadd -f wheel \
#     && sudo usermod -aG wheel pyqgisdev
# USER pyqgisdev
# WORKDIR /home/pyqgisdev

# Install required dependencies
RUN sudo dnf install --nodocs --refresh -y python3-pip python3-wheel \
    # Python packages
    && python3 -m pip install --no-cache-dir --upgrade astpretty tokenize-rt \
    && sudo dnf -y remove python3-pip python3-wheel \
    # clean up
    && sudo dnf autoremove -y \
    && sudo dnf clean all \
    && sudo rm -rf /var/cache/dnf/*

# Expose the conversion script as entrypoint - disabled to make it inspectable with an interactive run
# ENTRYPOINT [ "/usr/local/bin/pyqt5_to_pyqt6.py" ]
