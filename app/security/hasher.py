import bcrypt


class SecureHasher:
    def __init__(self, bcrypt_cost: int):
        self._bcrypt_cost = bcrypt_cost

    def hash(self, secret: str) -> str:
        return bcrypt.hashpw(secret.encode(), bcrypt.gensalt(self._bcrypt_cost)).decode()

    def verify(self, secret: str, hashed: str) -> bool:
        return bcrypt.checkpw(secret.encode(), hashed.encode())
