import asyncio

from src.flappy import Flappy
from src.flappy_bruteforce import FlappyBruteForce
import sys

modes_dict = dict()
modes_dict["regular"] = Flappy
modes_dict["bruteforce"] = FlappyBruteForce

if __name__ == "__main__":
    mode = sys.argv[1]
    asyncio.run(modes_dict[mode]().start())
