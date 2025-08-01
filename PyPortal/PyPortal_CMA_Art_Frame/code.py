# SPDX-FileCopyrightText: 2020 Dan Cogliano for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from os import getenv
import time
import random
import board
from adafruit_pyportal import PyPortal
from adafruit_display_shapes.circle import Circle

WIDTH = board.DISPLAY.width
HEIGHT = board.DISPLAY.height

# Get WiFi details and Adafruit IO keys, ensure these are setup in settings.toml
# (visit io.adafruit.com if you need to create an account, or if you need your Adafruit IO key.)
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
aio_username = getenv("ADAFRUIT_AIO_USERNAME")
aio_key = getenv("ADAFRUIT_AIO_KEY")

if None in [ssid, password, aio_username, aio_key]:
    raise RuntimeError(
        "WiFi and Adafruit IO settings are kept in settings.toml, "
        "please add them there. The settings file must contain "
        "'CIRCUITPY_WIFI_SSID', 'CIRCUITPY_WIFI_PASSWORD', "
        "'ADAFRUIT_AIO_USERNAME' and 'ADAFRUIT_AIO_KEY' at a minimum."
    )

#pylint: disable=line-too-long

# these lines show the entire collection
APIURL = "https://openaccess-api.clevelandart.org/api/artworks?cc0=1&has_image=1&indent=2&limit=1&skip="
IMAGECOUNT = 31954

# uncomment these lines to show just paintings
# APIURL = "https://openaccess-api.clevelandart.org/api/artworks?cc0=1&has_image=1&indent=2&limit=1&type=Painting&skip="
# IMAGECOUNT = 3223

BACKGROUND_FILE = "/background.bmp"
if WIDTH > 320:
    BACKGROUND_FILE = "/background_480.bmp"

pyportal = PyPortal(default_bg=BACKGROUND_FILE,
                    image_json_path=["data", 0, "images", "web", "url"],
                    image_dim_json_path=(["data", 0, "images", "web", "width"],
                                         ["data", 0, "images", "web", "height"]),
                    image_resize=(WIDTH, HEIGHT - 15),
                    image_position=(0, 0),
                    text_font="/fonts/OpenSans-9.bdf",
                    json_path=["data", 0, "title"],
                    text_position=(4, HEIGHT - 9),
                    text_color=0xFFFFFF)

circle = Circle(WIDTH - 8, HEIGHT - 7, 5, fill=0)
pyportal.root_group.append(circle)
loopcount = 0
errorcount = 0
while True:
    response = None
    try:
        circle.fill = 0xFF0000
        itemid = random.randint(1, IMAGECOUNT)
        # itemid = 20 # portrait mode example
        # itemid = 21 # landscape mode example
        print("retrieving url:", APIURL + str(itemid))
        response = pyportal.fetch(APIURL + str(itemid))
        circle.fill = 0
        print("Response is", response)
        loopcount = loopcount + 1

    except (RuntimeError, KeyError, TypeError) as e:
        print("An error occured, retrying! -", e)
        print("loop counter:", loopcount)
        assert errorcount < 20, "Too many errors, stopping"
        errorcount = errorcount + 1
        time.sleep(60)
        continue

    errorcount = 0
    stamp = time.monotonic()
    # wait 5 minutes before getting again
    while (time.monotonic() - stamp) < (5*60):
        # or, if they touch the screen, fetch immediately!
        if pyportal.touchscreen.touch_point:
            break
