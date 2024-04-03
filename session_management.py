from sql_connectors import custom_connector, GCP_connector
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


def get_session(env: str='', remote_hosting:bool=False,verbose=True, override=True, interpolate=True) -> sessionmaker|None:
    if load_dotenv(override=override, verbose=verbose, interpolate=interpolate):
        print("The .env file was loaded")
    elif load_dotenv(env, verbose=verbose, override=override, interpolate=interpolate):
        print(f"The {env}.env file was loaded")
    if remote_hosting:
        conecction = GCP_connector(env)
    else:
        conecction = custom_connector(env)
    Session = sessionmaker(autocommit=False, autoflush=False,bind=conecction) # We create a sessionmaker for the remote database
    return Session