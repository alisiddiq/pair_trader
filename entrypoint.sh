#!/bin/bash
set -e

echo "Running entry point script"

case "$1" in
default)
  echo "Running Webapp"
   gunicorn -b 0.0.0.0:5000 webapp.start_app:server -k gevent --timeout 600 --workers 4
  ;;
*)
  exec "$@"
  ;;
esac