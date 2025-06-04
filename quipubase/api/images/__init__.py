from fastapi import APIRouter
from .generations.route import app

def route()->APIRouter:
	api = APIRouter(prefix="/images")
	api.include_router(app)
	return api
	
    