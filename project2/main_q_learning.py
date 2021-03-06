# -*- coding: utf-8 -*-
"""
Based on: https://github.com/ronekko/basic_reinforcement_learning
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import vrep
import contexttimer
from environment import Robot


class Agent(object):
    def __init__(self, robot, alpha=0.1, gamma=0.9, epsilon=0.05, q_init=1):
        self.robot = robot
        self.angles_lut = np.genfromtxt('foo2.csv', delimiter=',', dtype=float)
        self.num_actions = len(self.angles_lut)

        # O numero de estados pode ser diferente do numero de acoes porque
        # estamos usando o metodo simxSetTargetPosition, que se nao conseguir
        # ir ate o angulo desejado para no meio do caminho. Nao sei se eh
        # importante no nosso caso
        self.num_states_vec = [
            5,
            5,
            6,
            6,
            8,
            8,
            8,
            8,
            6
        ]

        angles = self.angles_lut.T

        # Total de estados eh igual ao total de combinacoes entre angulos
        self.num_states = self.num_states_vec[0]
        for i in range(7):
            self.num_states *= self.num_states_vec[i + 1]

        self.state_bins = [
            np.linspace(min(angles[0]), max(angles[0]), self.num_states_vec[0], endpoint=False)[1:],
            np.linspace(min(angles[1]), max(angles[1]), self.num_states_vec[1], endpoint=False)[1:],
            np.linspace(min(angles[2]), max(angles[2]), self.num_states_vec[2], endpoint=False)[1:],
            np.linspace(min(angles[3]), max(angles[3]), self.num_states_vec[3], endpoint=False)[1:],
            np.linspace(min(angles[4]), max(angles[4]), self.num_states_vec[4], endpoint=False)[1:],
            np.linspace(min(angles[5]), max(angles[5]), self.num_states_vec[5], endpoint=False)[1:],
            np.linspace(min(angles[6]), max(angles[6]), self.num_states_vec[6], endpoint=False)[1:],
            np.linspace(min(angles[7]), max(angles[7]), self.num_states_vec[7], endpoint=False)[1:],
            np.linspace(min(angles[8]), max(angles[8]), self.num_states_vec[8], endpoint=False)[1:]]

        self.q_table = np.full((self.num_states, self.num_actions), q_init)
        #self.q_table = np.genfromtxt('qtable.csv', delimiter=',')
        self.alpha = alpha  # learning rate
        self.gamma = gamma  # discount factor
        self.epsilon = epsilon  # epsilon-greedy rate


    def choose_action(self, state):
        if np.random.uniform() < self.epsilon:
            action = np.random.choice(self.num_actions)
        else:
            action = np.argmax(self.q_table[state])
        return action

    def do_action(self, action):
        angles = self.angles_lut[action]
        self.robot.set_joint_angles(angles)
        self.robot.proceed_simulation(8)

    def observe_state(self):
        angles = self.robot.get_joint_angles()
        return self.calc_state(angles)

    def calc_state(self, angles):
        state = np.digitize([angles[0]], self.state_bins[0])[0]
        return state * self.num_states_vec[1] + self.recursao(angles, 1)

    def recursao(self, angles, current):
        state = np.digitize([angles[current]], self.state_bins[current])[0]
        if current == 8:
            return state
        return state * self.num_states_vec[current+1] + self.recursao(angles, current+1)

    def play(self):
        action = self.choose_action(self.state)
        self.do_action(action)

        state_new = self.observe_state()

        position_new = self.robot.get_vase_relative_position()
        z_forward = self.robot.get_body_position()[2] - self.position[2]
        delta_x = self.position[0] - position_new[0]
        delta_y = self.position[1] - position_new[1]

        reward = delta_x + delta_y - 0.001 - z_forward

        if self.robot.get_body_position()[2] < .3:
            self.isDown = True

        # update Q-table
        self.update_q(self.state, action, reward, state_new)

        self.state = state_new
        self.position = position_new

    def update_q(self, state, action, reward, state_new):
        q_sa = self.q_table[state, action]
        td_error = reward + self.gamma * np.max(self.q_table[state_new]) - q_sa
        self.q_table[state, action] = q_sa + self.alpha * td_error

    def initialize_episode(self):
        self.robot.restart_simulation()
        self.robot.initialize_pose()
        self.position = self.robot.get_body_position()
        angles = self.robot.get_joint_angles()
        self.state = self.calc_state(angles)
        print 'Initial state: ', self.state
        self.isDown = False

    def plot(self, body_trajectory, joints_trajectory, return_history, q_table):
        fig = plt.figure(figsize=(9, 4))
        T = len(body_trajectory)

        # plot an xyz trajectory of the body
        ax1 = plt.subplot(221)
        ax2 = plt.subplot(223)
        ax3 = plt.subplot(222)
        ax4 = plt.subplot(224)
        ax1.grid()
        ax1.set_color_cycle('rgb')
        ax1.plot(np.arange(T) * 0.05, np.array(body_trajectory))
        ax1.set_title('Position of the body')
        ax1.set_ylabel('position [m]')
        ax1.legend(['x', 'y', 'z'], loc='best')

        # plot a trajectory of angles of the joints
        ax2.grid()
        ax2.set_color_cycle('rg')
        ax2.plot(np.arange(T) * 0.05, np.array(joints_trajectory))
        ax2.set_title('Angle of the joints')
        ax2.set_xlabel('time in simulation [s]')
        ax2.set_ylabel('angle [rad]')
        ax2.legend(['joint_0', 'joint_1'], loc='best')

        # plot a history of returns of each episode
        ax3.grid()
        ax3.plot(return_history)
        ax3.set_title('Returns (total rewards) of each episode')
        ax3.set_xlabel('episode')
        ax3.set_ylabel('position [m]')

        # show Q-table
        ax4.matshow(q_table.T, cmap=plt.cm.gray)
        ax4.set_title('Q-table')
        ax4.xaxis.set_ticks_position('bottom')
        ax4.set_xlabel('state')
        ax4.set_ylabel('action')
        plt.tight_layout()
        plt.show()
        plt.draw()


if __name__ == '__main__':
    try:
        client_id
    except NameError:
        client_id = -1
    e = vrep.simxStopSimulation(client_id, vrep.simx_opmode_oneshot_wait)
    vrep.simxFinish(-1)
    client_id = vrep.simxStart('127.0.0.1', 25000, True, True, 5000, 5)
    assert client_id != -1, 'Failed connecting to remote API server'

    # print ping time
    sec, msec = vrep.simxGetPingTime(client_id)
    print "Ping time: %f" % (sec + msec / 1000.0)

    robot = Robot(client_id)
    agent = Agent(robot, alpha=0.5, gamma=0.9, epsilon=0.9, q_init=0)

    num_episodes = 10
    len_episode = 200
    return_history = []
    try:
        for episode in range(num_episodes):
            print "start simulation # %d" % episode

            with contexttimer.Timer() as timer:
                agent.initialize_episode()
                time.sleep(.5)
                body_trajectory = []
                joints_trajectory = []
                body_trajectory.append(robot.get_body_position())
                joints_trajectory.append(robot.get_joint_angles())

                for t in range(len_episode):
                    agent.play()

                    body_trajectory.append(robot.get_body_position())
                    joints_trajectory.append(robot.get_joint_angles())

                    if agent.isDown:
                        break

            position = body_trajectory[-1]
            return_history.append(position[0])

            if agent.epsilon > 0.1:
                agent.epsilon -= 0.05

            print
            print "Body position: ", position
            print "Elapsed time (wall-clock): ", timer.elapsed
            print

    except KeyboardInterrupt:
        print "Terminated by `Ctrl+c` !!!!!!!!!!"

    plt.grid()
    plt.plot(return_history)
    plt.title('Return (total reward in a episode)')
    plt.xlabel('episode')
    plt.ylabel('position [m]')
    plt.show()

    T = len(body_trajectory)

    # plot an xyz trajectory of the body
    plt.grid()
    plt.plot(np.arange(T) * 0.05, np.array(body_trajectory))
    plt.title('Position of the body')
    plt.ylabel('position [m]')
    plt.legend(['x', 'y', 'z'], loc='best')
    plt.show()

    e = vrep.simxStopSimulation(client_id, vrep.simx_opmode_oneshot_wait)
