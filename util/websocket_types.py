# Type hinting
from typing import *

# enums
from enum import Enum

# logging
import inspect
import logging

LOG = logging.getLogger(__name__)

# fmt: off
# Enumerable for sending data
class SubmoduleTypes(Enum):
    BASESTATION = "basestation"
    CORE        = "core"
    ARM         = "arm"
    AUTONOMY    = "autonomy"
    BIOSENSOR   = "biosensor"
# fmt: on


# 2d vector, for thumbsticks
class Vector2:
    def __init__(self, x_in: float, y_in: float):
        self.x = x_in
        self.y = y_in


# Acts to ensure that where expected keys are
# uniform when created.
# Simply returns a tuple of a list and type
class ExpectedKeys:
    # Provided with a list of keys names and their expected values
    def __init__(self, in_ex_keys: Union[List[str] | Set[str]], in_ex_type: type):
        # Ensure that there are no duplicates if a list
        if type(in_ex_keys) is list and len(set(in_ex_keys)) != len(in_ex_keys):
            # Get the parent caller
            parentCallerFrame = inspect.getouterframes(inspect.currentframe(), 2)
            LOG.warning(
                f"ExpectedKeys called from {parentCallerFrame[1][0]} with duplicate keys"
            )

        self.ex_keys = in_ex_keys
        self.ex_type = in_ex_type

    def validate_tup(self, in_data: Tuple[str, Any]) -> bool:
        # in_data is expected to be an item from
        # a dict.items call

        # fmt: off
        # Get the value rather than the key
        in_value = in_data[1]
        # For readability sake
        in_type  = type(in_value)
        # fmt: on

        # Return if the input datatype is equivalent to
        # the expected data type
        return in_type is self.ex_type

    def validate_single_val(self, in_value: Any) -> bool:
        return self.validate_tup((None, in_value))

    def __contains__(self, key):
        return key in self.ex_keys

    def __iter__(self):
        return self.ex_keys


class WebSocketData:

    def __init__(self, data):
        if "submodule" not in data.keys():
            return
        self.submodule = data.submodule

    def verify_props(self, data: dict, ex_keys: list[ExpectedKeys]):
        # Check data to confirm all keys are in the data
        # and vice versa
        for key_iterator, value_iterator in data.items():
            # Current out of loop scope iterator
            # for expected keys argument
            c_keys_ex = ExpectedKeys
            # Loop through the expected keys,
            # and confirm that the property exists
            for index in ex_keys:
                # Assign out of loop scope iterator
                c_keys_ex = ex_keys[index]
                # Check if iterator is currently where
                # the key is
                if key_iterator in c_keys_ex:
                    # If it has been found, break out
                    break
            # If there is a key present in the data,
            # and we have reached the end, but
            # it is not expected to be present
            # return False
            if key_iterator not in c_keys_ex:
                return False

            # Check if the value is of the correct type
            if not c_keys_ex.validate_single_val(value_iterator):
                return False
        return True


class ControllerData(WebSocketData):

    def __init__(self, data):
        super().__init__(data)
        if not super().verify_props(data, self.expected_keys):
            raise TypeError
        self.data = data

    controller_keys = [
        # The submodule to pass this data to
        ExpectedKeys(["submodule"], str),
        # Boolean values
        ExpectedKeys(
            {
                # Buttons
                "a",
                "b",
                "x",
                "y",
                # Top bumpers
                # left bumper & right bumper
                "l_bumper",
                "r_bumper",
                # Analog stick presses
                # left analog press & right analog press
                "la_press",
                "ra_press",
            },
            bool,
        ),
        # Analog sticks values
        # left analog vector & right analog vector
        ExpectedKeys(
            [
                "la_vector",
                "ra_vector",
            ],
            Vector2,
        ),
    ]
