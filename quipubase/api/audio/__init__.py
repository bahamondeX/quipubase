from fastapi import APIRouter
from .speech import route as speech_route
from .transcriptions import route as transcriptions_route

def route():
	api = APIRouter(tags=["audio"])
	api.include_router(speech_route())
	api.include_router(transcriptions_route())
	return api
	
