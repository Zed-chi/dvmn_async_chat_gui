import asyncio
import gui
import time
from listen_minechat import get_args as view_args
from listen_minechat import read_msgs


async def main():
    args = view_args()
    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    
    await asyncio.gather(
        #generate_msgs(messages_queue),
        read_msgs(args.host, args.port, messages_queue),
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
