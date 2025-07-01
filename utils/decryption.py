from Crypto import Random
from Crypto.Cipher import AES
from startStopJobApi.utils.properties import Properties
from startStopJobApi.utils.exceptions import Error
from pydantic import ValidationError
import base64
from hashlib import md5
import json

cfg = Properties()
BLOCK_SIZE = 16

def pad(data):
    length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)

    return data + (chr(length) * length).encode()


def unpad(data):
    return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]


def bytes_to_key(data, salt, output=48):
    # extended from https://gist.github.com/gsakkis/4546068

    assert len(salt) == 8, len(salt)

    data += salt

    key = md5(data).digest()

    final_key = key

    while len(final_key) < output:
        key = md5(key + data).digest()

        final_key += key

    return final_key[:output]


def encrypt(message, passphrase):
    salt = Random.new().read(8)

    key_iv = bytes_to_key(passphrase, salt, 32 + 16)

    key = key_iv[:32]

    iv = key_iv[32:]

    aes = AES.new(key, AES.MODE_CBC, iv)

    return base64.b64encode(b"Salted__" + salt + aes.encrypt(pad(message)))


def decrypt(encrypted, passphrase):
    encrypted = base64.b64decode(encrypted)

    assert encrypted[0:8] == b"Salted__"

    salt = encrypted[8:16]

    key_iv = bytes_to_key(passphrase, salt, 32 + 16)

    key = key_iv[:32]

    iv = key_iv[32:]

    aes = AES.new(key, AES.MODE_CBC, iv)

    return unpad(aes.decrypt(encrypted[16:]))


password = cfg.decryption_password.encode()


def decryptData(input):
    try:
        res = decrypt(input,password)
        return json.loads(res)
    except Exception:
        return None


def decryptInput(data: dict,model,env):
    if env == 'local' or "encryptedData" not in data:
        try:
            validate = model(**data)
            return validate
        except ValidationError as e:
            err = str(e).replace('\n',' ')
            raise Error(status_code=400,details=err)
        except Exception as e:
            print(e)
            raise Error(status_code=500,details="Something went wrong")
    else:
        try:
            res = decryptData(data['encryptedData'])
        except Exception as e:
            print(e)
            raise Error(status_code=500, details="Decryption Failure")
        try:
            validate = model(**res)
            return validate
        except ValidationError as e:
            err = str(e).replace('\n',' ')
            raise Error(status_code=400,details=err)
        except Exception as e:
            print(e)
            raise Error(status_code=500,details="Something went wrong")



def decryptInput2(data: dict,model,env,request):
    if env == 'local' or request.headers.get('byPassEncryption') == True or request.headers.get('byPassEncryption','').lower() == 'true':
        try:
            validate = model(**data)
            return validate
        except ValidationError as e:
            err = str(e).replace('\n',' ')
            raise Error(status_code=400,details=err)
        except Exception as e:
            print(e)
            raise Error(status_code=500,details="Something went wrong")
    else:
        try:
            res = decryptData(data['encryptedData'])
        except Exception as e:
            print(e)
            raise Error(status_code=500, details="Decryption Failure")
        try:
            validate = model(**res)
            return validate
        except ValidationError as e:
            err = str(e).replace('\n',' ')
            raise Error(status_code=400,details=err)
        except Exception as e:
            print(e)
            raise Error(status_code=500,details="Something went wrong")