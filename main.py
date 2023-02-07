import asyncio
import logging
import os
import time
from asyncio.exceptions import CancelledError
from concurrent.futures import TimeoutError
from socket import gaierror
from tkinter import messagebox, TclError

from anyio import create_task_group, run
from async_timeout import timeout

from config import CONFIG_FILEPATH, PING_SLEEPTIME, PING_TIMEOUT, TIMEOUT, args
from gui import (ReadConnectionStateChanged, SendingConnectionStateChanged,
                 TkAppClosed, draw)
from listener import read_msgs, save_messages
from registration import RegistrationWindow
from sender import TokenValidException, authorize, send_message

logging.basicConfig(
    level=logging.INFO,
    filename="client.log",
    format="%(levelname)s:watchdog:%(message)s",
)


connections = {
    "listener": {"reader": None, "writer": None},
    "sender": {"reader": None, "writer": None},
}

queues = {
    "messages": None,
    "logging": None,
    "sending": None,
    "status": None,
    "watchdog": None,
}


async def get_connection(host, port, status_queue, connection_type_enum):
    status_queue.put_nowait(connection_type_enum.INITIATED)
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port),
        timeout=TIMEOUT,
    )
    status_queue.put_nowait(connection_type_enum.ESTABLISHED)
    return reader, writer


async def init():
    logging.info("init cycle")

    listener_streams = await get_connection(
        args.host,
        args.listener_port,
        queues["status"],
        ReadConnectionStateChanged,
    )
    sender_streams = await get_connection(
        args.host,
        args.sender_port,
        queues["status"],
        SendingConnectionStateChanged,
    )

    connections["listener"]["reader"] = listener_streams[0]
    connections["listener"]["writer"] = listener_streams[1]
    connections["sender"]["reader"] = sender_streams[0]
    connections["sender"]["writer"] = sender_streams[1]
    await authorize(
        args.token,
        connections["sender"],
        queues["status"],
        queues["watchdog"],
    )


async def main():
    queues["messages"] = asyncio.Queue()
    queues["logging"] = asyncio.Queue()
    queues["sending"] = asyncio.Queue()
    queues["status"] = asyncio.Queue()
    queues["watchdog"] = asyncio.Queue()

    await load_history(args.history_path, queues["messages"])

    try:
        async with create_task_group() as tg:
            tg.start_soon(
                draw,
                queues["messages"],
                queues["sending"],
                queues["status"],
            )
            tg.start_soon(
                save_messages,
                args.history_path,
                queues["logging"],
            )
            tg.start_soon(handle_connection)
    except TimeoutError:
        logging.info("Watchdog detected time error")
    except TokenValidException:
        messagebox.showinfo(
            "Error",
            """
            Token is invalid, correct the value or delete
            it with key and program will create new
            """,
        )
    except CancelledError:
        logging.info("Cancelled via ctrl+c")
    except TkAppClosed:
        logging.info("Application closed")


async def load_history(filepath: str, queue: asyncio.Queue):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()
    lines = text.split("\n")
    for line in lines:
        queue.put_nowait(line)


async def watch_for_connection(queue: asyncio.Queue):
    while True:
        async with timeout(TIMEOUT):
            msg = await queue.get()
            stamp = time.strftime("%d.%m.%Y %H:%M:%S")
            logging.info(f"{stamp} watchdog: {msg}")


async def handle_connection():
    while True:
        try:
            logging.info("Connecting")
            await init()
            """
            Ожидание иницициализации из-за ошибки
            RuntimeError: readuntil() called while another coroutine
            is already waiting for incoming data
            """
            await asyncio.sleep(2)

            async with create_task_group() as tg:
                tg.start_soon(
                    read_msgs,
                    connections["listener"],
                    queues["messages"],
                    queues["logging"],
                    queues["watchdog"],
                )
                tg.start_soon(
                    send_message,
                    connections["sender"],
                    queues["sending"],
                    queues["watchdog"],
                )
                tg.start_soon(
                    watch_for_connection,
                    queues["watchdog"],
                )
                tg.start_soon(
                    ping_pong,
                    connections["sender"],
                    queues["watchdog"],
                )
        except TimeoutError:
            logging.info("Timeout error, reconnect")
        except gaierror:
            logging.info("Connection problems, reconnect")
        finally:
            logging.info("Closing connections")
            await close_writer_stream(
                connections["listener"]["writer"],
                queues["status"],
                ReadConnectionStateChanged,
            )
            await close_writer_stream(
                connections["sender"]["writer"],
                queues["status"],
                SendingConnectionStateChanged,
            )


async def close_writer_stream(
    writer_stream,
    status_queue: asyncio.Queue,
    stream_type,
):
    if writer_stream:
        writer_stream.close()
        await writer_stream.wait_closed()
    status_queue.put_nowait(stream_type.CLOSED)


async def ping_pong(connection, watchdog_queue: asyncio.Queue):
    reader, writer = connection["reader"], connection["writer"]
    while True:
        async with timeout(PING_TIMEOUT):
            writer.write("\n".encode())
            await writer.drain()
            await reader.readline()
            watchdog_queue.put_nowait("ping")
        await asyncio.sleep(PING_SLEEPTIME)


if __name__ == "__main__":
    try:
        if not args.token:
            window = RegistrationWindow(
                CONFIG_FILEPATH,
                args.host,
                args.sender_port,
            )
            window.run()
        else:
            run(main)
    except KeyboardInterrupt:
        logging.info("keyboard interrupt")
    except TclError:
        pass
