import tkinter as tk
from tkinter.constants import CHAR, DISABLED, NORMAL

def validateInput(evt):
    invalid_chars = "\'\"\\/?()_=*&^%$#@!.,`"
    text = nameInput.get()    
    normalized_text=""
    for i in text:
        if i not in invalid_chars:
            normalized_text+=i
        
    evt.widget.delete(0, tk.END)
    evt.widget.insert(0, normalized_text)
    if normalized_text:
        sendButton["state"] = NORMAL
    else:        
        sendButton["state"] = DISABLED    
def saveToken(filepath, value):
    with open(filepath, "a") as file:
        file.write(f"\ntoken={value}")

root = tk.Tk()
label=tk.Label(text="Токен не найден. Введите имя для регистрации.")
label.pack()
nameInput = tk.Entry()
nameInput.bind("<KeyPress>", validateInput)
nameInput.pack()
sendButton=tk.Button(text="Далее", state=DISABLED)
sendButton.pack()
root.mainloop()