import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

WEATHER_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# Per request, and httpx applies it per phase (connect, read, write, pool), so
# two sequential calls with only this bound can hold a conversational turn open
# for far longer than any of the individual numbers suggest.
WEATHER_REQUEST_TIMEOUT_SECONDS = 5.0
# The bound that actually matters: the whole tool call, both requests included.
WEATHER_TOTAL_TIMEOUT_SECONDS = 12.0

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


async def _lookup(location: str) -> str:
    """Geocode, then read the current conditions. Raises; `get_weather` reports."""
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

    temperature = current["temperature_2m"]
    description = WEATHER_CODE_DESCRIPTIONS.get(current["weather_code"], "unknown conditions")

    return f"It's {temperature}°C and {description} in {resolved_name} right now."


async def get_weather(location: str) -> str:
    """Get the current weather for a location. Only call this once the user's
    location is known (from known facts or from their answer earlier in this
    conversation) — do not guess a location."""
    try:
        async with asyncio.timeout(WEATHER_TOTAL_TIMEOUT_SECONDS):
            return await _lookup(location)
    except (httpx.HTTPError, TimeoutError, ValueError, KeyError, IndexError):
        # Not just HTTPError: Open-Meteo answers out-of-range coordinates with
        # `{"error": true, ...}` and error pages with HTML, so the response
        # parses fine and then KeyErrors on a field that is not there. Every one
        # of those should cost the user their weather, not the whole turn.
        logger.exception("Weather lookup failed for location=%s", location)
        return "Weather lookup failed, please try again."
