import logging
from dataclasses import dataclass
from uuid import UUID

import httpx
from agents import Agent, RunContextWrapper, function_tool
from sqlalchemy.orm import Session as DbSession

from ..models import Memory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Sarjy, a helpful, warm voice-and-text assistant. "
    "Keep replies concise and conversational, since they may be read aloud.\n\n"
    "When the user asks about the weather: look for a saved location among the "
    "known facts about this user below. If one is present, call get_weather with "
    "it directly. If none is present, ask the user what location they mean before "
    "calling any weather tool. Once they answer, call save_memory to remember the "
    "location, then call get_weather with it."
)

FACT_LOG_MAX_LENGTH = 60

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


@dataclass
class ChatContext:
    user_id: UUID
    session_id: UUID
    db: DbSession


@function_tool
async def save_memory(ctx: RunContextWrapper[ChatContext], fact: str) -> str:
    """Save a durable fact about the user that should be remembered in future
    conversations, even in a different session (e.g. preferences, names, ongoing
    situations). Only call this for things worth recalling later, not small talk."""
    db = ctx.context.db
    db.add(
        Memory(
            user_id=ctx.context.user_id,
            content=fact,
            source_session_id=ctx.context.session_id,
        )
    )
    db.commit()

    truncated = fact if len(fact) <= FACT_LOG_MAX_LENGTH else f"{fact[:FACT_LOG_MAX_LENGTH]}…"
    logger.info("Saved memory for user_id=%s: %s", ctx.context.user_id, truncated)

    return f"Remembered: {fact}"


@function_tool
async def get_weather(ctx: RunContextWrapper[ChatContext], location: str) -> str:
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


def build_agent(memory_facts: list[str]) -> Agent:
    instructions = SYSTEM_PROMPT
    if memory_facts:
        bullet_list = "\n".join(f"- {fact}" for fact in memory_facts)
        instructions += f"\n\nKnown facts about this user:\n{bullet_list}"

    return Agent(
        name="Sarjy",
        instructions=instructions,
        tools=[save_memory, get_weather],
        mcp_servers=[],  # extension point: add MCPServerStdio(...) / MCPServerSse(...) here
    )
