import os
import requests
import jinja2
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv('MAILGUN_DOMAIN')
template_loader = jinja2.FileSystemLoader("templates")
template_env = jinja2.Environment(loader=template_loader)

def render_template(template, **kwargs):
    return template_env.get_template(template).render(**kwargs)

def send_simple_message(to, subject, body, html):
    domain = os.getenv('MAILGUN_DOMAIN')
    return requests.post(
  		f"https://api.mailgun.net/v3/{domain}/messages",
  		auth=("api", os.getenv('MAILGUN_API_KEY')),
  		data={"from": "Yunfei Duan <postmaster@sandbox2300fb912b5548369c86d173d52974c3.mailgun.org>",
			"to": [to],
  			"subject": subject,
  			"text": body,
            "html": html})

def send_user_registration_email(email, username):
    return send_simple_message(
        to=email,
        subject="Successfully signed up",
        body=f"Hi {username}! You have successfully signed up to our service.",
        html=render_template("email/action.html", username=username)
    )