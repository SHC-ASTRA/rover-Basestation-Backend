# Type hinting
from typing import *

# Data processing
import json

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
    def __init__(self, raw_data: str):
        values = dict
        try:
            values = json.loads(raw_data)
        except:
            LOG.error(
                f'Attempted to parse invalid data "{raw_data}" as JSON for Vector2'
            )
        self.x = float(values["x"])
        self.y = float(values["y"])


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
        LOG.debug(f"Initalized ExpectedKeys item with type {self.ex_type}")

    def validate_tup(self, in_data: Tuple[str, Any]) -> bool:
        # in_data is expected to be an item from
        # a dict.items call

        # Get the value rather than the key
        in_value = in_data[1]
        # Process into the type
        try:
            proc_val = self.ex_type(in_value)
        except Exception as e:
            LOG.error(f"Failed to process {in_data[0]}: {in_value} as {str(type)}")
            LOG.error(f"{e}")
            return False

        # Return if the input datatype is equivalent to
        # the expected data type

        # A non-empty Tuple evaluates to a Truthy value
        # This allows for error checking if this function returns false
        return (in_data[0], proc_val)

    def validate_single_val(self, in_value: Any) -> bool:
        # Validate without providing the key name
        return self.validate_tup((None, in_value))

    # Used for checking "in"
    def __contains__(self, key):
        return key in self.ex_keys

    # When evaluated as an iterator
    def __iter__(self):
        for key in self.ex_keys:
            yield key


class WebSocketData:

    def __init__(self, raw_data: dict):
        self.loaded_data = json.loads(raw_data)
        # It is necessary that a submodule is provided at minimum
        if "submodule" not in self.loaded_data.keys():
            return

    def subset_of_expected(self, ex_keys: list[ExpectedKeys]) -> bool:
        # Some cursed list comprehension to
        # get the concatenation of all expected keys
        all_expected_keys = [key for instance in ex_keys for key in instance]
        """ Equivalent to
            for instance in ex_keys list:
                for key in instance
                    append_to_list(key)
        """

        # Convert the expected keys to a set
        expected_keys_set = set(all_expected_keys)
        # Get the keys of the loaded data
        loaded_keys_set = set(self.loaded_data.keys())
        # Actually check if all expected keys are in the loaded data
        return expected_keys_set.issubset(loaded_keys_set)

    def verify_props(self, data: dict, ex_keys_list: list[ExpectedKeys]):
        # Check data to confirm all keys are in the data
        # and vice versa
        ex_is_subset = self.subset_of_expected(ex_keys_list)
        if not ex_is_subset:
            LOG.warning(
                "There was an error the expected keys as a subset of the loaded data"
            )
            return False

        for input_key, input_value in data.items():
            # Current out of loop scope iterator
            # for expected keys argument
            # Predefined, but not with the correct value
            current_keys_expected = ExpectedKeys
            # Loop through the expected keys,
            # and confirm that the property exists
            for expected_keys_item in ex_keys_list:
                # Assign out of loop scope iterator
                current_keys_expected = expected_keys_item
                # Check if iterator is currently where
                # the key is
                if input_key in current_keys_expected:
                    # If it has been found, break out
                    break
            # If there is a key present in the data,
            # and we have reached the end, but
            # it is not expected to be present
            # return False
            if input_key not in current_keys_expected:
                # Could not find the value in the input data
                LOG.warning(f"{input_key} exists in input data but not expected keys")
                # Skip this value
                continue
            # Check if the value is of the correct type,
            # convert to its correct type
            new_value = current_keys_expected.validate_single_val(input_value)
            if not new_value:
                LOG.warning(f"Could not validate data {input_key}: {input_value}")
                return False
            self.loaded_data[input_key] = new_value[1]
        return True


# Represents a single message from a controller socket
class ControllerData(WebSocketData):

    def __init__(self, raw_data: dict):

        LOG.debug("Initalizing parent data ExpectedKeys in ControllerData")

        super().__init__(raw_data)

        LOG.debug("Attempting to process data into controller.")

        if not super().verify_props(self.loaded_data, self.controller_keys):
            LOG.error(f"There was an error verifying the props for controller data.")
            raise TypeError

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
                # Middle buttons
                "option",
                "share",
                # d-pad
                "up",
                "down",
                "left",
                "right",
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
        # Analog trigger value
        ExpectedKeys(
            [
                "left_trigger",
                "right_trigger",
            ],
            float,
        ),
    ]
