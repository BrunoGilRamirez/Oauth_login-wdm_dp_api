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
print("-"*50)
sender.send_template_email(recipient="bruno.syko@gmail.com", 
                           subject="Test welcome email", 
                           template="welcome.html", 
                           context=type_of_context["welcome.html"]
                        )
print("-"*50)
sender.send_template_email(recipient="bruno.syko@gmail.com",
                            subject="Test new token email",
                            template="new_token.html",
                            context=type_of_context["new_token.html"]
                            )
print("-"*50)
sender.send_template_email(recipient="bruno.syko@gmail.com",
                            subject="Test new session email",
                            template="new_session.html",
                            context=type_of_context["new_session.html"]
                            )
print("-"*50)
sender.send_template_email(recipient="bruno.syko@gmail.com",
                            subject="Test password reset email",
                            template="password_reset.html",
                            context=type_of_context["password_reset.html"]
                            )
print("-"*50)