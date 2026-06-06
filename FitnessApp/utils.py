from django.core.mail import EmailMessage
from Fitness_club.settings import EMAIL_HOST_USER

def send_email(subject, recipient_email, text):
    html_content1 = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>Email Template</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: #f4f4f4;
                            margin: 0;
                            padding: 20px;
                        }}
                        .email-container {{
                            max-width: 600px;
                            margin: 0 auto;
                            background-color: #ffffff;
                            border-radius: 20px;
                            overflow: hidden;
                            box-shadow: 0 2px 10px black;
                        }}
                        .header {{
                            background-color: #007bff;
                            color: white;
                            padding: 20px;
                            text-align: center;
                        }}
                        .content {{
                            padding: 20px;
                            color: #333333;
                        }}
                        .footer {{
                            background-color: #eeeeee;
                            padding: 10px;
                            text-align: center;
                            font-size: 12px;
                            color: #777777;
                        }}
                        a {{
                            color: #4CAF50;
                            text-decoration: none;
                        }}
                    </style>
                    </head>
                    <body>
                    <div class="email-container">
                        <div class="header">
                            <h1>GYM Center</h1>
                        </div>
                        <div class="content">
                            <h2>Здравствуйте!</h2>
                            <p>{text}</p>

                            <p>С уважением, <br/>Наша команда</p>
                        </div>
                        <div class="footer">
                            &copy; 2026 GYM Center. Все права защищены.
                            <br/>
                        </div>
                    </div>
                    </body>
                    </html>
                    """

    email = EmailMessage(
        subject,                # Email subject
        '',
        EMAIL_HOST_USER,        # From email (your email)
        [recipient_email],      # Recipient list
    )
    email.body = html_content1
    email.content_subtype = 'html'  # очень важно!
    email.send()


