#!/usr/bin/env sh

# Toggle Raspberry Pi "system is shutting down" indicator on GPIO 12.
# Usage: rpi-shutdown-indicator.sh on|off

PIN=12
STATE="${1:-}"

case "$STATE" in
  on)
    LEVEL=1
    ;;
  off)
    LEVEL=0
    ;;
  *)
    exit 0
    ;;
esac

set_with_pinctrl() {
  pinctrl set "$PIN" op
  if [ "$LEVEL" -eq 1 ]; then
    pinctrl set "$PIN" dh
  else
    pinctrl set "$PIN" dl
  fi
}

set_with_raspi_gpio() {
  if [ "$LEVEL" -eq 1 ]; then
    raspi-gpio set "$PIN" op dh
  else
    raspi-gpio set "$PIN" op dl
  fi
}

if command -v pinctrl >/dev/null 2>&1; then
  set_with_pinctrl && exit 0
fi

if command -v raspi-gpio >/dev/null 2>&1; then
  set_with_raspi_gpio && exit 0
fi

exit 0
