import asyncio
import json
import logging

import configargparse

from gui import NicknameReceived, SendingConnectionStateChanged

CONFIG_FILEPATH = "./sender_config.cfg"


class AuthError(Exception):
    pass


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
        default=5050,
    )
    parser.add("--token", help="token", required=False)    
    return parser.parse_args()


async def send_message(
    args, sender_queue, status_updates_queue, connection_queue
):
    status_updates_queue.put_nowait(
        SendingConnectionStateChanged.INITIATED,
    )
    reader, writer = await asyncio.open_connection(
        args.host,
        args.port,
    )
    status_updates_queue.put_nowait(
        SendingConnectionStateChanged.ESTABLISHED,
    )
    try:
        data = await reader.readline()
        connection_queue.put_nowait("Prompt before auth")
        logging.info(data.decode())

        await authorize(
            args.token,
            reader,
            writer,
            status_updates_queue,
            connection_queue,
        )

        while True:
            message = await sender_queue.get()
            sanitized_message = sanitize(message)
            await submit_message(
                sanitized_message, reader, writer, connection_queue
            )
    finally:
        status_updates_queue.put_nowait(
            SendingConnectionStateChanged.CLOSED,
        )
        writer.close()
        await writer.wait_closed()


async def submit_message(message, reader, writer, connection_queue):
    if not message:
        return
    writer.write(f"{message}\n\n".encode())
    await writer.drain()

    await reader.readline()
    connection_queue.put_nowait("Message accepted")


async def authorize(
    token, reader, writer, status_updates_queue, connection_queue
):
    writer.write(f"{token}\n".encode())
    await writer.drain()

    data = await reader.readline()
    response_info = data.decode().strip()
    connection_queue.put_nowait("Auth info response")

    user_info_dict = json.loads(response_info)
    if not user_info_dict:
        raise AuthError("Invalid token. Check or register new.")
    else:
        print(
            f"Выполнена авторизация. Пользователь {user_info_dict['nickname']}.",
        )
        status_updates_queue.put_nowait(
            NicknameReceived(user_info_dict["nickname"]),
        )


def sanitize(string):
    newstr = string
    for ch in ["\\n", "\\t", "\\r", "\\f", "\\b", "\\a", "\\"]:
        newstr = newstr.replace(ch, "")
    return newstr
