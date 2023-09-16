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
        self.frames_per_decision = 25
        self.decision_frequency = 1
        self.max_flaps = 3
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
            if self.curr_frame == self.decision_frequency:
                self.curr_frame = 0


    def simulate_game(self, moves_list):
        to_ret = True

        old_pipe_x = []
        old_pipe_y_l = []
        old_pipe_y_u = []
        for i in range(len(self.pipes.lower)):
            old_pipe_x.append(self.pipes.lower[i].x)
            old_pipe_y_l.append(self.pipes.lower[i].y)
            old_pipe_y_u.append(self.pipes.upper[i].y)

        old_player_x = self.player.x
        old_player_y = self.player.y
        old_player_vel_y = self.player.vel_y
        old_player_rot = self.player.rot
        old_player_vel_rot = self.player.vel_rot
        old_player_acc_y = self.player.acc_y
        old_player_flap_acc = self.player.flap_acc

        self.player.set_simulation_mode(True)
        self.pipes.set_simulation_mode(True)

        for i in range(len(moves_list)):
            if moves_list[i] == 1:
                self.player.flap()

            if self.player.collided(self.pipes, self.floor):
                to_ret = False
                break

            self.player.tick()
            self.pipes.tick()

        self.player.set_simulation_mode(False)
        self.pipes.set_simulation_mode(False)

        for i in range(len(self.pipes.lower)):
            self.pipes.lower[i].x = old_pipe_x[i]
            self.pipes.upper[i].x = old_pipe_x[i]
            self.pipes.lower[i].y = old_pipe_y_l[i]
            self.pipes.upper[i].y = old_pipe_y_u[i]

        self.player.x = old_player_x
        self.player.y = old_player_y
        self.player.vel_y = old_player_vel_y
        self.player.rot = old_player_rot
        self.player.vel_rot = old_player_vel_rot
        self.player.acc_y = old_player_acc_y
        self.player.flap_acc = old_player_flap_acc
        self.player.crashed = False

        return to_ret

