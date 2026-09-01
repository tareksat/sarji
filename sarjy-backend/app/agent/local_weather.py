"""A local `@function_tool` copy of the MCP server's `get_weather`.

Exists only for the latency write-up's A/B: the same lookup with and without
the MCP transport hop in front of it. `sarjy-mcp-server` remains the shipped
path — this module is reached only when `USE_LOCAL_WEATHER_TOOL=true`, and it
should be deleted if that comparison is ever dropped.
"""

import logging

import httpx
from agents import function_tool

logger = logging.getLogger(__name__)

WEATHER_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_REQUEST_TIMEOUT_SECONDS = 10.0

# WMO weather codes returned by Open-Meteo's `current.weather_code` field.
WEATHER_CODE_DESCRIPTIONS = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy with rime",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "light snow showers",
    86: "snow showers",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail",
}


@function_tool
async def local_get_weather(location: str) -> str:
    """Get the current weather for a location. Only call this once the user's
    location is known (from known facts or from their answer earlier in this
    conversation) — do not guess a location."""
    try:
        async with httpx.AsyncClient(timeout=WEATHER_REQUEST_TIMEOUT_SECONDS) as client:
            geocode_resp = await client.get(
                WEATHER_GEOCODING_URL, params={"name": location, "count": 1}
            )
            geocode_resp.raise_for_status()
            results = geocode_resp.json().get("results")
            if not results:
                return f"Could not find a location matching '{location}'."

            place = results[0]
            latitude, longitude = place["latitude"], place["longitude"]
            resolved_name = place["name"]

            forecast_resp = await client.get(
                WEATHER_FORECAST_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,weather_code",
                },
            )
            forecast_resp.raise_for_status()
            current = forecast_resp.json()["current"]
    except httpx.HTTPError:
        logger.exception("Weather lookup failed for location=%s", location)
        return "Weather lookup failed, please try again."

    temperature = current["temperature_2m"]
    description = WEATHER_CODE_DESCRIPTIONS.get(current["weather_code"], "unknown conditions")

    return f"It's {temperature}°C and {description} in {resolved_name} right now."
