import asyncio
import time
from concurrent.futures._base import TimeoutError
from datetime import datetime
from socket import gaierror

import aiofiles
import configargparse
from gui import ReadConnectionStateChanged
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
        "--port", required=False, help="port of sender client", default=5000,
    )
    parser.add(
        "--log_path",
        required=False,
        help="sender log path",
        default="./listener.log",
    )

    return parser.parse_args()


async def read_msgs(
    host, port, queue, status_updates_queue, history_path=None,
):
    connection_lost = False
    while True:
        try:
            status_updates_queue.put_nowait(
                ReadConnectionStateChanged.INITIATED,
            )
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0,
            )
            status_updates_queue.put_nowait(
                ReadConnectionStateChanged.ESTABLISHED,
            )
            try:
                while True:
                    data = await asyncio.wait_for(
                        reader.readline(), timeout=5.0,
                    )
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
        except (ConnectionError, TimeoutError, gaierror):
            print("Connection lost... Reconnecting")
            status_updates_queue.put_nowait(ReadConnectionStateChanged.CLOSED)
            if connection_lost:
                connection_lost = True
            else:
                time.sleep(5)


if __name__ == "__main__":
    args = get_args()
    first_connection_lost = True
    while True:
        try:
            asyncio.run(read_msgs(args.host, args.port))
        except KeyboardInterrupt:
            print("Client disconnected")
            break
        except (ConnectionError, TimeoutError, gaierror):
            print("Connection lost... Reconnecting")
            if first_connection_lost:
                first_connection_lost = False
            else:
                time.sleep(5)
