# cogs/api_utils.py
# No API keys yet except Google Safe Browsing

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import datetime
import urllib.parse

GOOGLE_SAFE_BROWSING_KEY = "Get Here: https://developers.google.com/safe-browsing/v4/get-started"


class APIUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        async with self.session.get("https://v2.jokeapi.dev/joke/Any?safe-mode") as r:
            data = await r.json()

        joke = data["joke"] if data["type"] == "single" else f"{data['setup']}\n{data['delivery']}"
        await interaction.response.send_message(joke)

    @app_commands.command(name="fact", description="Get a random fact")
    async def fact(self, interaction: discord.Interaction):
        async with self.session.get("https://uselessfacts.jsph.pl/random.json?language=en") as r:
            data = await r.json()
        await interaction.response.send_message(data["text"])

    @app_commands.command(name="urban", description="Search Urban Dictionary")
    async def urban(self, interaction: discord.Interaction, term: str):
        url = f"https://api.urbandictionary.com/v0/define?term={urllib.parse.quote(term)}"
        async with self.session.get(url) as r:
            data = await r.json()

        if not data["list"]:
            await interaction.response.send_message("No definition found.")
            return

        entry = data["list"][0]
        embed = discord.Embed(
            title=entry["word"],
            description=entry["definition"][:4000]
        )
        embed.add_field(
            name="Example",
            value=entry["example"][:1024] or "N/A",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="define", description="Define a word")
    async def define(self, interaction: discord.Interaction, word: str):
        async with self.session.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        ) as r:
            data = await r.json()

        if isinstance(data, dict):
            await interaction.response.send_message("No definition found.")
            return

        meaning = data[0]["meanings"][0]
        definition = meaning["definitions"][0]["definition"]
        await interaction.response.send_message(f"**{word}**: {definition}")

    @app_commands.command(name="time", description="Get current time for a timezone")
    async def time(self, interaction: discord.Interaction, timezone: str):
        async with self.session.get(
            f"https://worldtimeapi.org/api/timezone/{timezone}"
        ) as r:
            if r.status != 200:
                await interaction.response.send_message("Invalid timezone.")
                return
            data = await r.json()

        dt = datetime.datetime.fromisoformat(data["datetime"])
        await interaction.response.send_message(
            f"Time in `{timezone}`: **{dt.strftime('%Y-%m-%d %H:%M:%S')}**"
        )

    @app_commands.command(
        name="url-check",
        description="Check if a URL is safe using Google Safe Browsing"
    )
    async def url_check(self, interaction: discord.Interaction, url: str):
        endpoint = (
            "https://safebrowsing.googleapis.com/v4/threatMatches:find"
            f"?key={GOOGLE_SAFE_BROWSING_KEY}"
        )

        payload = {
            "client": {
                "clientId": "discord-bot",
                "clientVersion": "1.0"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }

        try:
            async with self.session.post(endpoint, json=payload) as r:
                data = await r.json()

            footer = (
                "_Searches not found in Google's database will return safe._"
            )

            if not data.get("matches"):
                await interaction.response.send_message(
                    "â **URL is safe** (no threats detected).\n" + footer
                )
            else:
                threats = {m["threatType"] for m in data["matches"]}
                threat_list = ", ".join(threats)

                await interaction.response.send_message(
                    f"â ï¸ **Unsafe URL detected**\n"
                    f"Threats: **{threat_list}**\n"
                    f"{footer}"
                )

        except Exception as e:
            await interaction.response.send_message(
                f"URL check failed:\n```{e}```"
            )

    @app_commands.command(
        name="weather",
        description="Get current weather and forecast for a city"
    )
    @app_commands.describe(
        city="City name (supports country/state)",
        units="Temperature units"
    )
    @app_commands.choices(
        units=[
            app_commands.Choice(name="Celsius", value="c"),
            app_commands.Choice(name="Fahrenheit", value="f")
        ]
    )
    async def weather(
        self,
        interaction: discord.Interaction,
        city: str,
        units: app_commands.Choice[str]
    ):
        unit = units.value if units else "c"
        temp_unit = "Â°F" if unit == "f" else "Â°C"
        wind_unit = "mph" if unit == "f" else "km/h"

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={urllib.parse.quote(city)}&count=1"
        )

        async with self.session.get(geo_url) as r:
            geo_data = await r.json()

        results = geo_data.get("results")
        if not results:
            await interaction.response.send_message("City not found.")
            return

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"] 
        name = loc["name"]
        country = loc.get("country", "")
        admin = loc.get("admin1")

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current_weather=true"
            "&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&temperature_unit={'fahrenheit' if unit == 'f' else 'celsius'}"
            f"&windspeed_unit={'mph' if unit == 'f' else 'kmh'}"
            "&timezone=auto"
        )

        async with self.session.get(weather_url) as r:
            data = await r.json()

        current = data.get("current_weather")
        daily = data.get("daily")

        if not current or not daily:
            await interaction.response.send_message("Weather data unavailable.")
            return

        weather_map = {
            0: "Clear âï¸",
            1: "Mostly Clear ð¤ï¸",
            2: "Partly Cloudy â",
            3: "Overcast âï¸",
            45: "Fog ð«ï¸",
            51: "Drizzle ð¦ï¸",
            61: "Rain ð§ï¸",
            71: "Snow âï¸",
            95: "Thunderstorm âï¸"
        }

        condition = weather_map.get(current["weathercode"], "Unknown ð¡ï¸")

        embed = discord.Embed(
            title=f"{name}{', ' + admin if admin else ''}, {country}",
            description=condition,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Current",
            value=f"{current['temperature']}{temp_unit}",
            inline=True
        )
        embed.add_field(
            name="Wind",
            value=f"{current['windspeed']} {wind_unit}",
            inline=True
        )

        forecast = ""
        for i in range(3):
            forecast += (
                f"**{daily['time'][i]}** â "
                f"{daily['temperature_2m_min'][i]} / "
                f"{daily['temperature_2m_max'][i]}{temp_unit}\n"
            )

        embed.add_field(
            name="3-Day Forecast",
            value=forecast,
            inline=False
        )

        embed.set_footer(text="Data provided by Open-Meteo")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(APIUtils(bot))
