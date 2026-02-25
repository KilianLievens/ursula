.PHONY: dev-install
dev-install:
	poetry install --only=dev

.PHONY: lint
lint: dev-install
	poetry run black . --extend-exclude="ursula/lib"

# SOURCE
example.py:
	wget https://raw.githubusercontent.com/waveshareteam/e-Paper/refs/heads/master/RaspberryPi_JetsonNano/python/examples/epd_7in5_V2_test.py -O example.py

original_epdconfig.py:
	wget https://github.com/waveshareteam/e-Paper/raw/refs/heads/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epdconfig.py -O original_epdconfig.py

requirements.txt:
	poetry export --without-hashes --format=requirements.txt > requirements.txt

# PATCHES
epdconfig.patch: original_epdconfig.py
	diff -u original_epdconfig.py ursula/lib/epdconfig.py > epdconfig.patch || :

# LIB
ursula/lib/epd.py:
	wget https://raw.githubusercontent.com/waveshareteam/e-Paper/refs/heads/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd7in5_V2.py -O ursula/lib/epd.py

ursula/lib/epdconfig.py: original_epdconfig.py
	patch original_epdconfig.py --output ursula/lib/epdconfig.py < epdconfig.patch

ursula/lib/font.ttc:
	wget https://github.com/waveshareteam/e-Paper/raw/refs/heads/master/RaspberryPi_JetsonNano/python/pic/Font.ttc -O ursula/lib/font.ttc

ursula/lib/DEV_Config_64.so:
	wget https://github.com/waveshareteam/e-Paper/raw/refs/heads/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/DEV_Config_64.so -O ursula/lib/DEV_Config_64.so

.PHONY: deps
deps: ursula/lib/epd.py ursula/lib/epdconfig.py ursula/lib/font.ttc ursula/lib/DEV_Config_64.so
	echo 'Done.'

.PHONY: rsync
rsync:
	rsync -azvhP ./ kilian@ursula.local:/home/kilian/ursula --exclude .git --filter=':- .gitignore'

.PHONY: run
run: rsync
	ssh kilian@ursula.local -t "cd /home/kilian/ursula && sudo PYTHONPATH='/home/kilian/ursula' .venv/bin/python ./ursula/main.py eink"

.PHONY: run-colemak
run-colemak: rsync
	ssh kilian@ursula.local -t "cd /home/kilian/ursula && sudo PYTHONPATH='/home/kilian/ursula' .venv/bin/python ./ursula/main.py eink colemak"

.PHONY: r-venv
r-venv:
	ssh kilian@ursula.local -t "cd /home/kilian/ursula && [ -d .venv ] || python -m venv .venv"

.PHONY: r-install
r-install: r-venv requirements.txt rsync
	ssh kilian@ursula.local -t "cd /home/kilian/ursula && .venv/bin/pip install -r requirements.txt"
	rm requirements.txt

.PHONY: r-clear
r-clear:
	ssh kilian@ursula.local -t "rm -rf ursula && mkdir ursula"

.PHONY: r-setup
r-setup: rsync r-gpio-shutdown
	ssh kilian@ursula.local -t "sudo ln -sf /home/kilian/ursula/90-btkbd.rules /etc/udev/rules.d/90-btkbd.rules"
	ssh kilian@ursula.local -t "sudo ln -sf /home/kilian/ursula/ursula.service /etc/systemd/system/ursula.service"
	ssh kilian@ursula.local -t "sudo ln -sf /home/kilian/ursula/bt-reconnect.service /etc/systemd/system/bt-reconnect.service"
	ssh kilian@ursula.local -t "sudo ln -sf /home/kilian/ursula/bt-reconnect.timer /etc/systemd/system/bt-reconnect.timer"
	ssh kilian@ursula.local -t "sudo udevadm control --reload-rules"
	ssh kilian@ursula.local -t "sudo systemctl daemon-reload"
	ssh kilian@ursula.local -t "sudo systemctl enable bt-reconnect.timer"
	ssh kilian@ursula.local -t "sudo systemctl start bt-reconnect.timer"

.PHONY: r-gpio-shutdown
r-gpio-shutdown:
	ssh kilian@ursula.local -t "sudo sh -c \"if grep -qxF 'dtoverlay=gpio-shutdown,gpio_pin=4' /boot/firmware/config.txt; then exit 0; fi; if grep -qxF 'dtoverlay=gpio-shutdown' /boot/firmware/config.txt; then sed -i \"s/^dtoverlay=gpio-shutdown$$/dtoverlay=gpio-shutdown,gpio_pin=4/\" /boot/firmware/config.txt; else { echo '# Power button: GPIO pin 4 triggers clean shutdown'; echo 'dtoverlay=gpio-shutdown,gpio_pin=4'; } >> /boot/firmware/config.txt; fi\""
