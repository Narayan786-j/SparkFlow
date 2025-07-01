import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
import os
from dotenv import load_dotenv

BS = 16

# Load .env once during module load
load_dotenv()

# Lazy variables
_key = None
_iv = None
_salt = None
_private_key = None


def _load_env_vars():
    global _key, _iv, _salt

    if not (_key and _iv and _salt):
        _key = os.getenv("key")
        _iv = os.getenv("iv")
        _salt = os.getenv("salt")

        if not (_key and _iv and _salt):
            raise ValueError("❌ Missing key/iv/salt in environment variables.")


def get_private_key():
    global _private_key

    if _private_key is None:
        _load_env_vars()
        salt_bytes = _salt.encode("utf-8")
        kdf = PBKDF2(_key, salt_bytes, 64, 1000)
        _private_key = kdf[:32]

    return _private_key


def encrypt(raw: bytes) -> str:
    """
    Encrypts the given bytes using AES encryption in CBC mode.
    Returns a base64-encoded string.
    """
    key = get_private_key()
    iv_bytes = _iv.encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
    return base64.b64encode(cipher.encrypt(pad(raw, BS))).decode("utf-8")


def decrypt(enc: str) -> str:
    """
    Decrypts a base64-encoded string encrypted using AES (CBC).
    Returns a UTF-8 decoded string.
    """
    key = get_private_key()
    iv_bytes = _iv.encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
    decrypted = cipher.decrypt(base64.b64decode(enc))
    return unpad(decrypted, BS).decode("utf-8")
