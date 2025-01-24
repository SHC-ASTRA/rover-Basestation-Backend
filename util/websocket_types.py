# enums
from enum import Enum, auto as e_auto


# class syntax
class SubmoduleTypes(Enum):
    BASESTATION = 0
    CORE = 1
    ARM = 2
    AUTONOMY = 3
    BIOSENSOR = 4


class WebSocketDat:

    def __init__(self, data):
        if "submodule" not in data.keys():
            return
        self.submodule = data.submodule

    def verify_props(self, data, keys):
        # Check data to confirm all keys are in the data
        # and vice versa
        pass


class ControllerDat(WebSocketDat):

    def __init__(self, data):
        super().__init()
        super().verify_props(self.expected_keys)
        self.parse_to_properties(data)

    def parse_to_properties(self, data):
        pass

    expected_keys = [
        # The submodule to pass this data to
        "submodule",
        #
        ## Boolean Values
        # Buttons
        "a",
        "b",
        "x",
        "y",
        # Top bumpers
        "l_bumper",
        "l_bumper",
        # Analog stick presses
        # left analog press & right analog press
        "la_press",
        "ra_press",
        #
        ## Float values
        # Analog sticks values
        # left analog vector & right analog vector
        "la_vector",
        "ra_vector",
    ]
