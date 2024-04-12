from sql_connectors import custom_connector, GCP_connector
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


def get_session(env: str='',verbose=True, override=True, interpolate=True) -> sessionmaker|None:

    if load_dotenv(env, verbose=verbose, override=override, interpolate=interpolate):
        print(f"The {env}.env file was loaded")
    if os.getenv("GCP_INSTANCE") and os.getenv("GCP_INSTANCE") != '':
        conecction = GCP_connector()
    else:
        conecction = custom_connector(env)
    Session = sessionmaker(autocommit=False, autoflush=False,bind=conecction) # We create a sessionmaker for the remote database
    return Session