#!/usr/bin/env bash
MAC="29:27:3C:65:60:D3"
if ! bluetoothctl info "$MAC" | grep -q "Connected: yes"; then
      bluetoothctl connect "$MAC"
fi
