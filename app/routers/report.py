from typing import List, Optional
from fastapi import Depends, APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import Category, Report, ReportImage, Price
from app.database import get_db
from sqlalchemy import DateTime, desc, func, or_
import os
import io
from datetime import datetime
from PIL import Image
import pandas as pd
import json

from app.routers.report_image import CreateReportImageRequest, UpdateReportImageRequest

router = APIRouter()


class CreateReport(BaseModel):
    title: str
    url: str
    category_id: int
    summary: str
    description: str
    toc: str
    highlights: str
    faqs: str
    meta_title: str
    meta_desc: str
    meta_keyword: str
    pages: str
    cover_img: str
    created_date: str


class CreateReportWithImages(BaseModel):
    report: CreateReport
    images: List[CreateReportImageRequest]


class UpdateReport(BaseModel):
    id: int
    title: str
    url: str
    category_id: int
    summary: str
    description: str
    toc: str
    highlights: str
    faqs: str
    meta_title: str
    meta_desc: str
    meta_keyword: str
    pages: str
    cover_img: str
    created_date: str


class GetReport(BaseModel):
    id: int
    url: str
    category_id: int
    category_name: str
    category_url: str
    title: str
    summary: str
    pages: str
    cover_img: str
    created_date: str


class GetLatestReport(BaseModel):
    title: str
    url: str
    summary: str
    cover_img: str


class GetReportByUrl(BaseModel):
    id: int
    title: str
    url: str
    category_id: int
    category_name: str
    category_url: str
    category_abr: str
    summary: str
    description: str
    toc: str
    highlights: str
    faqs: str
    meta_title: str
    meta_desc: str
    meta_keyword: str
    pages: str
    cover_img: str
    created_date: str
    
class GetReportMetaData(BaseModel):
    url: str
    meta_title: str
    meta_desc: str
    meta_keyword: str
    summary: str


@router.get("/")
async def get_reports(db: Session = Depends(get_db)):
    reports = (
        db.query(Report)
        .join(Category, Report.category_id == Category.id)
        .with_entities(
            Report.id,
            Report.url,
            Report.category_id,
            Category.name.label("category_name"),
            Category.url.label("category_url"),
            Report.title,
            Report.summary,
            Report.pages,
            Report.cover_img,
            Report.created_date,
        )
        .order_by(Report.id.desc())
        .all()
    )
    report_list = [
        GetReport(
            id=report.id,
            url=report.url,
            category_id=report.category_id,
            category_url=report.category_url,
            category_name=report.category_name,
            summary=report.summary,
            title=report.title,
            cover_img=report.cover_img,
            pages=report.pages,
            created_date=report.created_date,
        )
        for report in reports
    ]
    return {"data": report_list}


