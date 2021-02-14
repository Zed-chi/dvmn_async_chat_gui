import asyncio
import gui
import time
from listen_minechat import get_args as listen_args
from listen_minechat import read_msgs
from send_message import get_args as send_args
from send_message import send_message


async def main():
    listener_args = listen_args()
    sender_args = send_args()
    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    
    await asyncio.gather(
        send_message(sender_args, sending_queue),
        read_msgs(listener_args.host, listener_args.port, messages_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        loop=loop
    )
    

async def generate_msgs(q):
    while True:
        msg = round(time.time())
        q.put_nowait(msg)        
        await asyncio.sleep(1)
        

if __name__ == "__main__":        
    asyncio.run(main())
