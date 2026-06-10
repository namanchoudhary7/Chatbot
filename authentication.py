import bcrypt

def hash_password(plain_text_password: str)->bytes:
    password_bytes = plain_text_password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=password_bytes, salt=salt)

def check_password(plain_text_password: str, stored_hash: str)->bool:
    password_bytes = plain_text_password.encode('utf-8')
    stored_hash_bytes = bytes(stored_hash)
    return bcrypt.checkpw(password=password_bytes, hashed_password=stored_hash_bytes)
