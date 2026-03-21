from cryptography.fernet import Fernet, InvalidToken

from app.security.password.encryption import Encryption


def test_encrypt_decrypt_round_trip():
    current_key = Fernet.generate_key().decode()
    encryption = Encryption(current_key=current_key)

    plaintext = "This is a secret message."
    ciphertext = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(ciphertext)

    assert decrypted == plaintext


def test_decrypt_with_previous_key():
    first_key = Fernet.generate_key().decode()
    encryption = Encryption(current_key=first_key)

    plaintext = "This is a secret message."
    ciphertext = encryption.fernet.encrypt(plaintext.encode()).decode()

    # generate new key
    new_key = Fernet.generate_key().decode()
    # set first key as previous key
    new_encryption = Encryption(current_key=new_key, previous_key=first_key)
    decrypted = new_encryption.decrypt(ciphertext)

    assert decrypted == plaintext


def test_rotate_changes_ciphertext_and_still_decryptable():
    plaintext = "This is a secret message."
    first_key = Fernet.generate_key().decode()
    encryption = Encryption(current_key=first_key)

    encrypted_data = encryption.encrypt(plaintext)

    # generate new key
    new_key = Fernet.generate_key().decode()
    # set first_key as previous key
    new_encryption = Encryption(current_key=new_key, previous_key=first_key)

    new_encrypted_data = new_encryption.rotate(encrypted_data)
    assert new_encrypted_data != encrypted_data

    decrypted_data = new_encryption.decrypt(new_encrypted_data)
    assert decrypted_data == plaintext


def test_decrypt_with_wrong_key_raises_InvalidToken():
    current_key = Fernet.generate_key().decode()
    encryption = Encryption(current_key=current_key)

    encrypted_data = encryption.encrypt("This is a secret message.")

    # create new encryption with different key
    wrong_key = Fernet.generate_key().decode()
    wrong_encryption = Encryption(current_key=wrong_key)

    try:
        wrong_encryption.decrypt(encrypted_data)
        assert False, "Expected InvalidToken exception"
    except InvalidToken:
        pass


def test_init_without_previous_key_works():
    current_key = Fernet.generate_key().decode()
    encryption = Encryption(current_key=current_key)

    plaintext = "This is a secret message."
    ciphertext = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(ciphertext)

    assert decrypted == plaintext

    rotated = encryption.rotate(ciphertext)
    assert rotated != ciphertext
    decrypted_rotated = encryption.decrypt(rotated)
    assert decrypted_rotated == plaintext
