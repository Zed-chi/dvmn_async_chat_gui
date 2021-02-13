import asyncio
import json
import logging

import aiofiles
import configargparse

CONFIG_FILEPATH = "./sender_config.cfg"


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
        "--port", required=False, help="port of sender client", default=5050,
    )
    parser.add("--token", help="token", required=False)
    parser.add(
        "--log_path",
        required=False,
        help="sender log path",
        default="./sender.log",
    )
    parser.add(
        "--name", required=False, help="name for registration", default="user",
    )
    parser.add("message", help="message to send")

    return parser.parse_args()


async def send_message(args):
    reader, writer = await asyncio.open_connection(args.host, args.port)

    data = await reader.readline()
    logging.info(data.decode())

    if args.token:
        await authorize(args.token, reader, writer)
    else:
        name = sanitize(args.name) if args.name else get_name_from_input()
        await register(name, reader, writer)

    try:
        message = sanitize(args.message)
        await submit_message(message, reader, writer)
    finally:
        writer.close()
        await writer.wait_closed()


async def submit_message(message, reader, writer):
    if not message:
        return
    writer.write(f"{message}\n\n".encode())
    await writer.drain()

    data = await reader.readline()
    logging.info(data.decode())


def get_name_from_input():
    while True:
        name = sanitize(input("Type a name to register: "))
        if name:
            return name


async def authorize(token, reader, writer):
    writer.write(f"{token}\n".encode())
    await writer.drain()

    data = await reader.readline()
    response_info = data.decode().strip()
    logging.info(f"respose is {response_info}")
    if not json.loads(response_info):
        raise ValueError("Invalid token. Check or register new.")


async def register(name, reader, writer):
    writer.write("\n".encode())
    await writer.drain()

    data = await reader.readline()
    logging.info(data.decode())

    writer.write(f"{name}\n\n".encode())
    await writer.drain()

    data = await reader.readline()
    info_json = data.decode().strip()
    user_info_dict = json.loads(info_json)
    await save_token(user_info_dict["account_hash"])

    writer.write("\n".encode())
    await writer.drain()

    data = await reader.readline()
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
