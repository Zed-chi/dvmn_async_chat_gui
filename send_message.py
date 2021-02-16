import asyncio
import json
import logging

import aiofiles
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
    parser.add(
        "--log_path",
        required=False,
        help="sender log path",
        default="./sender.log",
    )
    parser.add(
        "--name",
        required=False,
        help="name for registration",        
    )
    parser.add("--message", help="message to send")

    return parser.parse_args()


async def send_message(
    args, sender_queue, status_updates_queue, connection_queue
):
    try:
        print(f"name = {args.name}")
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

            if args.token:
                await authorize(
                    args.token,
                    reader,
                    writer,
                    status_updates_queue,
                    connection_queue,
                )
            else:
                name = args.name if args.name else get_name_from_input()
                sanitized_name = sanitize(name)
                await register(
                    sanitized_name, reader, writer, connection_queue,status_updates_queue
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
    except AuthError:
        raise AuthError("")


async def submit_message(message, reader, writer, connection_queue):
    if not message:
        return
    writer.write(f"{message}\n\n".encode())
    await writer.drain()

    data = await reader.readline()
    connection_queue.put_nowait("Message accepted")
    logging.info(data.decode())


def get_name_from_input():
    while True:
        name = input("Type a name to register: ").strip()
        if name:
            return name


async def authorize(
    token, reader, writer, status_updates_queue, connection_queue
):
    writer.write(f"{token}\n".encode())
    await writer.drain()

    data = await reader.readline()
    response_info = data.decode().strip()
    connection_queue.put_nowait("Auth info response")
    logging.info(f"respose is {response_info}")

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


async def register(name, reader, writer, connection_queue, status_updates_queue):
    writer.write("\n".encode())
    await writer.drain()

    data = await reader.readline()
    connection_queue.put_nowait("Auth name question")
    logging.info(data.decode())

    writer.write(f"{name}\n\n".encode())
    await writer.drain()

    data = await reader.readline()
    connection_queue.put_nowait("Auth info response")
    info_json = data.decode().strip()
    user_info_dict = json.loads(info_json)
    await save_token(user_info_dict["account_hash"])
    status_updates_queue.put_nowait(
        NicknameReceived(user_info_dict["nickname"]),
    )

    writer.write("\n".encode())
    await writer.drain()

    data = await reader.readline()
    connection_queue.put_nowait("welcome message after registration")
    logging.info(data.decode())


async def save_token(account_hash):
    async with aiofiles.open(CONFIG_FILEPATH, mode="a", encoding="utf-8") as f:
        await f.write(f"\ntoken={account_hash}")


def sanitize(string):
    newstr = string
    for ch in ["\\n", "\\t", "\\r", "\\f", "\\b", "\\a", "\\"]:
        newstr = newstr.replace(ch, "")
    return newstr


if __name__ == "__main__":
    args = get_args()

    logging.basicConfig(
        level=logging.INFO,
        filename=args.log_path,
        format="%(levelname)s:sender:%(message)s",
    )

    try:
        asyncio.run(send_message(args))
    except KeyboardInterrupt:
        logging.info("Client disconnected")
    except ValueError:
        logging.warning("Invalid token. Check or register new.")
