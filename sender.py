import asyncio
import json

from gui import NicknameReceived


class TokenValidException(Exception):
    pass


async def send_message(
    connection,
    sending_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
):
    reader, writer = connection["reader"], connection["writer"]

    await reader.readline()

    while True:
        msg = await sending_queue.get()
        sanitized_message = sanitize(msg)
        await submit_message(sanitized_message, reader, writer)
        watchdog_queue.put_nowait("post")


async def submit_message(message, reader, writer):
    if not message:
        return
    writer.write(f"{message}\n\n".encode())
    await writer.drain()
    await reader.readline()


async def authorize(
    token,
    connection,
    status_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
):
    reader, writer = connection["reader"], connection["writer"]
    data = await reader.readline()
    writer.write(f"{token}\n".encode())
    await writer.drain()

    data = await reader.readline()
    response_info = data.decode().strip()

    if not json.loads(response_info):
        raise TokenValidException("Invalid token. Check or register new.")
    status_queue.put_nowait(
        NicknameReceived(json.loads(response_info)["nickname"]),
    )
    watchdog_queue.put_nowait("auth")


def sanitize(string):
    newstr = string
    for ch in ["\\n", "\\t", "\\r", "\\f", "\\b", "\\a", "\\"]:
        newstr = newstr.replace(ch, "")
    return newstr
