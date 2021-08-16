import aiosmtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import templates, settings

async def send_email(
    email: list, subject: str,
    sender: str, html: str,
    files: list = [], **param
) -> None:
    message = MIMEMultipart()

    message['Subject'] = subject
    message['From'] = sender
    message['To'] = ','.join(email)

    template = templates.get_template(html)
    html = template.render(**param)

    message.attach(MIMEText(html,'html'))

    for f in files:
        with open(f, "rb") as fil:
            part = MIMEApplication(fil.read(),Name=basename(f))
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(f))
        message.attach(part)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_server,
            port=settings.smtp_port,
            use_tls=settings.smtp_tls,
            username=settings.smtp_username,
            password=settings.smtp_password
        )
    except aiosmtplib.SMTPException as err:
        raise RuntimeError(err)
