from agents.flight_agent import FlightAgent
from agents.general_agent import GeneralAgent
from agents.hotel_agent import HotelAgent

AGENT_CLASSES = [FlightAgent, HotelAgent, GeneralAgent]


def build_agents():
    return {cls.name: cls() for cls in AGENT_CLASSES}