import tkinter as tk
from PIL import Image, ImageTk
import socket
import threading

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = ''
if not HOST:
    HOST = input("What is the host ip? (the ip the server.py output's on run)\n")
PORT = 55555

try:
    client.connect((HOST, PORT))
except ConnectionRefusedError:
    print("Could not connect to the server. Is it running?")
    exit()

stop_thread = False
nickname = ""

BG_COLOR = "#2C2F33"
TEXT_COLOR = "#FFFFFF"
INPUT_BG_COLOR = "#23272A"
BUTTON_COLOR = "#7289DA"
NICK_COLOR = "#7289DA"
SYSTEM_COLOR = "#FF0000"

root = tk.Tk()
root.title("Graphical TCP chat client")
root.configure(bg=BG_COLOR)

chat_frame = tk.Frame(root, bg=BG_COLOR)
chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

input_area = tk.Text(root, bg=INPUT_BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, height=3, wrap=tk.WORD)
input_area.pack(padx=10, pady=(0, 10), fill=tk.X, side=tk.LEFT, expand=True)

send_button = tk.Button(root, text="Send", bg=BUTTON_COLOR, fg=TEXT_COLOR, command=lambda: send_message())
send_button.pack(pady=(0, 10), padx=10, side=tk.RIGHT)

def load_avatar(image_path, size=(40, 40)):
    img = Image.open(image_path).resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)

avatar_img = load_avatar("avatar_placeholder.png")

def get_valid_nickname():
    global nickname
    nickname_prompt = tk.Toplevel(root)
    nickname_prompt.title("Choose a Nickname")
    nickname_prompt.configure(bg=BG_COLOR)

    prompt_label = tk.Label(nickname_prompt, text="Enter a nickname:", bg=BG_COLOR, fg=TEXT_COLOR)
    prompt_label.pack(padx=20, pady=10)

    nickname_input = tk.Entry(nickname_prompt, bg=INPUT_BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
    nickname_input.pack(pady=10, padx=20)

    def submit_nickname():
        global nickname
        nickname = nickname_input.get()
        nickname_prompt.destroy()

    submit_button = tk.Button(nickname_prompt, text="Submit", bg=BUTTON_COLOR, fg=TEXT_COLOR, command=submit_nickname)
    submit_button.pack(pady=10)

    nickname_prompt.transient(root)
    nickname_prompt.grab_set()
    root.wait_window(nickname_prompt)

get_valid_nickname()

def receive():
    global stop_thread
    while not stop_thread:
        try:
            message = client.recv(1024).decode()
            if message == 'NICK':
                client.send(nickname.encode())
            else:
                display_message(message)
        except OSError:
            stop_thread = True
            client.close()
            break
        except Exception as e:
            display_message(f"[SYSTEM] Error: {str(e)}")  
            stop_thread = True
            client.close()
            break

def display_message(full_message):
    message_frame = tk.Frame(chat_frame, bg=BG_COLOR)
    message_frame.pack(anchor='w', padx=10, pady=5, fill=tk.X)
    avatar_label = tk.Label(message_frame, image=avatar_img, bg=BG_COLOR)
    avatar_label.pack(side=tk.LEFT, padx=(0, 10))

    if ':' in full_message:
        nick, msg = full_message.split(':', 1)
        text_frame = tk.Frame(message_frame, bg=BG_COLOR)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nick_label = tk.Label(text_frame, text=nick.strip(), fg=NICK_COLOR, bg=BG_COLOR, font=('Helvetica', 10, 'bold'))
        nick_label.pack(anchor='w')
        msg_label = tk.Label(text_frame, text=msg.strip(), fg=TEXT_COLOR, bg=BG_COLOR, font=('Helvetica', 10))
        msg_label.pack(anchor='w')
    else:  
        system_label = tk.Label(message_frame, text=full_message, fg=SYSTEM_COLOR, bg=BG_COLOR, font=('Helvetica', 10, 'italic'))
        system_label.pack(anchor='w')

def send_message():
    global stop_thread
    try:
        message = input_area.get("1.0", tk.END).strip()
        if message:
            client.send(message.encode())
            input_area.delete("1.0", tk.END)
    except OSError:
        stop_thread = True
        client.close()

def on_key_press(event):
    if event.keysym == 'Return':
        if event.state & 0x0001:
            input_area.insert(tk.INSERT, '\n')
            return "break"
        else:
            send_message()
            return "break"

input_area.bind("<Return>", on_key_press)

receive_thread = threading.Thread(target=receive)
receive_thread.start()

root.mainloop()

stop_thread = True
try:
    client.close()
except OSError:
    print("Socket already closed.")