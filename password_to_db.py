import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password
import ast

def verify_password(password, hashed_password):

    if isinstance(hashed_password, str):
        try:
            hashed_password = ast.literal_eval(hashed_password)
        except (SyntaxError, ValueError):
            pass

    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

