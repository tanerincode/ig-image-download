from fastapi import FastAPI
from dto.Model import IgRecord
from services.post_service import PostService
from services.image_service import ImageService
from typing import List
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")


@app.get("/")
async def root():
    return {"message": "this is the root of the API"}


@app.post("/bulk/post")
async def bulk_post(items: List[IgRecord]):
    post_service = PostService(items)
    try:
        data = post_service.process()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    return {"data": data}


@app.post("/bulk/image")
async def bulk_image(items: List[IgRecord]):
    image_service = ImageService(items)
    try:
        data = image_service.process()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    return {"data": data}
