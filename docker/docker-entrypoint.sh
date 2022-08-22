#!/bin/bash

/usr/bin/Xvfb ${DISPLAY} -screen 0 1024x768x24 -ac +extension GLX +render -noreset -nolisten tcp &

exec "$@"
