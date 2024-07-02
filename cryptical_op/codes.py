import string, secrets
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

def simple_code (x:int=10, y:int=8)->int:
    """
    Generates a random 8-digit code.
    Args: 
        - x: integer, this defines the range of the code, default is 10.
        - y: integer, this defines the length of the code, default is 8.
    Returns:
        - int: random 8-digit code
    """
    return secrets.randbelow(x**y) #generate a random 8-digit code


def alphan_code(length: int) -> str:
    """
    Generates a random alpha numeric string of the specified length.

    Args:
        - tamano (int): The length of the generated string.

    Returns:
        - str: A random string of the specified length.
    """

    caracteres = string.ascii_letters + string.digits + string.punctuation
    clave = ''.join(secrets.choice(caracteres) for _ in range(length))
    return clave

def create_session_secret( context: CryptContext , secret:str, metadata:str, client:str)->list[str,str,datetime]:
    """
    Generates a session secret code and returns a hashed version of the data along with the code and creation time.

    Args:
        - context (CryptContext): The passlib (is a password hashing library) context object.
        - secret (str): The secret value.
        - metadata (str): The metadata value.
        - client (str): The client value.

    Returns:
        - tuple: A tuple containing the hashed data, session code, and time created.
    """
    #generate a random number  of 20 digits
    code = str(secrets.randbelow(10**20))
    time_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {'secret':secret, 'metadata':metadata, 'client':client, 'session_code':code, 'time_created':time_created}
    return context.hash(str(data)), code, time_created