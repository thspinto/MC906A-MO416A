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
        # # Quantidade de angulos após discretizacao para cada junta
        # self.num_actions_vec = [
        #     3,
        #     3,
        #     3,
        #     3,
        #     3,
        #     3,
        #     3,
        #     3,
        #     3
        # ]
        #
        # # Total de acoes eh igual ao total de combinacoes entre angulos
        # self.num_actions = self.num_actions_vec[0]
        # for i in range(1, 8):
        #     self.num_actions *= self.num_actions_vec[i]
        #
        # # TODO validar (http://doc.aldebaran.com/1-14/family/nao_h25/joints_h25.html)
        # # Intervalos para serem discretizados
        #
        # #braços
        # self.angles_0 = np.linspace(1, 2, self.num_actions_vec[0])
        # self.angles_1 = np.linspace(1, 2, self.num_actions_vec[1])
        #
        # #quadril
        # self.angles_2 = np.linspace(-.5, .5, self.num_actions_vec[2])
        # self.angles_3 = np.linspace(-.5, .5, self.num_actions_vec[3])
        #
        # self.angles_4 = np.linspace(0, .5, self.num_actions_vec[4])
        # self.angles_5 = np.linspace(0, .5, self.num_actions_vec[5])
        # self.angles_6 = np.linspace(-.5, 0, self.num_actions_vec[6])
        # self.angles_7 = np.linspace(-.5, 0, self.num_actions_vec[7])
        # self.angles_8 = np.linspace(-.1, 0.1, self.num_actions_vec[8])
        #
        # # TODO Eita, nao sei o que isso faz nao...
        # look-up table from action to angles
        # self.angles_lut = np.array(np.meshgrid(self.angles_0, self.angles_1,
        #                                        self.angles_2,
        #                                        self.angles_3,
        #                                        self.angles_4,
        #                                        self.angles_5, self.angles_6, self.angles_7, self.angles_8,
        #                                        indexing='ij')).reshape(9, -1).T

        self.angles_lut = np.genfromtxt('foo.csv', delimiter=',')
        self.num_actions = len(self.angles_lut)

        # self.state_bins = self.angles_lut.T
        # for i in range(len(self.state_bins)):
        #     self.state_bins[i].sort()

        # O numero de estados pode ser diferente do numero de acoes porque
        # estamos usando o metodo simxSetTargetPosition, que se nao conseguir
        # ir ate o angulo desejado para no meio do caminho. Nao sei se eh
        # importante no nosso caso
        self.num_states_vec = [
            3,
            3,
            4,
            4,
            8,
            8,
            8,
            8,
            4
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
            np.linspace(-min(angles[8]), max(angles[8]), self.num_states_vec[8], endpoint=False)[1:]]

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
        self.robot.proceed_simulation()

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
        print 'New state: ', state_new

        position_new = self.robot.get_body_position()
        x_forward = position_new[0] - self.position[0]
        z_forward = position_new[2] - self.position[2]
        reward = x_forward - 0.001 - z_forward

        if position_new[2] < .3:
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

    def plot(body_trajectory, joints_trajectory, return_history, q_table):
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
    agent = Agent(robot, alpha=0.1, gamma=0.9, epsilon=0.1, q_init=100000)

    num_episodes = 50
    len_episode = 500
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
                    print agent.state,

                    body_trajectory.append(robot.get_body_position())
                    joints_trajectory.append(robot.get_joint_angles())

                    if agent.isDown:
                        break

            position = body_trajectory[-1]
            return_history.append(position[0])

            print
            print "Body position: ", position
            print "Elapsed time (wall-clock): ", timer.elapsed
            print

    except KeyboardInterrupt:
        print "Terminated by `Ctrl+c` !!!!!!!!!!"

    np.savetxt('qtable.csv', agent.q_table, delimiter=',')
    plt.grid()
    plt.plot(return_history)
    plt.title('Return (total reward in a episode)')
    plt.xlabel('episode')
    plt.ylabel('position [m]')
    plt.show()

    e = vrep.simxStopSimulation(client_id, vrep.simx_opmode_oneshot_wait)
