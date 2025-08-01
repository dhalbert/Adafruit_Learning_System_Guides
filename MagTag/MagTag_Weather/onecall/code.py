# SPDX-FileCopyrightText: 2020 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# pylint: disable=redefined-outer-name, eval-used, wrong-import-order

from os import getenv
import time
import terminalio
import displayio
import adafruit_imageload
from adafruit_display_text import label
from adafruit_magtag.magtag import MagTag

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

# --| USER CONFIG |--------------------------
METRIC = False  # set to True for metric units
# -------------------------------------------

# ----------------------------
# Define various assets
# ----------------------------
BACKGROUND_BMP = "/bmps/weather_bg.bmp"
ICONS_LARGE_FILE = "/bmps/weather_icons_70px.bmp"
ICONS_SMALL_FILE = "/bmps/weather_icons_20px.bmp"
ICON_MAP = ("01", "02", "03", "04", "09", "10", "11", "13", "50")
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
magtag = MagTag()

# ----------------------------
# Backgrounnd bitmap
# ----------------------------
magtag.graphics.set_background(BACKGROUND_BMP)

# ----------------------------
# Weather icons sprite sheet
# ----------------------------
icons_large_bmp, icons_large_pal = adafruit_imageload.load(ICONS_LARGE_FILE)
icons_small_bmp, icons_small_pal = adafruit_imageload.load(ICONS_SMALL_FILE)

# /////////////////////////////////////////////////////////////////////////


def get_data_source_url(api="onecall", location=None):
    """Build and return the URL for the OpenWeather API."""
    if api.upper() == "GEO":
        URL = "https://api.openweathermap.org/geo/1.0/direct?q="
        URL += location
    elif api.upper() == "GEOREV":
        URL = "https://api.openweathermap.org/geo/1.0/reverse?limit=1"
        URL += "&lat={}".format(location[0])
        URL += "&lon={}".format(location[1])
    elif api.upper() == "ONECALL":
        URL = "https://api.openweathermap.org/data/2.5/onecall?exclude=minutely,hourly,alerts"
        URL += "&lat={}".format(location[0])
        URL += "&lon={}".format(location[1])
    else:
        raise ValueError("Unknown API type: " + api)
    return URL + "&appid=" + getenv("openweather_token")


def get_latlon(city_name):
    """Use the Geolocation API to determine lat/lon for given city."""
    magtag.url = get_data_source_url(api="geo", location=city_name)
    raw_data = eval(magtag.fetch())[0]
    return raw_data["lat"], raw_data["lon"]


def get_city(latlon_location):
    """Use the Geolocation API to determine city for given lat/lon."""
    magtag.url = get_data_source_url(api="georev", location=latlon_location)
    raw_data = eval(magtag.fetch())[0]
    return raw_data["name"] + ", " + raw_data["country"]


def get_forecast(location):
    """Use OneCall API to fetch forecast and timezone data."""
    resp = magtag.network.fetch(get_data_source_url(api="onecall", location=location))
    json_data = resp.json()
    return json_data["daily"], json_data["current"]["dt"], json_data["timezone_offset"]


def make_banner(x=0, y=0):
    """Make a single future forecast info banner group."""
    day_of_week = label.Label(terminalio.FONT, text="DAY", color=0x000000)
    day_of_week.anchor_point = (0, 0.5)
    day_of_week.anchored_position = (0, 10)

    icon = displayio.TileGrid(
        icons_small_bmp,
        pixel_shader=icons_small_pal,
        x=25,
        y=0,
        width=1,
        height=1,
        tile_width=20,
        tile_height=20,
    )

    day_temp = label.Label(terminalio.FONT, text="+100F", color=0x000000)
    day_temp.anchor_point = (0, 0.5)
    day_temp.anchored_position = (50, 10)

    group = displayio.Group(x=x, y=y)
    group.append(day_of_week)
    group.append(icon)
    group.append(day_temp)

    return group


def temperature_text(tempK):
    if METRIC:
        return "{:3.0f}C".format(tempK - 273.15)
    else:
        return "{:3.0f}F".format(32.0 + 1.8 * (tempK - 273.15))


def wind_text(speedms):
    if METRIC:
        return "{:3.0f}m/s".format(speedms)
    else:
        return "{:3.0f}mph".format(2.23694 * speedms)


def update_banner(banner, data):
    """Update supplied forecast banner with supplied data."""
    banner[0].text = DAYS[time.localtime(data["dt"]).tm_wday][:3].upper()
    banner[1][0] = ICON_MAP.index(data["weather"][0]["icon"][:2])
    banner[2].text = temperature_text(data["temp"]["day"])


def update_today(data, tz_offset=0):
    """Update today info banner."""
    date = time.localtime(data["dt"])
    sunrise = time.localtime(data["sunrise"] + tz_offset)
    sunset = time.localtime(data["sunset"] + tz_offset)

    today_date.text = "{} {} {}, {}".format(
        DAYS[date.tm_wday].upper(),
        MONTHS[date.tm_mon - 1].upper(),
        date.tm_mday,
        date.tm_year,
    )
    today_icon[0] = ICON_MAP.index(data["weather"][0]["icon"][:2])
    today_morn_temp.text = temperature_text(data["temp"]["morn"])
    today_day_temp.text = temperature_text(data["temp"]["day"])
    today_night_temp.text = temperature_text(data["temp"]["night"])
    today_humidity.text = "{:3d}%".format(data["humidity"])
    today_wind.text = wind_text(data["wind_speed"])
    today_sunrise.text = "{:2d}:{:02d} AM".format(sunrise.tm_hour, sunrise.tm_min)
    today_sunset.text = "{:2d}:{:02d} PM".format(sunset.tm_hour - 12, sunset.tm_min)


