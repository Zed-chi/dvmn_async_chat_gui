import asyncio
import time
from datetime import datetime
from concurrent.futures._base import TimeoutError
from socket import gaierror

import aiofiles
import configargparse
from requests.exceptions import ConnectionError

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
        "--port", required=False, help="port of sender client", default=5000
    )
    parser.add(
        "--log_path",
        required=False,
        help="sender log path",
        default="./listener.log",
    )

    return parser.parse_args()


async def listen_chat(args):

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(args.host, args.port), timeout=5.0
    )

    try:
        while True:
            data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            message = data.decode("utf-8")
            now = datetime.now().strftime("[%d.%m.%y %H:%M]")
            if "history_path" in args:
                async with aiofiles.open(
                    args.history_path,
                    mode="a",
                    encoding="utf-8",
                ) as f:
                    await f.write(f"{now} {message}")
            print(f"{now} {message.strip()}")
    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    args = get_args()
    first_connection_lost = True
    while True:
        try:
            asyncio.run(listen_chat(args))
        except KeyboardInterrupt:
            print("Client disconnected")
            break
        except (ConnectionError, TimeoutError, gaierror):
            print("Connection lost... Reconnecting")
            if first_connection_lost:
                first_connection_lost = False
            else:
                time.sleep(5)
