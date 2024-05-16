from typing import List
from fastapi import Depends, APIRouter, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.models import Report, ReportImage  # Import the ReportImage model
from app.database import get_db
from pydantic import BaseModel
import os

router = APIRouter()


class GetReportImage(BaseModel):
    img_name: str
    img_file: str

class CreateReportImageRequest(BaseModel):
    img_name: str
    img_file: str
    
class UpdateReportImageRequest(BaseModel):
    id: int
    img_img: str
    img_file: str


@router.post("/")
async def create_report_image(image: CreateReportImageRequest, db: Session = Depends(get_db)):
    existing_image = db.query(ReportImage).filter(ReportImage.img_name == image.img_name).first()
    
    if existing_image is None:
        new_image = ReportImage(**image.dict())
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
    else:
        existing_image.img_name = image.img_name
        existing_image.img_file = image.img_file
        db.commit()
        db.refresh(existing_image)
    
    return {"data": existing_image}



@router.get("/{image_name}")
async def get_images_by_search(image_name: str, db: Session = Depends(get_db)):
    images = db.query(ReportImage).filter(ReportImage.img_name.like(f"%{image_name}%")).all()
    return {"data": images}


@router.delete("/{image_id}")
async def delete_report_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(ReportImage).filter(ReportImage.id == image_id).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Report Image not found")

    db.delete(image)
    db.commit()
    return {"message": "Report Image deleted"}