def go_to_sleep(current_time):
    """Enter deep sleep for time needed."""
    # compute current time offset in seconds
    hour, minutes, seconds = time.localtime(current_time)[3:6]
    seconds_since_midnight = 60 * (hour * 60 + minutes) + seconds
    three_fifteen = (3 * 60 + 15) * 60
    # wake up 15 minutes after 3am
    seconds_to_sleep = (24 * 60 * 60 - seconds_since_midnight) + three_fifteen
    print(
        "Sleeping for {} hours, {} minutes".format(
            seconds_to_sleep // 3600, (seconds_to_sleep // 60) % 60
        )
    )
    magtag.exit_and_deep_sleep(seconds_to_sleep)


# ===========
# Location
# ===========
openweather_location = getenv("openweather_location")
is_lat_long = "," in openweather_location
if openweather_location and not is_lat_long:
    # Get lat/lon using city name
    city = openweather_location
    print("Getting lat/lon for city:", city)
    latlon = get_latlon(city)
elif openweather_location:
    # Get city name using lat/lon
    latlon = openweather_location.split(",")
    print("Getting city name for lat/lon:", latlon)
    city = get_city(latlon)
else:
    raise ValueError(f"Unknown location:{openweather_location}")

print("City =", city)
print("Lat/Lon = ", latlon)

# ===========
# U I
# ===========
today_date = label.Label(terminalio.FONT, text="?" * 30, color=0x000000)
today_date.anchor_point = (0, 0)
today_date.anchored_position = (15, 13)

city_name = label.Label(terminalio.FONT, text=city, color=0x000000)
city_name.anchor_point = (0, 0)
city_name.anchored_position = (15, 24)

today_icon = displayio.TileGrid(
    icons_large_bmp,
    pixel_shader=icons_small_pal,
    x=10,
    y=40,
    width=1,
    height=1,
    tile_width=70,
    tile_height=70,
)

today_morn_temp = label.Label(terminalio.FONT, text="+100F", color=0x000000)
today_morn_temp.anchor_point = (0.5, 0)
today_morn_temp.anchored_position = (118, 59)

today_day_temp = label.Label(terminalio.FONT, text="+100F", color=0x000000)
today_day_temp.anchor_point = (0.5, 0)
today_day_temp.anchored_position = (149, 59)

today_night_temp = label.Label(terminalio.FONT, text="+100F", color=0x000000)
today_night_temp.anchor_point = (0.5, 0)
today_night_temp.anchored_position = (180, 59)

today_humidity = label.Label(terminalio.FONT, text="100%", color=0x000000)
today_humidity.anchor_point = (0, 0.5)
today_humidity.anchored_position = (105, 95)

today_wind = label.Label(terminalio.FONT, text="99m/s", color=0x000000)
today_wind.anchor_point = (0, 0.5)
today_wind.anchored_position = (155, 95)

today_sunrise = label.Label(terminalio.FONT, text="12:12 PM", color=0x000000)
today_sunrise.anchor_point = (0, 0.5)
today_sunrise.anchored_position = (45, 117)

today_sunset = label.Label(terminalio.FONT, text="12:12 PM", color=0x000000)
today_sunset.anchor_point = (0, 0.5)
today_sunset.anchored_position = (130, 117)

today_banner = displayio.Group()
today_banner.append(today_date)
today_banner.append(city_name)
today_banner.append(today_icon)
today_banner.append(today_morn_temp)
today_banner.append(today_day_temp)
today_banner.append(today_night_temp)
today_banner.append(today_humidity)
today_banner.append(today_wind)
today_banner.append(today_sunrise)
today_banner.append(today_sunset)

future_banners = [
    make_banner(x=210, y=18),
    make_banner(x=210, y=39),
    make_banner(x=210, y=60),
    make_banner(x=210, y=81),
    make_banner(x=210, y=102),
]

magtag.graphics.root_group.append(today_banner)
for future_banner in future_banners:
    magtag.graphics.root_group.append(future_banner)

# ===========
#  M A I N
# ===========
print("Fetching forecast...")
forecast_data, utc_time, local_tz_offset = get_forecast(latlon)

print("Updating...")
update_today(forecast_data[0], local_tz_offset)
for day, forecast in enumerate(forecast_data[1:6]):
    update_banner(future_banners[day], forecast)

print("Refreshing...")
time.sleep(magtag.display.time_to_refresh + 1)
magtag.display.refresh()
time.sleep(magtag.display.time_to_refresh + 1)

print("Sleeping...")
go_to_sleep(utc_time + local_tz_offset)
#  entire code will run again after deep sleep cycle
#  similar to hitting the reset button
