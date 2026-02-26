#!/usr/bin/env sh

# Toggle Bluetooth keyboard status LED on GPIO 6.
# Usage: bt-kbd-led.sh on|off

STATE="${1:-}"

case "$STATE" in
  on)
    LEVEL_HIGH=1
    ;;
  off)
    LEVEL_HIGH=0
    ;;
  *)
    exit 0
    ;;
esac

set_with_sysfs() {
  [ -d /sys/class/gpio/gpio6 ] || echo 6 > /sys/class/gpio/export
  echo out > /sys/class/gpio/gpio6/direction
  if [ "$LEVEL_HIGH" -eq 1 ]; then
    echo 1 > /sys/class/gpio/gpio6/value
  else
    echo 0 > /sys/class/gpio/gpio6/value
  fi
}

if [ -w /sys/class/gpio/export ]; then
  set_with_sysfs || true
fi

exit 0
