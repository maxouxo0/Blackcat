import socket
import threading
import json
from crypto import hash_uid, generate_salt, derive_key, encrypt, decrypt

def receive_messages(sock, key):
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break
            payload = json.loads(data.decode())
            action = payload.get("action")
            if action == "SEND_MESSAGE":
                message = decrypt(payload["data"], key)
                print(message)
        except Exception:
            break

def main():
    host = input("IP du serveur : ")
    port = 8080
    uid = input("UID du groupe : ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    hashed_uid = hash_uid(uid)

    print("Que voulez vous faire ?")
    print("1. Rejoindre un canal")
    print("2. Créer un canal")
    choix = input("Votre choix : ")

    if choix == "1":
        sock.sendall(json.dumps({"action": "REQUEST_SALT", "uid": hashed_uid}).encode())
        response = json.loads(sock.recv(4096).decode())
        if response["action"] == "ERROR":
            print(f"Erreur : {response['data']}")
            return
        salt = response["data"]
        sock.sendall(json.dumps({"action": "JOIN_CHANNEL", "uid": hashed_uid, "salt": salt}).encode())
    elif choix == "2":
        salt = generate_salt().hex()
        sock.sendall(json.dumps({"action": "CREATE_CHANNEL", "uid": hashed_uid, "salt": salt}).encode())
    else:
        print("Choix invalide")
        return

    response = json.loads(sock.recv(4096).decode())
    key = derive_key(uid, bytes.fromhex(salt))

    threading.Thread(target=receive_messages, args=(sock, key), daemon=True).start()

    print("Connecté ! Tapez vos messages :")
    while True:
        try:
            message = input()
            if message:
                sock.sendall(json.dumps({"action": "SEND_MESSAGE", "data": encrypt(message, key)}).encode())
        except (BrokenPipeError, ConnectionResetError):
            print("Connexion perdue.")
            break

main()