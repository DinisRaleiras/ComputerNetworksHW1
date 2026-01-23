"""

@author: Dinis Raleiras - 67819
@author: Filipe Nobre - 67850

"""
import socket 
import os
import sys
import pickle
import threading

OP_RRQ = 1    
OP_DAT = 3
OP_ACK = 4    
OP_ERR = 5 

BLOCK_SIZE = 512

def send_dat (client_socket, block_number, size, data):
    dat = {"opcode": 3, "block_number": block_number, "size": size, "data": data.encode()}
    client_socket.send(pickle.dumps(dat))

def send_error(client_socket, message):
    error = {"opcode": OP_ERR, "error": message.encode()}
    client_socket.send(pickle.dumps(error))

def send_directory_listing(client_socket):
    block_number = 1
    for path in os.listdir("."):
        if os.path.isfile(os.path.join(".", path)):
            filename = os.path.basename(path)
            send_dat(client_socket, block_number, len(filename), filename)
            response = pickle.loads(client_socket.recv(4096))
            if response["opcode"] == OP_ACK:
                if response["block_number"] == block_number:
                    block_number += 1
                else:
                    send_error(client_socket, "Invalid block number, closing connection")
                    client_socket.close()
                    return
                
    send_dat(client_socket, block_number, 0, "")
    response = pickle.loads(client_socket.recv(BLOCK_SIZE))
    if response["opcode"] == OP_ACK and response["block_number"] != block_number:
        send_error(client_socket, "Invalid block number, closing connection")
        client_socket.close()

def send_file(client_socket, filename):
    if not os.path.exists(filename):
        send_error(client_socket, "File not found")
        return
    block_number = 1
    with open(filename, "r") as f:
        while True:
            data = f.read(BLOCK_SIZE)
            send_dat(client_socket, block_number, len(data), data)
            response = pickle.loads(client_socket.recv(4096))
            if response["opcode"] == OP_ACK:
                if response["block_number"] == block_number:
                    block_number += 1
                    if len(data) < BLOCK_SIZE:
                        break
                else:
                    send_error(client_socket, "Invalid block number, closing connection")
                    client_socket.close()
                    return

def handle_client(client_socket, client_address, server_ip):
    print(f"New connection from {client_address}")
    try:
        greeting = f"Welcome to {server_ip} file server"
        send_dat(client_socket, 0, len(greeting), greeting)

        while True:
            response = pickle.loads(client_socket.recv(4096))
            if not response or response["opcode"] == 4:
                break
        
        while True:
            request = pickle.loads(client_socket.recv(4096))
            if request["opcode"] == OP_RRQ:
                filename = request["filename"].decode()
                if filename == "":
                    send_directory_listing(client_socket)
                else:
                    send_file(client_socket, filename)
            else:
                send_error(client_socket, "Protocol error, Connection closed")
                break

    except Exception:
        print(f"Connection with {client_address} lost")
    finally:
        client_socket.close()

def main(serverIP, serverPort):
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((serverIP, serverPort))
        serverSocket.listen(5)
        print("Server is running")
    except Exception:
        print("Unable to start server")
        sys.exit(1) 

    while True:
        client_socket, client_address = serverSocket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, serverIP), daemon=True)
        client_thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_addr> <server_port>")
        sys.exit(1)

    serverAddr = sys.argv[1]
    serverPort = int(sys.argv[2])

    main(serverAddr, serverPort)