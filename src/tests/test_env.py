import os

import dotenv
from dotenv import load_dotenv

load_dotenv()
print(f"Loaded .env from: {dotenv.find_dotenv()}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')[:4]}...")  # Ofuscar contraseña
print(f"TOKEN: {os.getenv('TOKEN')[:4]}...")  # Ofuscar token