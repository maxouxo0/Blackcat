import socket
import threading
import json

groups = {}

def get_group(conn):
    for group in groups.values():
        if conn in group["clients"]:
            return group
    return None

def handle_client(conn, addr):
    allowed_actions = ["SEND_MESSAGE", "REQUEST_SALT", "JOIN_CHANNEL", "CREATE_CHANNEL"]
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            data = json.loads(data.decode('utf-8'))

            if data.get("action") not in allowed_actions:
                conn.sendall(json.dumps({"action": "ERROR", "data": "Invalid request"}).encode('utf-8'))
                conn.close()
                return

            if data["action"] == "SEND_MESSAGE":
                group = get_group(conn)
                if group is None:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "Not in a group"}).encode('utf-8'))
                    conn.close()
                    return
                for client in group["clients"]:
                    if client != conn:
                        try:
                            client.sendall(json.dumps({"action": "SEND_MESSAGE", "data": data["data"]}).encode('utf-8'))
                        except (BrokenPipeError, ConnectionResetError):
                            group["clients"].remove(client)

            elif data["action"] == "REQUEST_SALT":
                if "uid" not in data:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "Invalid request"}).encode('utf-8'))
                    conn.close()
                    return
                if data["uid"] not in groups:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "UID not found"}).encode('utf-8'))
                    conn.close()
                    return
                conn.sendall(json.dumps({"action": "REQUEST_SALT", "data": groups[data["uid"]]["salt"]}).encode('utf-8'))

            elif data["action"] == "JOIN_CHANNEL":
                if "salt" not in data or "uid" not in data:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "Invalid request"}).encode('utf-8'))
                    conn.close()
                    return
                if data["uid"] not in groups:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "UID not found"}).encode('utf-8'))
                    conn.close()
                    return
                if data["salt"] != groups[data["uid"]]["salt"]:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "Invalid salt"}).encode('utf-8'))
                    conn.close()
                    return
                groups[data["uid"]]["clients"].append(conn)
                conn.sendall(json.dumps({"status": "success", "data": "Joined channel"}).encode('utf-8'))

            elif data["action"] == "CREATE_CHANNEL":
                if "salt" not in data or "uid" not in data:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "Invalid request"}).encode('utf-8'))
                    conn.close()
                    return
                if data["uid"] in groups:
                    conn.sendall(json.dumps({"action": "ERROR", "data": "UID already exist"}).encode('utf-8'))
                    conn.close()
                    return
                groups[data["uid"]] = {"clients": [conn], "salt": data["salt"]}
                conn.sendall(json.dumps({"status": "success", "data": "Channel created"}).encode('utf-8'))

        except (BrokenPipeError, ConnectionResetError):
            break
        except Exception as e:
            print(f"Erreur : {e}")
            break

    conn.close()
    for uid, group in list(groups.items()):
        if conn in group["clients"]:
            group["clients"].remove(conn)
            if len(group["clients"]) == 0:
                del groups[uid]
            break
    print('connexion fermée')

addr = ("0.0.0.0", 8080)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen()

print("[serveur] en écoute sur le port 8080...")

while True:
    conn, addr = s.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()