@router.get("/category/category_count")
async def get_category_count(db: Session = Depends(get_db)):
    query = (
        db.query(
            Category.id.label("category_id"),
            Category.url.label("category_url"),
            Category.abr.label("category_abr"),
            Category.name.label("category_name"),
            Category.back_cover.label("category_back_cover"),
            Category.icon.label("category_icon"),
            func.count(Report.category_id).label("count"),
        )
        .join(Report, Category.id == Report.category_id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
        .all()
    )
    result = [
        {
            "category_id": category_id,
            "category_url": category_url,
            "category_abr": category_abr,
            "category_name": category_name,
            "category_back_cover": category_back_cover,
            "category_icon": category_icon,
            "count": count,
        }
        for category_id, category_url, category_abr, category_name, category_back_cover, category_icon, count in query
    ]
    return {"data": result}


@router.get("/latest")
async def get_latest_reports(
    page: int,
    per_page: int,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page

    reports = (
        db.query(Report)
        .with_entities(
            Report.title,
            Report.url,
            Report.summary,
            Report.cover_img,
        )
        .order_by(func.cast(Report.created_date, DateTime).desc(), Report.id.asc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    report_list = [
        GetLatestReport(
            title=report.title,
            url=report.url,
            summary=report.summary,
            cover_img=report.cover_img,
        )
        for report in reports
    ]

    return {"data": report_list}


@router.get("/search")
async def get_searched_reports(
    page: int,
    per_page: int,
    keyword: str,
    category_id: Optional[int] = None,  # Make category_id optional
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page

    query = (
        # db.query(Report)
        db.query(Report)
        .join(Category, Category.id == Report.category_id)
        .with_entities(
            Report.id,
            Report.url,
            Report.category_id,
            Category.name.label("category_name"),
            Category.url.label("category_url"),
            Report.summary,
            Report.title,
            Report.pages,
            Report.cover_img,
            Report.created_date,
        )
        .filter(
            # func.to_tsvector("english", Report.title).match(
            #     keyword, postgresql_regconfig="english"
            # )
            or_(
                func.to_tsvector("english", Report.title).match(
                    keyword, postgresql_regconfig="english"
                ),
                Report.title.ilike(f"%{keyword}%"),
            )
        )
        # .order_by(func.cast(Report.created_date, DateTime).desc())
        # .offset(offset)
        # .limit(per_page)
    )
    
     # Apply category filter if category_id is provided
    if category_id is not None:
        query = query.filter(Report.category_id == category_id)


    reports = query.order_by(func.cast(Report.created_date, DateTime).desc()).offset(offset).limit(per_page).all()

    report_list = [
        GetReport(
            id=report.id,
            url=report.url,
            title=report.title,
            category_id=report.category_id,
            category_name=report.category_name,
            category_url=report.category_url,
            summary=report.summary,
            pages=report.pages,
            cover_img=report.cover_img,
            created_date=report.created_date,
        )
        for report in reports
    ]

    return {"data": report_list}


@router.get("/{report_id}")
async def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    return {"data": report}


@router.get("/report_load/{report_id}")
async def get_report_by_report_id(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).join(Category, Category.id == Report.category_id).filter(Report.id == report_id).first()
    category = db.query(Category).filter(Category.id == report.category_id).first()
    priceList = db.query(Price).all()
    images = db.query(ReportImage).filter(ReportImage.img_name.like(f"%RP{report_id}%")).all()
    return {"data":{"report": report, "category":category, "price_list":priceList, "images": images}}


@router.get("/url/{report_url}")
async def get_report_by_url(report_url: str, db: Session = Depends(get_db)):
    report = (
        db.query(Report)
        .join(Category, Category.id == Report.category_id)
        .with_entities(
            Report.id,
            Report.url,
            Report.category_id,
            Category.name.label("category_name"),
            Category.url.label("category_url"),
            Category.abr.label("category_abr"),
            Report.summary,
            Report.title,
            Report.pages,
            Report.cover_img,
            Report.created_date,
            Report.description,
            Report.toc,
            Report.highlights,
            Report.faqs,
            Report.meta_title,
            Report.meta_desc,
            Report.meta_keyword,
        )
        .filter(Report.url == report_url)
        .first()
    )

    get_report_data = GetReportByUrl(
        id=report.id,
        url=report.url,
        title=report.title,
        category_id=report.category_id,
        category_name=report.category_name,
        category_url=report.category_url,
        category_abr=report.category_abr,
        summary=report.summary,
        pages=report.pages,
        cover_img=report.cover_img,
        created_date=report.created_date,
        description=report.description,
        toc=report.toc,
        highlights=report.highlights,
        faqs=report.faqs,
        meta_title=report.meta_title,
        meta_desc=report.meta_desc,
        meta_keyword=report.meta_keyword,
    )

    return {"data": get_report_data}

@router.get("/meta/{report_url}")
async def get_reportmeta_by_url(report_url: str, db: Session = Depends(get_db)):
    report = (
        db.query(Report)
        .with_entities(
            Report.url,
            Report.meta_title,
            Report.meta_desc,
            Report.meta_keyword,
            Report.summary,
        )
        .filter(Report.url == report_url)
        .first()
    )

    get_report_data = GetReportMetaData(
        url=report.url,
        meta_title=report.meta_title,
        meta_desc=report.meta_desc,
        meta_keyword=report.meta_keyword,
        summary=report.summary,
    )

    return {"data": get_report_data}


@router.get("/category/{category_url}")
async def get_reports_by_category(
    category_url: str,
    page: int,
    per_page: int,
    db: Session = Depends(get_db),
):
    if category_url is None:
        raise HTTPException(status_code=404, detail="Category not found")

    offset = (page - 1) * per_page
    
    if(category_url != 'all-industries'):
        reports = (
            # db.query(Report)
            db.query(Report)
            .join(Category, Report.category_id == Category.id)
            .with_entities(
                Report.id,
                Report.url,
                Report.category_id,
                Category.name.label("category_name"),
                Category.url.label("category_url"),
                Report.summary,
                Report.title,
                Report.pages,
                Report.cover_img,
                Report.created_date,
            )
            .filter(Category.url == category_url)
            .order_by(func.cast(Report.created_date, DateTime).desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )
    else:
        reports = (
            # db.query(Report)
            db.query(Report)
            .join(Category, Report.category_id == Category.id)
            .with_entities(
                Report.id,
                Report.url,
                Report.category_id,
                Category.name.label("category_name"),
                Category.url.label("category_url"),
                Report.summary,
                Report.title,
                Report.pages,
                Report.cover_img,
                Report.created_date,
            )
            .order_by(func.cast(Report.created_date, DateTime).desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

    report_list = [
        GetReport(
            id=report.id,
            url=report.url,
            title=report.title,
            category_id=report.category_id,
            category_name=report.category_name,
            category_url=report.category_url,
            summary=report.summary,
            pages=report.pages,
            cover_img=report.cover_img,
            created_date=report.created_date,
        )
        for report in reports
    ]

    return {"data": report_list}


@router.post("/")
async def create_report(report: CreateReportWithImages, db: Session = Depends(get_db)):
    db_report = Report(**report.report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    for image in report.images:
        image.img_name = image.img_name.replace("XXX", str(db_report.id))
        new_image = ReportImage(**image.dict())
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

    return {"data": "Report Added Successfully"}

@router.post("/bulk")
async def bulk_create_report(reports: list[CreateReportWithImages], db: Session = Depends(get_db)):
    for report in reports:
        db_report = Report(**report.report.dict())
        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        for image in report.images:
            image.img_name = image.img_name.replace("XXX", str(db_report.id))
            new_image = ReportImage(**image.dict())
            db.add(new_image)
            db.commit()
            db.refresh(new_image)

    return {"data": "Report Added Successfully"}

@router.put("/{report_id}")
async def update_report(new_report: UpdateReport, db: Session = Depends(get_db)):
    existing_report = db.query(Report).filter(Report.id == new_report.id).first()
    if existing_report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    for attr, value in new_report.dict().items():
        setattr(existing_report, attr, value)

    db.commit()
    db.refresh(existing_report)

    return {"data": existing_report}


@router.delete("/{report_id}")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}

@router.post("/generate-payload-from-excel")
async def convert_excel_to_json(file: UploadFile = File(...)):
    try:
        if not file.content_type.lower() in (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ):
            raise ValueError("Invalid file format. Please upload an Excel file (.xlsx or .xls).")

        data = pd.read_excel(file.file, sheet_name=None) 
        
        category_list = [
            {
            "id": 6,
            "abr": "ADV",
            "url": "advanced-materials",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Advanced Material",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 22,
            "abr": "AGR",
            "url": "agriculture",
            "back_cover": None,
            "meta_desc": None,
            "icon": None,
            "name": "Agriculture",
            "meta_title": None,
            "meta_keyword": None
            },
            {
            "id": 1,
            "abr": "ANA",
            "url": "analytics",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Analytics",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 17,
            "abr": "ARC",
            "url": "architecture",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Architecture",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 21,
            "abr": "AUT",
            "url": "automobile-and-transportation",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Automobile & Transportation",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 19,
            "abr": "BIO",
            "url": "biotechnology",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Biotechnology",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 15,
            "abr": "BLD",
            "url": "building-materials",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Building Materials",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 4,
            "abr": "CHE",
            "url": "chemicals",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Chemicals & Materials",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 10,
            "abr": "COM",
            "url": "commercial-aviation",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Commercial Aviation",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 12,
            "abr": "CGS",
            "url": "consumer-goods",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Consumer Goods",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 18,
            "abr": "CNV",
            "url": "convenience-food",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Convenience Food",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 7,
            "abr": "EAS",
            "url": "electronics-and-semiconductors",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Electronics & Semiconductors",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 14,
            "abr": "EAP",
            "url": "energy-and-power",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Energy & Power",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 13,
            "abr": "FAN",
            "url": "feed-and-animal-nutrition",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Feed and Animal Nutrition",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 23,
            "abr": "FAB",
            "url": "food-and-beverages",
            "back_cover": None,
            "meta_desc": None,
            "icon": None,
            "name": "Food & Beverages",
            "meta_title": None,
            "meta_keyword": None
            },
            {
            "id": 9,
            "abr": "HAP",
            "url": "household-appliances",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Household Appliances",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 20,
            "abr": "IEQ",
            "url": "industrial-equipment",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Industrial Equipment",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 16,
            "abr": "IT",
            "url": "information-technology",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Information Technology",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 2,
            "abr": "MAE",
            "url": "machinery-and-equipment",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Machinery & Equipment",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 11,
            "abr": "MDEV",
            "url": "medical-devices",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Medical Devices",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 24,
            "abr": "PAK",
            "url": "packaging",
            "back_cover": None,
            "meta_desc": None,
            "icon": None,
            "name": "Packaging",
            "meta_title": None,
            "meta_keyword": None
            },
            {
            "id": 3,
            "abr": "PHA",
            "url": "pharmaceuticals",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Pharma & Healthcare",
            "meta_title": "",
            "meta_keyword": ""
            },
            {
            "id": 5,
            "abr": "SER",
            "url": "services",
            "back_cover": "",
            "meta_desc": "",
            "icon": "",
            "name": "Services",
            "meta_title": "",
            "meta_keyword": ""
            }
        ]
        
        # For Multiple Sheets
        # json_data = {}
        # for sheet_name, sheet_data in data.items():
        #     json_data[sheet_name] = json.loads(sheet_data.to_json(orient="records"))
        
        # For Single Sheet
        json_data = {}
        payload:list[CreateReportWithImages] = []
        for sheet_name, sheet_data in data.items():
            json_data = json.loads(sheet_data.to_json(orient="records"))
        for i, jdata in enumerate(json_data):
            report:CreateReportWithImages = {}
            json_data[i]['url'] = (json_data[i]['title'].lower().split('market')[0] + 'market').replace('global ', '').split(' ')
            json_data[i]['url'] = '-'.join(json_data[i]['url'])
            json_data[i]['pages'] = str(json_data[i]['pages'])
            json_data[i]['created_date'] = datetime.fromtimestamp(json_data[i]['created_date'] / 1000.0).strftime("%Y/%m/%d")
            if jdata['description'] is not None:
                json_data[i]['summary'] = jdata['description'].split('\n')[0]
                json_data[i]['meta_desc'] = jdata['description'].split('\n')[0]
            for j, cat in enumerate(category_list):
                if json_data[i]['category_id'] == cat['name']: 
                    json_data[i]['category_id'] = cat['id']
            json_data[i]['faqs'] = ''
            json_data[i]['cover_img'] = ''
            json_data[i]['meta_keyword'] = ''
            report['report'] = json_data[i]
            report['images'] = []
            payload.append(report)
        
        return payload

    except ValueError as e:
        return {"error": str(e)}  # Handle file format errors

    except Exception as e:
        error_dict = {"error": str(e)}
        return json.dumps(error_dict)


@router.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        file_extension = file.filename.split(".")[-1]

        destination_folder = "images"
        os.makedirs(destination_folder, exist_ok=True)

        file_path = os.path.join(destination_folder, f"{timestamp}.{file_extension}")

        contents = file.file.read()

        image = Image.open(io.BytesIO(contents))

        max_width = 800
        image.thumbnail((max_width, max_width))

        image.save(file_path)

    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {
        "message": f"Successfully uploaded and compressed {file.filename} to {file_path}"
    }
