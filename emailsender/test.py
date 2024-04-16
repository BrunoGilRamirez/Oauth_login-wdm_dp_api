from Sender import Sender
import os
from dotenv import load_dotenv
import datetime
type_of_context= {
    "welcome.html": {"username": "Bruno", 
                     "creation_date": datetime.datetime.now().strftime("%d/%m/%Y"),
                     "verification_link": "https://www.google.com"
                     },
    "new_token.html": {"username": "Bruno",
                        "creation_date": datetime.datetime.now().strftime("%d/%m/%Y"),
                        "new_token": "1234567890"
                        },
    "new_session.html": {"username": "Bruno",
                            "creation_date": datetime.datetime.now().strftime("%d/%m/%Y"),
                            "new_session": "1234567890"
                            },
    "password_reset.html": {"username": "Bruno",
                            "creation_date": datetime.datetime.now().strftime("%d/%m/%Y"),
                            "reset_link": "https://www.google.com"
                            },
}

load_dotenv(".env.local")
email = os.getenv('email')
password = os.getenv('password')
sender = Sender(email, password)
sender.send_template_email(recipient="bruno.syko@gmail.com", 
                           subject="Test1", 
                           template="welcome.html", 
                           context={
                               "username": "Bruno", 
                               "creation_date": datetime.datetime.now().strftime("%d/%m/%Y"),
                               "verification_link": "https://www.google.com"
                               }
                            )
print("Email sent")