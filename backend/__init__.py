__version__ = "0.1.0"
import coloredlogs, logging
import os

coloredlogs.install(level=os.environ.get("LOG_LEVEL", "INFO"))
LOG = logging.getLogger(__name__)


def start():
    from backend.app import main

    main()


def build():
    import subprocess
    from pathlib import Path
    from sys import stderr, stdout
    import re

    # remove existing proto files
    LOG.info("Removing old Python ProtoBuf files")
    py_dir = Path("./generated")
    for path in py_dir.glob("*_pb2.py"):
        path.unlink()
        LOG.debug(f"  Removed {path}")

    # build new proto files
    LOG.info("Building new Python ProtoBuf files")
    subprocess.run(
        [
            "protoc",
            "--proto_path=./proto",
            "--python_out=./generated",
            # also generate stubs for pylance https://github.com/nipunn1313/mypy-protobuf
            "--mypy_out=./generated",
        ]
        + [str(path) for path in Path("./proto").glob("*.proto")],
        check=True,
        stdout=stdout,
        stderr=stderr,
    )

    # modify proto files to work in poetry
    # by default, imports of other protos look like `import protoname_pb2 ...`
    # but in a package, local imports need to use `.`, eg `from . import protoname_pb2 ...`
    LOG.info("Modifying new Python ProtoBuf files")
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

        LOG.debug(f"  Modified {path}")


def test_client():
    from .test_client import ws_client
    import asyncio

    asyncio.run(ws_client())
