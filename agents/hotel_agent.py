import os

import requests # type: ignore
from langchain_chroma import Chroma # type: ignore

from agents.base import Agent, embeddings, splitter
from config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, FAQ_DIR, FAQ_TOP_K, FORECAST_URL, GEOCODING_URL


def _get(url, **params):
    resp = requests.get(url, params=params, timeout=10)
    if not resp.ok:
        raise ValueError(resp.json().get("reason", resp.text))
    return resp.json()


class HotelAgent(Agent):
    name = "hotel_agent"
    description = "Searches hotels, answers hotel policy questions (check-in times, pets, occupancy, cancellations, insurance), or reports live weather and forecasts for a city."
    handoff_tool = "search_hotels"

    def __init__(self):
        super().__init__()
        self.store = Chroma(collection_name=f"{self.name}_faqs_{CHUNK_SIZE}_{CHUNK_OVERLAP}", embedding_function=embeddings,
                            persist_directory=CHROMA_DIR)
        if not self.store.get(limit=1)["ids"]:
            with open(os.path.join(FAQ_DIR, f"{self.name}.txt"), encoding="utf-8") as f:
                entries = f.read().strip().split("\n\n")
            self.store.add_texts([c for e in entries for c in splitter.split_text(e)])

    def search_faq(self, question):
        return [d.page_content for d in self.store.similarity_search(question, k=FAQ_TOP_K)]

    def search_hotels(self, location, check_in, check_out, guests):
        params = {"location": location, "check_in": check_in, "check_out": check_out, "guests": guests}
        return [{"hotel_name": "Grand Central Suites", "price_per_night_usd": 129, **params},
                {"hotel_name": "Harborview Inn", "price_per_night_usd": 98, **params}]

    def search_weather(self, location, country_code=None, start_date=None, end_date=None):
        found = _get(GEOCODING_URL, name=location, count=1, countryCode=country_code).get("results")
        if not found:
            raise ValueError(f"location not found: {location}")
        params = {"latitude": found[0]["latitude"], "longitude": found[0]["longitude"], "timezone": "auto",
                  "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                  "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max"}
        if start_date or end_date:
            params.update(start_date=start_date or end_date, end_date=end_date or start_date)
        forecast = _get(FORECAST_URL, **params)
        return {"place": f"{found[0]['name']}, {found[0].get('country', '')}",
                **{k: forecast[k] for k in ("current", "current_units", "daily", "daily_units")}}