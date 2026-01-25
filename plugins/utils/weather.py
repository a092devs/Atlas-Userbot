import aiohttp

from utils.respond import respond
from db.apikeys import get_key


__plugin__ = {
    "name": "Weather",
    "category": "utils",
    "description": "Get current weather information for a city",
    "commands": {
        "weather": "Show current weather for a given city",
    },
}


API_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUIRED_KEY = "WEATHER_API_KEY"


async def handler(event, args):
    if not args:
        return await respond(event, "❌ Usage: `.weather <city>`")

    api_key = get_key(REQUIRED_KEY)
    if not api_key:
        return await respond(
            event,
            "❌ Weather API key not configured.\n\n"
            "Set it using:\n"
            f"`.setapi {REQUIRED_KEY} <your_api_key>`",
        )

    city = " ".join(args)

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as resp:
                if resp.status != 200:
                    return await respond(event, "❌ City not found.")

                data = await resp.json()

    except Exception as e:
        return await respond(event, f"❌ Error fetching weather:\n`{e}`")

    text = (
        f"🌦 **Weather in {data['name']}, {data['sys']['country']}**\n\n"
        f"🌡 **Temperature:** {data['main']['temp']}°C\n"
        f"🤒 **Feels Like:** {data['main']['feels_like']}°C\n"
        f"💧 **Humidity:** {data['main']['humidity']}%\n"
        f"🌬 **Wind:** {data['wind']['speed']} m/s\n"
        f"☁️ **Condition:** {data['weather'][0]['description'].title()}"
    )

    await respond(event, text)
