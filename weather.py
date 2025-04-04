import logging
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aussie_weather")

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "aussie-weather-app/1.0"
REQUEST_TIMEOUT = 30.0


async def send_request_to_nws(url: str) -> Optional[dict[str, Any]]:
    """
    Make a request to the NWS API with proper error handling.

    Args:
        url: The endpoint URL.

    Returns:
        A JSON-decoded dictionary if the request succeeds, or None otherwise.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    async with httpx.AsyncClient() as client:
        try:
            logger.debug("Sending request to: %s", url)
            response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Crikey! Failed request to %s: %s", url, exc)
            return None


def format_alert(feature: dict) -> str:
    """
    Format an alert feature into a readable string.

    Args:
        feature: A dictionary containing alert information.

    Returns:
        A formatted multi-line string with alert details.
    """
    props = feature.get("properties", {})
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions provided')}"
    )


@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY).

    Returns:
        A formatted string containing alerts, or an error message.
    """
    logger.debug("get_alerts called with state: %s", state)
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await send_request_to_nws(url)

    if not data or "features" not in data:
        logger.error("Dinkum! No data or missing 'features' from %s", url)
        return "Fair go, unable to fetch alerts or none available."

    if not data["features"]:
        logger.info("No active alerts available for state %s", state)
        return "No active alerts, mate."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Get weather forecast for a location.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.

    Returns:
        A formatted string with forecast details or an error message.
    """
    logger.debug("get_forecast called with lat=%s, lon=%s", latitude, longitude)
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await send_request_to_nws(points_url)

    if not points_data:
        logger.error("Struth! Unable to fetch forecast grid for coordinates (%s, %s)", latitude, longitude)
        return "No forecast data available for this location, mate."

    forecast_url = points_data.get("properties", {}).get("forecast")
    if not forecast_url:
        logger.error("Missing 'forecast' URL for coordinates (%s, %s)", latitude, longitude)
        return "No forecast URL found in the data."

    forecast_data = await send_request_to_nws(forecast_url)
    if not forecast_data:
        logger.error("Unable to fetch detailed forecast from %s", forecast_url)
        return "No detailed forecast available, sorry mate."

    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        logger.info("No forecast periods available.")
        return "No forecast available right now, mate."

    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = (
            f"{period.get('name', 'Unknown')}:\n"
            f"Temperature: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', '')}\n"
            f"Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', 'N/A')}\n"
            f"Forecast: {period.get('detailedForecast', 'N/A')}"
        )
        forecasts.append(forecast)
    return "\n---\n".join(forecasts)


if __name__ == "__main__":
    logger.info("G'day mate, starting Aussie Weather server on port 8000 using SSE transport...")
    mcp.run(transport="sse")