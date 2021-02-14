import asyncio
import time
import tkinter as tk
from tkinter import messagebox

import gui
from listen_minechat import get_args as listen_args
from listen_minechat import read_msgs
from send_message import get_args as send_args
from send_message import send_message, AuthError


async def main():
    listener_args = listen_args()
    sender_args = send_args()
    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    connection_queue = asyncio.Queue()

    await asyncio.gather(
        connection_routine(connection_queue),
        send_message(
            sender_args, sending_queue, status_updates_queue, connection_queue
        ),
        read_msgs(
            listener_args.host,
            listener_args.port,
            messages_queue,
            status_updates_queue,
            connection_queue,
        ),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        loop=loop,
    )


async def connection_routine(connection_queue):
    status = "Connection is alive"
    while True:
        now = round(time.time())
        msg = await connection_queue.get()
        print(f"[{now}] {status}. {msg}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AuthError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Ошибка", e)
