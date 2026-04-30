from fastapi import APIRouter, Depends, UploadFile, File, Request,status
from fastapi.responses import JSONResponse

basic_client_router=APIRouter(prefix="/client",tags=["Client"],)







from Dependencies.welcome_dependency import get_welcome_service, WelcomeService
@basic_client_router.get("/welcome")
async def welcome(service: WelcomeService = Depends(get_welcome_service)):
    message = await service.welcome()
    return {"message": message}



from Dependencies.arabic_pdf_processing_dependency import get_arabic_pdf_service
from Services.Exceptions.arabic_pdf_processing_excp import ArabicPdfProcessingError
@basic_client_router.post("/read_arabic_and_chunk_pdf")
async def read_and_process(
    request: Request,
    service=Depends(get_arabic_pdf_service),
    file: UploadFile = File(...)
):
    try:
        results = await service.process(
            file=file
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "PDF processed successfully",
                "data": results
            },
            status_code=status.HTTP_200_OK
        )

    except ArabicPdfProcessingError as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": e.message
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": "Internal server error"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



