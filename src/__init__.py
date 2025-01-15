__version__ = "0.1.0"


def start():
    import asyncio
    from src.app import ros_loop, main

    future = asyncio.wait([ros_loop(), main()])
    asyncio.get_event_loop().run_until_complete(future)


def protoc():
    import subprocess
    from pathlib import Path
    import re

    # remove existing proto files
    print("Removing old Python ProtoBuf files")
    py_dir = Path("./src")
    for path in py_dir.glob("*_pb2.py"):
        path.unlink()
        print("\tremoved", path)

    # build new proto files
    print("Building new Python ProtoBuf files")
    subprocess.run(
        ["protoc", "--proto_path=./proto", "--python_out=./src"]
        + list(Path("./proto").glob("*.proto"))
    )

    # modify proto files to work in poetry
    # by default, imports of other protos look like `import protoname_pb2 ...`
    # but in a package, local imports need to use `.`, eg `from . import protoname_pb2 ...`
    print("Modifying new Python ProtoBuf files")
    py_paths = py_dir.glob("*_pb2.py")
    for path in py_paths:
        with open(path, "r") as file:
            contents = file.read()

        # add `from . ` to the start of lines that import other protobuf files
        modified_contents = re.sub(
            r"^(import \w+?_pb2 .+?)$",
            r"from . \1",
            contents,
            flags=re.M,
        )

        with open(path, "w") as file:
            file.write(modified_contents)

        print("\tmodified", path)
