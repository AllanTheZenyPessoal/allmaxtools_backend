from fastapi import HTTPException, status 
from database import db_models, base_models

async def readSincronization(sincronization_id: int, db):
    try:
        sincronization = db.query(db_models.Sincronization).filter(db_models.Sincronization.id_sincronization == sincronization_id).first() 
        if sincronization is None:
            return HTTPException(status_code=404, detail="Sincronization not found")
        return sincronization
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def createSincronization(db):
    try:
        db_sincronization = db_models.SincronizationStatus() 
        db_sincronization.status = "pending" 
        db.add(db_sincronization)
        db.commit()
        db.refresh(db_sincronization) 
        return db_sincronization
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR