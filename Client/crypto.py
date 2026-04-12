import os
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def hash_uid(uid):
    h = hashlib.sha256()
    h.update(uid.encode())
    return h.hexdigest()

def generate_salt():
    return os.urandom(16)

def derive_key(uid, salt):
    return hashlib.pbkdf2_hmac('sha256', uid.encode(), salt, 100000)

def encrypt(message, key):
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(message.encode(), AES.block_size))
    return base64.b64encode(iv + ct).decode('utf-8')

def decrypt(message, key):
    raw = base64.b64decode(message.encode())
    iv, ct = raw[:16], raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')