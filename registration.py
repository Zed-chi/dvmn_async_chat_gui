import asyncio
import json
import tkinter as tk
from tkinter.constants import DISABLED, NORMAL

from sender import sanitize


class RegistrationWindow:
    def __init__(self, config_path, host, port):
        self.config_path = config_path
        self.host = host
        self.port = int(port)
        self.root = tk.Tk()
        self.label = tk.Label(
            text="Токен не найден. Введите имя для регистрации."
        )
        self.label.pack()
        self.name_input = tk.Entry()
        self.name_input.bind("<KeyPress>", self.validateInput)
        self.name_input.pack()
        self.send_button = tk.Button(
            text="Далее", state=DISABLED, command=self.run_register
        )
        self.send_button.pack()
        self.root.mainloop()

    def validateInput(self, evt):
        text = self.name_input.get()
        sanitized_text = sanitize(text)

        evt.widget.delete(0, tk.END)
        evt.widget.insert(0, sanitized_text)
        if sanitized_text:
            self.send_button["state"] = NORMAL
        else:
            self.send_button["state"] = DISABLED

    def run_register(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.register())

    async def register(self):
        name = self.name_input.get()
        r, w = await asyncio.open_connection(self.host, self.port)
        try:
            print(await r.readline())
            w.write("\n".encode())
            print(await r.readline())
            w.write(f"{name}\n".encode())
            data = (await r.readline()).decode().split("\n")[0]
            user_dict = json.loads(data)
            self.save_token(user_dict["account_hash"])
        finally:
            w.close()
            await w.wait_closed()
            self.root.destroy()

    def save_token(self, account_hash):
        with open(self.config_path, mode="a", encoding="utf-8") as f:
            f.write(f"\ntoken={account_hash}")


if __name__ == "__main__":
    RegistrationWindow("qwe", "minechat.dvmn.org", 5050)
