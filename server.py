import threading
import socket
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

class Client():
    def __init__(self, clientSocket, name=None, isAdmin=False):
        self.clientSocket = clientSocket
        self.nickname = name
        self.isAdmin = isAdmin

clients = []

def remove_disconnected(client: Client):
    clients.remove(client)
    client.clientSocket.close()
    broadcast(f'{client.nickname} has left!'.encode())

def ask_to_leave(client: Client, msg):
    client.clientSocket.send(f'LEAVE_CHAT:{msg}'.encode())

def broadcast(message):
    for client in clients:
        client.clientSocket.send(message)

def handle(client: Client):
    while True:
        try:
            message = client.clientSocket.recv(1024)
            if not message:
                break
            decoded_message = message.decode()
            if not decoded_message.startswith('/'):
                message = f"[ADMIN] {client.nickname}: {decoded_message}".encode() if client.isAdmin else f"{client.nickname}: {decoded_message}".encode()
                broadcast(message)
                continue

            command = decoded_message.split(' ')
            opcode = command[0]
            args = command[1:]

            if opcode.lower() == '/whisper':
                message_to_target = ' '.join(args[1:])
                if message_to_target.isspace() or message_to_target == '':
                    client.clientSocket.send("You can't send an empty message!".encode())
                    continue

                whisperingTargetExists = False
                for possibleWhisperTarget in clients:
                    if possibleWhisperTarget.nickname == args[0]:
                        if possibleWhisperTarget == client:
                            client.clientSocket.send("You can't whisper to yourself!".encode())
                            continue

                        possibleWhisperTarget.clientSocket.send(f'{client.nickname} whispered you: {message_to_target}'.encode())
                        client.clientSocket.send(f'You whispered "{message_to_target}" to {possibleWhisperTarget.nickname}'.encode())
                        whisperingTargetExists = True

                if not whisperingTargetExists:
                    client.clientSocket.send("Target doesn't exist!".encode())
                    continue

            elif opcode.lower() == '/kick':
                if not client.isAdmin:
                    client.clientSocket.send("You don't have permissions to do that!".encode())
                    continue

                if args[0].isspace() or args[0] == '':
                    client.clientSocket.send("You have to specify a target!".encode())
                    continue

                if args[0] == client.nickname:
                    client.clientSocket.send("You can't kick yourself!".encode())
                    continue

                kickingTargetExists = False
                for possibleKickingTarget in clients:
                    if possibleKickingTarget.nickname == args[0]:
                        ask_to_leave(possibleKickingTarget, "You got kicked!")
                        client.clientSocket.send(f"You successfully kicked {possibleKickingTarget.nickname}!".encode())
                        kickingTargetExists = True

                if not kickingTargetExists:
                    client.clientSocket.send(f"Target doesn't exist".encode())

            else:
                client.clientSocket.send('Invalid command!'.encode())

        except Exception as e:
            break
    remove_disconnected(client)

def receive():
    print('Listening on', HOST, PORT)

    while True:
        try:
            clientSocket, address = server.accept()
            client = Client(clientSocket=clientSocket)
            print(f'Connected with {str(address)}')

            client.clientSocket.send("NICK".encode())
            nickname = client.clientSocket.recv(1024).decode()

            if clients == []:
                client.isAdmin = True
                client.clientSocket.send("You are now Admin!".encode())

            client.nickname = nickname
            clients.append(client)

            print(f'Nickname of the client is {nickname}!')
            broadcast(f'[ADMIN] {nickname} joined the chat!'.encode() if client.isAdmin else f'{nickname} joined the chat!'.encode())
            time.sleep(0.1)
            client.clientSocket.send('Connected to the server!'.encode())

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    receive()