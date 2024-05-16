from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, func


class Report(Base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False, unique=True)
    url = Column(String, nullable=False, unique=True)
    category_id = Column(Integer, nullable=False)
    summary = Column(String)
    description = Column(String)
    toc = Column(String)
    highlights = Column(String)
    faqs = Column(String)
    meta_title = Column(String)
    meta_desc = Column(String)
    meta_keyword = Column(String)
    pages = Column(String)
    cover_img = Column(String)
    created_date = Column(String)
    

class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, nullable=False)
    abr = Column(String)
    name = Column(String)
    url = Column(String, nullable=False, unique=True)
    icon = Column(String)
    back_cover = Column(String)
    meta_title = Column(String)
    meta_desc = Column(String)
    meta_keyword = Column(String)


class ReportImage(Base):
    __tablename__ = "report_image"

    id = Column(Integer, primary_key=True, nullable=False)
    img_name = Column(String, nullable=False)
    img_file = Column(String, nullable=False)

class PressRelease(Base):
    __tablename__ = "press_release"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String)
    url = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)
    description = Column(String)
    report_id = Column(Integer)
    summary = Column(String)
    meta_title = Column(String)
    meta_desc = Column(String)
    meta_keyword = Column(String)
    cover_img = Column(String)
    created_date = Column(String)
    
class Price(Base):
    __tablename__ = "price"

    id = Column(Integer, primary_key=True, nullable=False)
    license = Column(String, nullable=False)
    price = Column(String, nullable=False)