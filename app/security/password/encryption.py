from cryptography.fernet import Fernet, MultiFernet


class Encryption:
    def __init__(self, current_key: str, previous_key: str | None = None) -> None:
        fernet_keys = [Fernet(current_key)]
        if previous_key:
            fernet_keys.append(Fernet(previous_key))

        self.fernet = MultiFernet(fernet_keys)

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()

    def rotate(self, ciphertext: str) -> str:
        return self.fernet.rotate(ciphertext.encode()).decode()
