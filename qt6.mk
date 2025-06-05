COMPOSE_FILE=docker-compose-qt6.yaml

DOCKER_CMD = docker compose -f $(COMPOSE_FILE) run --rm --user `id -u`:`id -g` pyqt5_to_pyqt6

build:
	docker compose -f $(COMPOSE_FILE) build pyqt5_to_pyqt6

.PHONY: pyqt5_to_pyqt6-dry-run
pyqt5_to_pyqt6-dry-run:
	$(DOCKER_CMD) pyqt5_to_pyqt6.py --dry_run /src

bash:
	$(DOCKER_CMD) bash

bash-root:
	docker compose -f $(COMPOSE_FILE) run --rm pyqt5_to_pyqt6 bash

.PHONY: pyqt5_to_pyqt6
pyqt5_to_pyqt6:
	$(DOCKER_CMD) pyqt5_to_pyqt6.py /src
