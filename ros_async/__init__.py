from . import submodule


def test():
    print("ros_async")
    my_subm = submodule.Submodule([int, str], [int, str])

    @my_subm.websocket(bool)
    def my_coroutine(i: int) -> None:
        pass
