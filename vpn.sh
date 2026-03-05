#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root"
  exit 1
fi

PID_FILE_PATH='/var/run/vpn.pid'
LOG_PATH='/tmp/openconnect.log'

if [[ ! -f "${HOME}/.openconnect/connection-info.env" ]]; then
  echo "Error: Configuration file not found at ${HOME}/.openconnect/connection-info.env"
  exit 1
fi

set -o allexport
source "${HOME}/.openconnect/connection-info.env"
set +o allexport

check_dependencies() {
  for cmd in openconnect-sso openconnect dig ping; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "Error: $cmd is required but not installed"
      exit 1
    fi
  done
}

validate_environment() {
  local required_vars=("HOST" "USERNAME" "PASSWORD" "AUTHGROUP" "HOSTS_TO_ROUTE")

  for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
      echo "Error: $var is not set in environment file"
      exit 1
    fi
  done
}

start() {
  check_dependencies
  validate_environment

  if ! is_network_available; then
    echo "Network is not available. Check your internet connection"
    exit 1
  fi

  if is_vpn_running; then
    echo "VPN is already running"
    exit 1
  fi

  echo "Connecting to ${HOST}"

  local auth
  # --authenticate shell outputs HOST=, COOKIE=, FINGERPRINT= to stdout
  auth=$(openconnect-sso --server "${HOST}" --user "${USERNAME}" --authgroup "${AUTHGROUP}" --authenticate shell --log-level ERROR 2>>"$LOG_PATH")

  local cookie vpn_host fingerprint
  cookie=$(echo "$auth" | grep '^COOKIE=' | cut -d= -f2- | tr -d "'")
  vpn_host=$(echo "$auth" | grep '^HOST=' | cut -d= -f2- | tr -d "'")
  fingerprint=$(echo "$auth" | grep '^FINGERPRINT=' | cut -d= -f2- | tr -d "'")

  if [[ -z "$cookie" || -z "$vpn_host" || -z "$fingerprint" ]]; then
    echo "VPN authentication failed!"
    echo "auth output: $auth" >>"$LOG_PATH"
    tail -20 "$LOG_PATH"
    exit 1
  fi

  echo "$cookie" | openconnect \
    --cookie-on-stdin \
    --servercert "$fingerprint" \
    --script "vpn-slice --no-ns-hosts --no-host-names --verbose $HOSTS_TO_ROUTE" \
    --pid-file="$PID_FILE_PATH" \
    --background \
    "$vpn_host" >>"$LOG_PATH" 2>&1

  if is_vpn_running; then
    echo "VPN is connected"
    print_current_ip_address
  else
    echo "VPN failed to connect!"
    tail -20 "$LOG_PATH"
    exit 1
  fi
}

cleanup_routes() {
  local vpn_ip
  vpn_ip=$(dig +short "$HOST" | head -1)
  if [[ -n "$vpn_ip" ]]; then
    route delete -host "$vpn_ip" >/dev/null 2>&1 || true
  fi

  for subnet in $HOSTS_TO_ROUTE; do
    route delete -net "$subnet" >/dev/null 2>&1 || true
  done
}

stop() {
  if is_vpn_running; then
    local pid
    pid=$(cat "$PID_FILE_PATH")
    kill -TERM "$pid" 2>/dev/null || true
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 5 ]]; do
      sleep 1
      ((waited++)) || true
    done
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE_PATH" >/dev/null 2>&1
  fi

  cleanup_routes

  echo "VPN is disconnected"
  print_current_ip_address
}

restart() {
  stop
  start
}

status() {
  is_vpn_running && echo "VPN is running" || echo "VPN is stopped"
}

print_info() {
  echo "Usage: $(basename "$0") (start|stop|restart|status|clean)"
}

is_network_available() {
  ping -q -c 1 -W 1 8.8.8.8 >/dev/null 2>&1
}

is_vpn_running() {
  test ! -f "$PID_FILE_PATH" && return 1
  local pid
  pid=$(cat "$PID_FILE_PATH")
  kill -0 "$pid" >/dev/null 2>&1
}

print_current_ip_address() {
  local ip
  ip=$(dig +short myip.opendns.com @resolver1.opendns.com)
  echo "Your IP address is $ip"
}

case "$1" in
start) start ;;
stop) stop ;;
status) status ;;
restart) restart ;;
clean) cleanup_routes ;;
*)
  print_info
  exit 0
  ;;
esac
