#!/usr/bin/env bash
# Shared logging helpers, sourced by backend/run.sh and frontend/run.sh.
# Colors are used only when stdout is a terminal and NO_COLOR is unset.

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  _DIM=$'\033[2m'; _RED=$'\033[31m'; _GREEN=$'\033[32m'; _YELLOW=$'\033[33m'; _BLUE=$'\033[34m'; _RESET=$'\033[0m'
else
  _DIM=""; _RED=""; _GREEN=""; _YELLOW=""; _BLUE=""; _RESET=""
fi

_log() { # level color message...
  local level=$1 color=$2; shift 2
  printf '%s%s%s %s%-5s%s [%s] %s\n' "$_DIM" "$(date +%H:%M:%S)" "$_RESET" "$color" "$level" "$_RESET" "${LOG_TAG:-run}" "$*"
}
info()  { _log INFO  "$_BLUE"   "$@"; }
ok()    { _log OK    "$_GREEN"  "$@"; }
warn()  { _log WARN  "$_YELLOW" "$@" >&2; }
error() { _log ERROR "$_RED"    "$@" >&2; }
die()   { error "$@"; _DIED=1; exit 1; }

require() { # command, install hint
  command -v "$1" >/dev/null 2>&1 || die "'$1' is not installed. $2"
}

on_exit() { # installed via trap; reports how the process ended
  local code=$?
  [ -n "${_DIED:-}" ] && return
  if [ "$code" -eq 0 ] || [ "$code" -eq 130 ] || [ "$code" -eq 143 ]; then
    info "Stopped"
  else
    error "Exited with code $code"
  fi
}
