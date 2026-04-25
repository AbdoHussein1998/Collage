from dotenv import load_dotenv
load_dotenv(".env")
from Api.Routes.Client.basic_client_routes import basic_client_router
from Api.ApiConfiguration.fast_api_config import create_lifespan
from fastapi import FastAPI
import uvicorn




app = FastAPI(lifespan=create_lifespan())
app.include_router(basic_client_router)




if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)






