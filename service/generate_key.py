from Crypto.PublicKey import RSA


def generate_and_save_rsa_keys(public_key_path, private_key_path):
    # Generate a fresh key pair
    key = RSA.generate(4096)

    # Save the private key
    with open(private_key_path, "wb") as private_file:
        private_file.write(key.exportKey())

    # Save the public key
    with open(public_key_path, "wb") as public_file:
        public_file.write(key.publickey().exportKey())


# Example usage
generate_and_save_rsa_keys("../data/keys/public_key.pem", "../data/keys/private_key.pem")
