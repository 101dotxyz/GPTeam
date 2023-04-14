import asyncio

from dotenv import load_dotenv

from .memory.agent import Memory

load_dotenv()


def main():
    m1 = Memory(id="1", description="picked up a kettle and poured water into it")
    m2 = Memory(id="2", description="killed my neighbour")
    m3 = Memory(id="3", description="went fishing")
    m4 = Memory(id="4", description="discovered a new music artist")
    m5 = Memory(id="5", description="ate a sandwich")
    m6 = Memory(id="6", description="found out that Mike is a good friend")
