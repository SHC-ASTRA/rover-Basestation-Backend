# rover-Basestation-Backend

This repository contains a Python AIOHTTP app to communicate with the web app
and the rover.

## Architecture

Generally, there are two parts to the architecture of Backend. There is the
custom ROS wrapper and there is aiohttp.

### aiohttp

Aiohttp is an asynchronous HTTP server for Python. We use it to communicate with
the frontend. Communication is done over a websocket using JSON strings.

## Running

To run the project, use this command:

```bash
poetry run start
```
