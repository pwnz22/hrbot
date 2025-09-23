from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import get_db, engine
from shared.models.vacancy import Vacancy, Base
from api.schemas import VacancyResponse, VacancyCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR Bot API", description="API для получения данных о вакансиях", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "HR Bot API"}

@app.get("/vacancies", response_model=List[VacancyResponse])
async def get_vacancies(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    processed: Optional[bool] = Query(None, description="Фильтр по статусу обработки"),
    db: Session = Depends(get_db)
):
    query = db.query(Vacancy)

    if processed is not None:
        query = query.filter(Vacancy.is_processed == processed)

    vacancies = query.order_by(desc(Vacancy.created_at)).offset(skip).limit(limit).all()
    return vacancies

@app.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return vacancy

@app.put("/vacancies/{vacancy_id}/processed")
async def mark_vacancy_processed(vacancy_id: int, db: Session = Depends(get_db)):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    vacancy.is_processed = True
    db.commit()
    return {"message": "Vacancy marked as processed"}

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total = db.query(Vacancy).count()
    processed = db.query(Vacancy).filter(Vacancy.is_processed == True).count()
    unprocessed = total - processed

    return {
        "total": total,
        "processed": processed,
        "unprocessed": unprocessed
    }