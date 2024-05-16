from typing import List
from fastapi import Depends, APIRouter, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.models import Report, Price  # Import the Price model
from app.database import get_db
from pydantic import BaseModel
import os

router = APIRouter()


class GetPrice(BaseModel):
    id: int
    license: str
    price: str


class CreatePriceRequest(BaseModel):
    license: str
    price: str


class UpdatePriceRequest(BaseModel):
    id: int
    license: str
    price: str



@router.post("/")
async def create_price(
    price: CreatePriceRequest, db: Session = Depends(get_db)
):
    db_price = Price(**price.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return {"data": db_price}


@router.get("/")
async def get_price(db: Session = Depends(get_db)):
    priceList = db.query(Price).all()
    return {"data": priceList}

@router.get("/{price_id}")
async def get_price_by_id(price_id: int, db: Session = Depends(get_db)):
    priceData = db.query(Price).filter(Price.id == price_id).first()
    return {"data": priceData}


@router.put("/{price_id}")
async def update_price(
    new_price: UpdatePriceRequest, db: Session = Depends(get_db)
):
    existing_price = (
        db.query(Price).filter(Price.id == new_price.id).first()
    )
    if existing_price is None:
        raise HTTPException(status_code=404, detail="Price not found")

    for attr, value in new_price.dict().items():
        setattr(existing_price, attr, value)

    db.commit()
    db.refresh(existing_price)
    return {"data": existing_price}


@router.delete("/{price_id}")
async def delete_price(price_id: int, db: Session = Depends(get_db)):
    price = (
        db.query(Price).filter(Price.id == price_id).first()
    )
    if price is None:
        raise HTTPException(status_code=404, detail="Price not found")

    db.delete(price)
    db.commit()
    return {"message": "Price deleted"}

