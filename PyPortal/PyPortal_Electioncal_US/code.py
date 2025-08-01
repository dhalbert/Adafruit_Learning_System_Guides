# SPDX-FileCopyrightText: 2020 Alvaro Figueroa for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from os import getenv
import sys
import time
import board
from adafruit_pyportal import PyPortal
cwd = ("/"+__file__).rsplit('/', 1)[0] # the current working directory (where this file is)
sys.path.append(cwd)
import electioncal_graphics  # pylint: disable=wrong-import-position

# Get WiFi details, ensure these are setup in settings.toml
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

if None in [ssid, password]:
    raise RuntimeError(
        "WiFi settings are kept in settings.toml, "
        "please add them there. The settings file must contain "
        "'CIRCUITPY_WIFI_SSID', 'CIRCUITPY_WIFI_PASSWORD', "
        "at a minimum."
    )

# Change this to your state and county, replacing spaces for underscores and in lowercase
STATE="new_york"
COUNTY="new_york"

DATA_SOURCE = "https://electioncal.us/en/" + STATE +"/" + COUNTY + "/voter.json"
DATA_LOCATION = []

# Initialize the pyportal object and let us know what data to fetch and where
# to display it
pyportal = PyPortal(url=DATA_SOURCE,
                    json_path=DATA_LOCATION,
                    status_neopixel=board.NEOPIXEL,
                    default_bg=0x000000)


gfx = electioncal_graphics.Electioncal_Graphics(pyportal.root_group, am_pm=True)
display_refresh = None
while True:
    # only query the online time once per hour (and on first run)
    if (not display_refresh) or (time.monotonic() - display_refresh) > 3600:
        try:
            print("Getting time from internet!")
            pyportal.get_local_time()
            display_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

        try:
            value = pyportal.fetch()
            #print("Response is", value)
            gfx.load_data(value)
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue
    try:
        gfx.elections_cycle()
    except RuntimeError as e:
        print("Some error ocurred, retrying! -", e)
        continue
