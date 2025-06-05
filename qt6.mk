export COMPOSE_FILE=docker-compose-qt6.yaml

include Makefile

PYQT5_to_PYQT6_DOCKER_RUN_CMD = docker compose run --rm --user `id -u`:`id -g` pyqt5_to_pyqt6

.PHONY: pyqt5-to-pyqt6-dry-run
pyqt5-to-pyqt6-dry-run:
	$(PYQT5_to_PYQT6_DOCKER_RUN_CMD) pyqt5_to_pyqt6.py --dry_run /src

.PHONY: pyqt5-to-pyqt6
pyqt5-to-pyqt6:
	$(PYQT5_to_PYQT6_DOCKER_RUN_CMD) pyqt5_to_pyqt6.py /src
