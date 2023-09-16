import asyncio
import copy
import random
import sys

import pygame
import torch
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .flappy import Flappy
from .utils import GameConfig, Images, Sounds, Window
from .ModelMLP import ModelMLP

class FlappyNN(Flappy):
    def __init__(self):
        self.population_size = 200
        self.num_alive = self.population_size
        self.selection_param = 0.4
        self.mutation_probabilty = 0.1
        self.mutation_factor = 0.1

        self.models = []
        for _ in range(self.population_size):
            model = ModelMLP(input_dim=3, hidden_dim=10, output_dim=1)
            self.models.append(model)

        pygame.init()
        pygame.display.set_caption("Flappy Bird")
        window = Window(288, 512)
        screen = pygame.display.set_mode((window.width, window.height))
        images = Images()

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=30,
            window=window,
            images=images,
            sounds=Sounds(),
        )

        self.players = [Player(self.config) for i in range(self.population_size)]
        self.start_y = self.players[0].y
        self.dead = []
        self.max_score = self.population_size * [0]
        self.total_max = 0

    async def start(self):
        first_game = True
        while True:
            self.background = Background(self.config)
            self.floor = Floor(self.config)

            self.welcome_message = WelcomeMessage(self.config)
            self.game_over_message = GameOver(self.config)
            self.pipes = Pipes(self.config)
            self.score = Score(self.config)
            if first_game:
                await self.splash()
                first_game = False
            await self.play()
            # await self.game_over()

    async def splash(self):
        """Shows welcome splash screen animation of flappy bird"""

        for player in self.players:
            player.set_mode(PlayerMode.SHM)

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    return

            self.background.tick()
            self.floor.tick()
            for player in self.players:
                player.tick()
            self.welcome_message.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def check_quit_event(self, event):
        if event.type == QUIT or (
            event.type == KEYDOWN and event.key == K_ESCAPE
        ):
            pygame.quit()
            sys.exit()

    def is_tap_event(self, event):
        m_left, _, _ = pygame.mouse.get_pressed()
        space_or_up = event.type == KEYDOWN and (
            event.key == K_SPACE or event.key == K_UP
        )
        screen_tap = event.type == pygame.FINGERDOWN
        return m_left or space_or_up or screen_tap

    async def play(self):
        self.score.reset()

        self.players = [Player(self.config) for _ in range(self.population_size)]

        for player in self.players:
            player.set_mode(PlayerMode.NORMAL)
            player.alive = True

        while True:
            assert(len(self.models) == self.population_size)
            assert(len(self.players) == self.population_size)

            for i, player in enumerate(self.players):
                if not player.alive:
                    continue

                if player.collided(self.pipes, self.floor):
                    player.alive = False
                    self.num_alive -= 1
                    self.dead.append(i)
                    # print(self.num_alive)
                    if self.num_alive == 0:
                        self.game_over()
                        return

                for pipe in self.pipes.upper:
                    if player.crossed(pipe):
                        self.max_score[i] += 1
                        if self.max_score[i] > self.total_max:
                            self.total_max += 1
                            self.score.add()

                for event in pygame.event.get():
                    self.check_quit_event(event)

                model = self.models[i]
                upper_pipe = self.pipes.upper[0]
                lower_pipe = self.pipes.lower[0]

                dist_x = upper_pipe.rect.x - (player.rect.x + player.rect.w)
                dist_y_upper = player.rect.y - (upper_pipe.rect.y + upper_pipe.rect.h)
                dist_y_lower = lower_pipe.rect.y - (player.rect.y + player.rect.h)

                dists = [dist_x, dist_y_lower, dist_y_upper]
                tensor = torch.tensor(dists).float()

                decision = model(tensor)

                if decision:
                    player.flap()

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()

            for player in self.players:
                if player.alive:
                    player.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def game_over(self):
        self.num_alive = self.population_size
        # print(self.dead)
        self.selection()
        self.dead = []
        self.total_max = 0
        self.max_score = self.population_size * [0]

    def selection(self):
        """
        receives population and returns the best species
        """
        self.dead.reverse()
        to_keep = self.dead[:int(self.selection_param * self.population_size)]
        self.mutation(to_keep)

    def mutation(self, to_keep):
        newmodels = []
        for j in range(self.population_size):
            index = random.randint(0, len(to_keep) - 1)
            # index = j
            model = copy.deepcopy(self.models[index])
            model.mutate_weights(mutation_probability=self.mutation_probabilty, mutation_factor=self.mutation_factor)
            newmodels.append(model)
        self.models = copy.deepcopy(newmodels)
        assert(len(self.models) == self.population_size)
        assert(len(self.dead) == self.population_size)
        print(self.dead)



