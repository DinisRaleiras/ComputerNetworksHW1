"""

@author: Dinis Raleiras - 67819
@author: Filipe Nobre - 67850

"""
import socket
import pickle
import os
import sys

OP_RRQ = 1    
OP_DAT = 3
OP_ACK = 4    
OP_ERR = 5 

BLOCK_SIZE = 512

def send_ack(sock, block_number):
    ack_packet = {"opcode": OP_ACK, "block_number": block_number}
    sock.send(pickle.dumps(ack_packet))

def send_rrq(sock, filename):
    rrq_packet = {"opcode": OP_RRQ, "filename": filename.encode()}
    sock.send(pickle.dumps(rrq_packet))

def get_file(sock, remote_filename, local_filename):
    if os.path.exists(local_filename):
        print("File already exists in the system")
        return

    send_rrq(sock, remote_filename)

    with open(local_filename, "wb") as f:
        while True:
            response = pickle.loads(sock.recv(4096))
            
            if response["opcode"] == 5:
                print(response["error"].decode())
                os.remove(local_filename)
                break

            elif response["opcode"] == 3:
                f.write(response["data"])
                send_ack(sock, response["block_number"])
                
                if response["size"] < BLOCK_SIZE:
                    print("File transfer completed")
                    break

def list_dir(sock):
    send_rrq(sock, "")
    while True:
        response = pickle.loads(sock.recv(4096))
        if response["opcode"] == 5:
            print(response["error"].decode())
            break
        elif response["opcode"] == 3:
            if response["size"] == 0:
                send_ack(sock, response["block_number"])
                break
            else:
                print(response["data"].decode())
                send_ack(sock, response["block_number"])

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_addr> <server_port>")
        return

    server_addr = sys.argv[1]
    server_port = int(sys.argv[2])

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_sock.connect((server_addr, server_port))
        print("Connect to server")
    except Exception :
        print("Unable to connect with the server")
        return

    greeting = pickle.loads(client_sock.recv(4096))
    print(greeting["data"].decode())
    send_ack(client_sock, 1)

    while True:
        cmd = input("client> ").strip().split()
        if not cmd:
            print("...")
        elif cmd[0] == "end":
            client_sock.close()
            print("Connection close, client ended")
            break
        elif cmd[0] == "dir":
            list_dir(client_sock)
            print("...")
        elif cmd[0] == "get":
            if(len(cmd) != 3):
                print("Usage: get <remote_filename> <local_filename>")
                continue
            get_file(client_sock, cmd[1], cmd[2])
            print("...")
        else:
            print("Unknown command")
            print("...")

if __name__ == "__main__":
    main()
