import asyncio
import gui
import time


async def main():
    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    
    await asyncio.gather(
        generate_msgs(messages_queue),
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