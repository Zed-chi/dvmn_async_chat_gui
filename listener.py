import asyncio
from datetime import datetime

import aiofiles

import configargparse

from gui import ReadConnectionStateChanged


CONFIG_FILEPATH = "./listener_config.cfg"


def get_args():
    parser = configargparse.ArgParser(
        default_config_files=[
            CONFIG_FILEPATH,
        ],
    )
    parser.add(
        "--host",
        required=False,
        help="host address",
        default="minechat.dvmn.org",
    )
    parser.add(
        "--port",
        required=False,
        help="port of sender client",
        default=5000,
    )

    return parser.parse_args()


async def read_msgs(
    host,
    port,
    queue,
    status_updates_queue,
    connection_queue,
    history_path=None,
):
    status_updates_queue.put_nowait(
        ReadConnectionStateChanged.INITIATED,
    )
    reader, writer = await asyncio.open_connection(host, port)
    status_updates_queue.put_nowait(
        ReadConnectionStateChanged.ESTABLISHED,
    )
    try:
        while True:
            data = await reader.readline()
            connection_queue.put_nowait("New message in chat")

            message = data.decode("utf-8")
            now = datetime.now().strftime("[%d.%m.%y %H:%M]")
            if history_path:
                async with aiofiles.open(
                    history_path,
                    mode="a",
                    encoding="utf-8",
                ) as f:
                    await f.write(f"{now} {message}")
            queue.put_nowait(message.strip())
    finally:
        writer.close()
        await writer.wait_closed()
