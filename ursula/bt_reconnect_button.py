#!/usr/bin/env python3
from signal import pause
import subprocess

from gpiozero import Button


def reconnect() -> None:
    subprocess.run(["systemctl", "start", "bt-reconnect.service"], check=False)


button = Button(26, pull_up=True, bounce_time=0.2)
button.when_pressed = reconnect
pause()
