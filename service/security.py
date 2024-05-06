import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def generate_aes_key(size=32):
    """Generate a random AES key. Default size is for AES-256."""
    return get_random_bytes(size)

def encrypt_with_aes(key, data):
    # Create a new IV for each encryption
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data.encode(), AES.block_size))

    # We return both the IV (needed for decryption) and the encrypted data
    return base64.b64encode(iv + encrypted_data).decode()


def decrypt_with_aes(key, encoded_encrypted_data):
    decoded_data = base64.b64decode(encoded_encrypted_data)
    # Extract the IV which was concatenated before the data
    iv = decoded_data[:16]
    encrypted_data = decoded_data[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return data.decode()

def encrypt_key_with_rsa(public_key_path, aes_key):
    with open(public_key_path, 'r') as key_file:
        public_key = RSA.importKey(key_file.read())
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_aes_key = cipher.encrypt(aes_key)
    return encrypted_aes_key

def decrypt_key_with_rsa(private_key_path, encrypted_aes_key):
    with open(private_key_path, 'r') as key_file:
        private_key = RSA.importKey(key_file.read())
    cipher = PKCS1_OAEP.new(private_key)
    aes_key = cipher.decrypt(encrypted_aes_key)
    return aes_key

if __name__=="__main__":
    # 1. Encryption
    data = "Hello, World!"
    aes_key = generate_aes_key()
    encrypted_data = encrypt_with_aes(aes_key, data)
    encrypted_aes_key = encrypt_key_with_rsa("../data/keys/public_key.pem", aes_key)
    base64_encrypted_aes_key = base64.b64encode(encrypted_aes_key).decode()

    print(encrypted_data)
    print(base64_encrypted_aes_key)

    # 2. Decryption
    decrypted_aes_key = decrypt_key_with_rsa("../data/keys/private_key.pem", base64.b64decode(base64_encrypted_aes_key))
    decrypted_data = decrypt_with_aes(decrypted_aes_key, encrypted_data)

    print(decrypted_data)  # Should output "Hello, World!"