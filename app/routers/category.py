from typing import List
from fastapi import Depends, APIRouter, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.models import Category
from app.database import get_db
from pydantic import BaseModel
import os

router = APIRouter()

# class CreatePriceRequest(BaseModel):
#     license: str
#     price: str


class CreateCategoryRequest(BaseModel):
    abr: str
    name: str
    url: str
    icon: str
    back_cover: str
    meta_title: str
    meta_desc: str
    meta_keyword: str

@router.post("/")
async def create_category(
    category: CreateCategoryRequest, db: Session = Depends(get_db)
):
    db_category = category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return {"data": db_category}
@router.post("/bulk")
async def create_category_bulk(
    categories: list[CreateCategoryRequest], db: Session = Depends(get_db)
):
    for category in categories:
        db_category = Category(**category.dict())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
    return {"data": db_category}


@router.get("/")
async def get_category(db: Session = Depends(get_db)):
    category_list = db.query(Category).order_by(Category.name.asc()).all()
    return {"data": category_list}

@router.get("/{category_id}")
async def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    categoryData = db.query(Category).filter(Category.id == category_id).first()
    return {"data": categoryData}

@router.get("/url/{category_url}")
async def get_category_by_url(category_url: str, db: Session = Depends(get_db)):
    categoryData = db.query(Category).filter(Category.url == category_url).first()
    return {"data": categoryData}


# @router.put("/{price_id}")
# async def update_price(
#     new_price: UpdatePriceRequest, db: Session = Depends(get_db)
# ):
#     existing_price = (
#         db.query(Price).filter(Price.id == new_price.id).first()
#     )
#     if existing_price is None:
#         raise HTTPException(status_code=404, detail="Price not found")

#     for attr, value in new_price.dict().items():
#         setattr(existing_price, attr, value)

#     db.commit()
#     db.refresh(existing_price)
#     return {"data": existing_price}


# @router.delete("/{price_id}")
# async def delete_price(price_id: int, db: Session = Depends(get_db)):
#     price = (
#         db.query(Price).filter(Price.id == price_id).first()
#     )
#     if price is None:
#         raise HTTPException(status_code=404, detail="Price not found")

#     db.delete(price)
#     db.commit()
#     return {"message": "Price deleted"}

