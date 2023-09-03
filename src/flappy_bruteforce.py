import asyncio
import copy
import sys

import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Pipe,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .utils import GameConfig, Images, Sounds, Window
from .flappy import Flappy

def generate_lists(n, k):
    if k == 0:
        return [[0] * n]
    if n == k:
        return [[1] * n]

    lists_with_zero = generate_lists(n - 1, k)
    lists_with_one = generate_lists(n - 1, k - 1)

    for lst in lists_with_one:
        lst.append(1)

    for lst in lists_with_zero:
        lst.append(0)

    return lists_with_zero + lists_with_one

class FlappyBruteForce(Flappy):

    def __init__(self):
        super().__init__()
        self.curr_frame = 0
        self.frames_per_decision = 10
        self.max_flaps = 10
        self.moves_lists = []
        for i in range(self.max_flaps + 1):
            self.moves_lists += generate_lists(self.frames_per_decision, i)
        # print(self.moves_lists)

    async def play(self):
        self.score.reset()
        self.player.set_mode(PlayerMode.NORMAL)

        moves = self.frames_per_decision * [0]

        while True:
            if self.curr_frame == 0:
                moves = self.moves_lists[0]
                set_moves = False
                results = []
                for moves_list in self.moves_lists:
                    result = self.simulate_game(moves_list)
                    results.append(result)
                    if result:
                        moves = moves_list
                        break

                # print(results)

            print(self.player.x)
            print(self.pipes.lower[0].rect.x)

            if self.player.collided(self.pipes, self.floor):
                return

            for i, pipe in enumerate(self.pipes.upper):
                if self.player.crossed(pipe):
                    self.score.add()

            if moves[self.curr_frame] == 1:
                self.player.flap()

            for event in pygame.event.get():
                self.check_quit_event(event)

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()
            self.player.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

            self.curr_frame += 1
            if self.curr_frame == self.frames_per_decision:
                self.curr_frame = 0


    def simulate_game(self, moves_list):
        simulation_player = Player(self.player.config)
        simulation_player.y = self.player.y
        simulation_player.x = self.player.x
        simulation_player.acc_y = self.player.acc_y
        simulation_player.vel_y = self.player.vel_y
        simulation_player.rot = self.player.rot
        simulation_player.vel_rot = self.player.vel_rot
        simulation_player.rot_max = self.player.rot_max
        simulation_player.rot_min = self.player.rot_min
        simulation_player.min_vel_y = self.player.min_vel_y
        simulation_player.max_vel_y = self.player.max_vel_y
        simulation_player.flapped = self.player.flapped
        simulation_player.flap_acc = self.player.flap_acc
        simulation_player.set_simulation_mode(True)
        simulation_player.mode = self.player.mode
        simulation_player.hit_mask = self.player.hit_mask
        simulation_player.rect = self.player.rect

        simulation_pipes = Pipes(self.pipes.config)
        simulation_pipes.upper = []
        simulation_pipes.lower = []

        for pipe in self.pipes.upper:
            newpipe = Pipe(pipe.config)
            newpipe.x = pipe.x
            newpipe.y = pipe.y
            newpipe.vel_x = pipe.vel_x
            newpipe.hit_mask = copy.deepcopy(pipe.hit_mask)
            newpipe.rect = copy.deepcopy(pipe.rect)
            simulation_pipes.upper.append(newpipe)

        for pipe in self.pipes.lower:
            newpipe = Pipe(pipe.config)
            newpipe.x = pipe.x
            newpipe.y = pipe.y
            newpipe.vel_x = pipe.vel_x
            newpipe.hit_mask = copy.deepcopy(pipe.hit_mask)
            newpipe.rect = copy.deepcopy(pipe.rect)
            simulation_pipes.lower.append(newpipe)

        simulation_pipes.set_simulation_mode(True)

        for i in range(len(moves_list)):
            if moves_list[i] == 1:
                simulation_player.flap()

            print(simulation_player.x)
            print(simulation_pipes.lower[0].rect.x)
            print('N')
            if simulation_player.collided(simulation_pipes, self.floor):
                print("COLLIDED")
                print(simulation_player.y)
                print(simulation_player.x)
                return False

            simulation_player.tick()
            simulation_pipes.tick()

        return True

