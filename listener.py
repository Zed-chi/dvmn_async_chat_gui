import asyncio
from datetime import datetime

import aiofiles


async def save_messages(log_path, logging_queue: asyncio.Queue):
    while True:
        async with aiofiles.open(
            log_path,
            mode="a",
            encoding="utf-8",
        ) as f:
            msg = await logging_queue.get()
            await f.write(msg + "\n")


async def read_msgs(
    connection,
    message_queue: asyncio.Queue,
    logging_queue: asyncio.Queue,
    watchdog_queue: asyncio.Queue,
):
    reader = connection["reader"]
    while True:
        data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        message = data.decode("utf-8")
        now = datetime.now().strftime("[%d.%m.%y %H:%M]")
        watchdog_queue.put_nowait("get")
        message_queue.put_nowait(f"{now} {message.strip()}")
        logging_queue.put_nowait(f"{now} {message.strip()}")
