import os

from langchain_chroma import Chroma # type: ignore

from agents.base import Agent, embeddings, splitter
from config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, FAQ_DIR, FAQ_TOP_K


class FlightAgent(Agent):
    name = "flight_agent"
    description = "Searches flights or answers flight policy questions (baggage, cancellations, delays, documents)."
    handoff_tool = "search_flights"

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

    def search_flights(self, origin, destination, depart_date, passengers, return_date=None):
        params = {"origin": origin, "destination": destination, "depart_date": depart_date,
                  "passengers": passengers, "return_date": return_date}
        params = {k: v for k, v in params.items() if v is not None}
        return [{"flight_no": "AI202", "price_usd": 412, **params},
                {"flight_no": "6E555", "price_usd": 375, **params}]