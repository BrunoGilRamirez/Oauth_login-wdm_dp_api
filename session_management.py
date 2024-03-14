from sql_connectors import custom_connector, GCP_connector
from sqlalchemy.orm import sessionmaker


def get_session(env: str='', remote_hosting:bool=False) -> sessionmaker|None:
    if remote_hosting:
        conecction = GCP_connector(env)
    else:
        conecction = custom_connector(env)
    Session = sessionmaker(autocommit=False, autoflush=False,bind=conecction) # We create a sessionmaker for the remote database
    return Session