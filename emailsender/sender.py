import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import jinja2
from datetime import datetime

class Sender:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.smtp_server = 'smtp.office365.com'
        self.smtp_port = 587
        self.templates_path = 'templates/e-mails'
        

    def send_email(self, recipient:str, subject:str, message:str, type:str='plain')->bool:
        '''Enviar un correo electrónico simple.
        - recipient: str, dirección de correo del destinatario.
        - subject: str, asunto del correo.
        - message: str, cuerpo del correo.'''
        try:
            # Configurar el servidor SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)

            # Crear el mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(message, type, _charset='utf-8'))

            # Enviar el correo
            server.send_message(msg)
            server.quit()
            print('Correo enviado exitosamente')
            return True
        except Exception as e:
            print('Error al enviar el correo:', str(e))
            return False

    def send_template_email(self, recipient:str, subject:str, template:str, context:dict[str, str]=None)->bool:
        '''Enviar un correo electrónico con un template HTML.
        - recipient: str, dirección de correo del destinatario.
        - subject: str, asunto del correo.
        - template: str, nombre del archivo de template.
        - context: dict, contexto para el template. Ejemplo:
            - "name": str, nombre del destinatario (opcional).
            - "message": str, cuerpo del correo (opcional).
            - "link": str, enlace para el botón del correo (opcional).
            - "code": str, código de verificación (opcional).'''
        with open(f"{self.templates_path}/{template}", mode="r", encoding='utf-8') as file:
            template_str = file.read()
 
        jinja_template = jinja2.Template(template_str)
        if context is not None:
            template_str = jinja_template.render(context)
        else:
            template_str = jinja_template.render()
        return self.send_email(recipient, subject, template_str, 'html')


