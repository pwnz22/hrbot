from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import get_db, engine
from shared.models.vacancy import Vacancy, Application, Base
from api.schemas import VacancyResponse, VacancyCreate, ApplicationResponse, ApplicationCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR Bot API", description="API для управления вакансиями и откликами", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "HR Bot API"}

# Endpoints для вакансий
@app.get("/vacancies", response_model=List[VacancyResponse])
async def get_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    vacancies = db.query(Vacancy).order_by(desc(Vacancy.created_at)).offset(skip).limit(limit).all()
    return vacancies

@app.post("/vacancies", response_model=VacancyResponse)
async def create_vacancy(vacancy: VacancyCreate, db: Session = Depends(get_db)):
    db_vacancy = Vacancy(**vacancy.model_dump())
    db.add(db_vacancy)
    try:
        db.commit()
        db.refresh(db_vacancy)
        return db_vacancy
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="Vacancy with this title already exists")

@app.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return vacancy

# Endpoints для откликов
@app.get("/applications", response_model=List[ApplicationResponse])
async def get_applications(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    processed: Optional[bool] = Query(None, description="Фильтр по статусу обработки"),
    vacancy_id: Optional[int] = Query(None, description="Фильтр по ID вакансии"),
    db: Session = Depends(get_db)
):
    query = db.query(Application)

    if processed is not None:
        query = query.filter(Application.is_processed == processed)

    if vacancy_id is not None:
        query = query.filter(Application.vacancy_id == vacancy_id)

    applications = query.order_by(desc(Application.created_at)).offset(skip).limit(limit).all()
    return applications

@app.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@app.put("/applications/{application_id}/processed")
async def mark_application_processed(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.is_processed = True
    db.commit()
    return {"message": "Application marked as processed"}

@app.put("/applications/{application_id}/vacancy/{vacancy_id}")
async def link_application_to_vacancy(application_id: int, vacancy_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    application.vacancy_id = vacancy_id
    db.commit()
    return {"message": "Application linked to vacancy"}

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_applications = db.query(Application).count()
    processed_applications = db.query(Application).filter(Application.is_processed == True).count()
    unprocessed_applications = total_applications - processed_applications
    total_vacancies = db.query(Vacancy).count()

    return {
        "applications": {
            "total": total_applications,
            "processed": processed_applications,
            "unprocessed": unprocessed_applications
        },
        "vacancies": {
            "total": total_vacancies
        }
    }