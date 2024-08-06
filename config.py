import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name, default=None):
    return os.getenv(name, default)

BOT_TOKEN = get_env_variable("BOT_TOKEN")
DATA_FOLDER = get_env_variable("DATA_FOLDER")
TYPE = get_env_variable("TYPE")
PROJECT_ID = get_env_variable("PROJECT_ID")
PRIVATE_KEY_ID = get_env_variable("PRIVATE_KEY_ID")
PRIVATE_KEY = get_env_variable("PRIVATE_KEY").replace('\\n', '\n')
CLIENT_EMAIL = get_env_variable("CLIENT_EMAIL")
CLIENT_ID = get_env_variable("CLIENT_ID")
AUTH_URI = get_env_variable("AUTH_URI")
TOKEN_URI = get_env_variable("TOKEN_URI")
AUTH_PROVIDER_X509_CERT_URL = get_env_variable("AUTH_PROVIDER_X509_CERT_URL")
CLIENT_X509_CERT_URL = get_env_variable("CLIENT_X509_CERT_URL")
UNIVERSE_DOMAIN = get_env_variable("UNIVERSE_DOMAIN")

credentials_info = {
  "type": TYPE,
  "project_id": PROJECT_ID,
  "private_key_id": PRIVATE_KEY_ID,
  "private_key": PRIVATE_KEY,
  "client_email": CLIENT_EMAIL,
  "client_id": CLIENT_ID,
  "auth_uri": AUTH_URI,
  "token_uri": TOKEN_URI,
  "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
  "client_x509_cert_url": CLIENT_X509_CERT_URL,
  "universe_domain": UNIVERSE_DOMAIN,
}