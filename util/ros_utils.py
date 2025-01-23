from typing import *
import interfaces_pkg.msg as astra_msgs


def convert_controller(data) -> astra_msgs.ControllerState:
    return astra_msgs.ControllerState(
        # triggers and bumpers
        lt=data.left_trigger,
        rt=data.right_trigger,
        lb=data.left_bumper,
        rb=data.right_bumper,
        # plus and minus
        plus=data.option,
        minus=data.share,
        # left stick
        ls_x=data.left_stick.x,
        ls_y=data.left_stick.y,
        # right stick
        rs_x=data.right_stick.x,
        rs_y=data.right_stick.y,
        # face buttons
        a=data.a,
        b=data.b,
        x=data.x,
        y=data.y,
        # dpad
        d_up=data.up,
        d_down=data.down,
        d_left=data.left,
        d_right=data.right,
    )
