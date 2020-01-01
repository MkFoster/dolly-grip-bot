#!/usr/bin/env python3
# Copyright 2019 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
# 
# You may not use this file except in compliance with the terms and conditions 
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMAZON SPECIFICALLY DISCLAIMS, WITH 
# RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

import os
import sys
import time
import logging
import json
import random
import threading

from enum import Enum
from agt import AlexaGadget

from ev3dev2.led import Leds
from ev3dev2.sound import Sound
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent, MediumMotor, LargeMotor
from ev3dev2.sensor.lego import ColorSensor

# Set the logging level to INFO to see messages from AlexaGadget
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger = logging.getLogger(__name__)


class Direction(Enum):
    """
    The list of directional commands and their variations.
    These variations correspond to the skill slot values.
    """
    FORWARD = ['forward', 'forwards', 'go forward']
    BACKWARD = ['back', 'backward', 'backwards', 'go backward']
    UP = ['up']
    DOWN = ['down']
    LEFT = ['left', 'go left']
    RIGHT = ['right', 'go right']
    STOP = ['stop', 'brake']

class MindstormsGadget(AlexaGadget):
    """
    A Mindstorms gadget that performs movement based on voice commands.
    Two types of commands are supported, directional movement and preset.
    """

    def __init__(self):
        """
        Performs Alexa Gadget initialization routines and ev3dev resource allocation.
        """
        super().__init__()

        # Ev3dev initialization
        self.leds = Leds()
        self.sound = Sound()
        self.largeMotorOne = LargeMotor(OUTPUT_B)
        self.largeMotorTwo = LargeMotor(OUTPUT_C)
        self.mediumMotor = MediumMotor(OUTPUT_A)
        self.colorSensor = ColorSensor()

    def on_connected(self, device_addr):
        """
        Gadget connected to the paired Echo device.
        :param device_addr: the address of the device we connected to
        """
        self.leds.set_color("LEFT", "GREEN")
        self.leds.set_color("RIGHT", "GREEN")
        logger.info("{} connected to Echo device".format(self.friendly_name))

    def on_disconnected(self, device_addr):
        """
        Gadget disconnected from the paired Echo device.
        :param device_addr: the address of the device we disconnected from
        """
        self.leds.set_color("LEFT", "BLACK")
        self.leds.set_color("RIGHT", "BLACK")
        logger.info("{} disconnected from Echo device".format(self.friendly_name))

    def on_custom_mindstorms_gadget_control(self, directive):
        """
        Handles the Custom.Mindstorms.Gadget control directive.
        :param directive: the custom directive with the matching namespace and name
        """
        try:
            payload = json.loads(directive.payload.decode("utf-8"))
            print("Control payload: {}".format(payload), file=sys.stderr)
            control_type = payload["type"]

            if control_type == "pitch":
                self._pitch(payload["direction"], int(payload["angle"]))

            if control_type == "position":
                self._position(payload["position"], payload["direction"], int(payload["speed"]))

            if control_type == "stop":
                self._stop()

        except KeyError:
            print("Missing expected parameters: {}".format(directive), file=sys.stderr)

    def _stop(self):
        self.largeMotorOne.stop()
        self.largeMotorTwo.stop()
        self.mediumMotor.stop()

    def _pitch(self, direction, angle, is_blocking=False):
        """
        Pitches the camera up or down
        :param direction: up or down
        :param is_blocking: if set, motor run until duration expired before accepting another command
        """
        print("Pitch: ({}, {}, {})".format(direction, angle, is_blocking), file=sys.stderr)
        rotations = angle * .13
        print("Rotations: " + str(rotations), file=sys.stderr)
        if direction in Direction.UP.value:
            self.mediumMotor.on_for_rotations(SpeedPercent(100), rotations, False, block=is_blocking)

        if direction in Direction.DOWN.value:
            self.mediumMotor.on_for_rotations(SpeedPercent(-100), rotations, False, block=is_blocking)

    def _position(self, position="none", direction="forward", speed=100, is_blocking=False):
        """
        Moves the camera dolly on a continuous loop or to a color position if provided
        :param direction: up or down
        :param is_blocking: if set, motor run until duration expired before accepting another command
        """
        print("Position: ({}, {})".format(position, is_blocking), file=sys.stderr)

        if position != "none":
            while self.colorSensor.color_name != position:
                print("Color: " + self.colorSensor.color_name, file=sys.stderr)
                if direction in Direction.FORWARD.value:
                    self.largeMotorOne.on(SpeedPercent(-speed), False, block=is_blocking)
                    self.largeMotorTwo.on(SpeedPercent(speed), False, block=is_blocking)
                if direction in Direction.BACKWARD.value:
                    self.largeMotorOne.on(SpeedPercent(speed), False, block=is_blocking)
                    self.largeMotorTwo.on(SpeedPercent(-speed), False, block=is_blocking)
            self.largeMotorOne.stop()
            self.largeMotorTwo.stop()
        else:
            print("No Position.  Direction: " + direction, file=sys.stderr)
            if direction in Direction.FORWARD.value:
                    self.largeMotorOne.on(SpeedPercent(-speed), False, block=is_blocking)
                    self.largeMotorTwo.on(SpeedPercent(speed), False, block=is_blocking)
            if direction in Direction.BACKWARD.value:
                self.largeMotorOne.on(SpeedPercent(speed), False, block=is_blocking)
                self.largeMotorTwo.on(SpeedPercent(-speed), False, block=is_blocking)

        

if __name__ == '__main__':

    gadget = MindstormsGadget()

    # Set LCD font and turn off blinking LEDs
    os.system('setfont Lat7-Terminus12x6')
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")

    # Startup sequence
    gadget.sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
    gadget.leds.set_color("LEFT", "GREEN")
    gadget.leds.set_color("RIGHT", "GREEN")

    # Gadget main entry point
    gadget.main()

    # Shutdown sequence
    gadget.sound.play_song((('E5', 'e'), ('C4', 'e')))
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")
