from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from Dependencies.welcome_dependcy import get_welcome_service,WelcomeService



basic_client_router=APIRouter(prefix="/client",tags=["Client"],)
@basic_client_router.get("/welcome")
async def welcome(service: WelcomeService = Depends(get_welcome_service)):
    message = await service.welcome()
    return {"message": message}









