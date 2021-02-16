import asyncio
import time
import tkinter as tk

from concurrent.futures._base import TimeoutError
from socket import gaierror
from tkinter import messagebox
from tkinter.constants import DISABLED, NORMAL

import gui
from anyio import create_task_group, run
from async_timeout import timeout
from listen_minechat import get_args as listen_args
from listen_minechat import read_msgs
from requests.exceptions import ConnectionError
from send_message import get_args as send_args
from send_message import send_message, AuthError, CONFIG_FILEPATH, register
from gui import TkAppClosed
from registration import RegistrationWindow


class EmptyTokenError(Exception):
    pass

async def main():
    try:
        listener_args = listen_args()
        sender_args = send_args()

        if not sender_args.token:
            raise EmptyTokenError()
        
        messages_queue = asyncio.Queue()
        sending_queue = asyncio.Queue()
        status_updates_queue = asyncio.Queue()

        async with create_task_group() as tg:
            await tg.spawn(handle_connection, messages_queue, sending_queue, status_updates_queue, listener_args,sender_args)
            await tg.spawn(gui.draw, messages_queue, sending_queue, status_updates_queue)

    except (KeyboardInterrupt, TkAppClosed):
        print("app closed")    


async def connection_routine(connection_queue):
    status = "Connection is alive"
    while True:
        async with timeout(5) as cm:
            msg = await connection_queue.get()
            now = round(time.time())
            print(f"[{now}] {status}. {msg}")        


async def ping_pong(args):    
    while True:
        async with timeout(60) as cm:
            reader, writer = await asyncio.open_connection(
                args.host,
                args.port,
            )
            writer.write("\n".encode())
            await writer.drain()
            await reader.readline()
            await asyncio.sleep(10)



async def handle_connection(
    messages_queue, sending_queue, status_updates_queue, listener_args,sender_args
):    
    connection_queue = asyncio.Queue()
    sender_args = send_args()
    while True:
        try:
            async with create_task_group() as tg:
                await tg.spawn(
                    send_message,
                    sender_args, sending_queue, status_updates_queue, connection_queue
                )
                await tg.spawn(
                    ping_pong,
                    sender_args,                    
                )                
                await tg.spawn(
                    read_msgs,
                    listener_args.host,
                    listener_args.port,
                    messages_queue,
                    status_updates_queue,
                    connection_queue,
                )
                await tg.spawn(connection_routine, connection_queue)
        except (ConnectionError, TimeoutError, gaierror):
            now = round(time.time())
            print(f"[{now}] 1s timeout is elapsed")            
            print("Connection lost... Reconnecting")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except EmptyTokenError:
        RegistrationWindow(CONFIG_FILEPATH, send_args().host,send_args().port)
    except AuthError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Ошибка", e)    