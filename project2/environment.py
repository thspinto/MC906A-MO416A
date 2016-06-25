# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 12:47:16 2015

@author: ryuhei
"""

import time
import numpy as np
import vrep


class Robot(object):
    def __init__(self, client_id):
        assert not client_id == -1
        self.client_id = client_id
        self.configure_handles()

    def start_simulation(self):
        rc = vrep.simxStartSimulation(self.client_id,
                                      vrep.simx_opmode_oneshot_wait)
        rc = vrep.simxSynchronous(self.client_id, True)

    def restart_simulation(self):
        rc = vrep.simxStopSimulation(self.client_id,
                                     vrep.simx_opmode_oneshot_wait)
        time.sleep(0.5)
        self.start_simulation()

    def proceed_simulation(self, num_steps=1):
        for t in range(num_steps):
            rc = vrep.simxSynchronousTrigger(self.client_id)

    def configure_handles(self):
        # Handles of body and joints
        rc, body = vrep.simxGetObjectHandle(self.client_id, 'NAO', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc

        rc, joint_0 = vrep.simxGetObjectHandle(self.client_id, 'LShoulderPitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_1 = vrep.simxGetObjectHandle(self.client_id, 'RShoulderPitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc

        rc, joint_2 = vrep.simxGetObjectHandle(self.client_id, 'LHipPitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_3 = vrep.simxGetObjectHandle(self.client_id, 'RHipPitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_4 = vrep.simxGetObjectHandle(self.client_id, 'LKneePitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_5 = vrep.simxGetObjectHandle(self.client_id, 'RKneePitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_6 = vrep.simxGetObjectHandle(self.client_id, 'LAnklePitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc
        rc, joint_7 = vrep.simxGetObjectHandle(self.client_id, 'RAnklePitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc

        rc, joint_8 = vrep.simxGetObjectHandle(self.client_id, 'LHipYawPitch3', vrep.simx_opmode_oneshot_wait)
        assert rc == 0, rc

        self.body = body
        self.joints = [joint_0, joint_1, joint_2, joint_3, joint_4, joint_5, joint_6, joint_7, joint_8]
        self.get_body_position(initial=True)
        self.get_joint_angles(initial=True)
        time.sleep(0.5)

    def get_body_position(self, initial=False):
        if initial:
            mode = vrep.simx_opmode_streaming
        else:
            mode = vrep.simx_opmode_buffer
        rc, body_position = vrep.simxGetObjectPosition(
            self.client_id, self.body, -1, mode)
        assert rc == (1 if initial else 0), rc
        return np.array(body_position)

    def get_joint_angles(self, initial=False):
        if initial:
            mode = vrep.simx_opmode_streaming
        else:
            mode = vrep.simx_opmode_buffer
        angles = []
        for joint in self.joints:
            rc, angle = vrep.simxGetJointPosition(self.client_id, joint, mode)
            assert rc == (1 if initial else 0), rc
            angles.append(angle)
        return np.array(angles)

    def set_joint_angles(self, angles):
        assert len(angles) == 9
        for joint, angle in zip(self.joints, angles):
            rc = vrep.simxSetJointTargetPosition(self.client_id, joint, angle,
                                                 vrep.simx_opmode_streaming)

    def initialize_pose(self):
        self.set_joint_angles([2, 2, 0, 0, 0, 0, 0, 0, 0])
        self.proceed_simulation(10)


if __name__ == '__main__':
    pass