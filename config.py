import configargparse

CONFIG_FILEPATH = "./config.cfg"
TIMEOUT = 40
PING_TIMEOUT = 20
PING_SLEEPTIME = 20


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
        "--listener_port",
        required=False,
        help="port of sender client",
        default=5000,
    )
    parser.add(
        "--sender_port",
        required=False,
        help="port of sender client",
        default=5050,
    )
    parser.add("--token", help="token", required=False)
    parser.add(
        "--history_path",
        required=False,
        help="messages log path",
        default="./history.log",
    )
    return parser.parse_args()


args = get_args()
