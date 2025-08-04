from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import URL detection system after loading .env
from url_detection import get_environment_info