from fastapi import HTTPException, status 
from database import db_models, base_models
  
async def readUtilizationById(utilization_id: int, db):
    try:
        utilization = db.query(db_models.CompanyUtilization).filter(db_models.CompanyUtilization.id_company_utilization == utilization_id).first()
        if utilization is None:
            return HTTPException(status_code=404, detail="Utilization not found")
        return utilization
    except Exception as e:
        return HTTPException(status_code=404, detail="Utilization not found")

async def createUtilization(utilization, db):     
    try: 
        utilization_data = utilization.dict()
        db_utilization = db_models.CompanyUtilization(**utilization_data)
        db.add(db_utilization)
        db.commit()
        db.refresh(db_utilization)
        return db_utilization, status.HTTP_201_CREATED
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updateUtilization(utilization_id, utilization, db):
    try:
        db_utilization = db.query(db_models.CompanyUtilization).filter(db_models.CompanyUtilization.id_company_utilization == utilization_id).first()
        if db_utilization is None:
            return HTTPException(status_code=404, detail="Utilization not found")
        
        update_data = utilization.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_utilization, key, value)
        
        db.add(db_utilization)
        db.commit()
        db.refresh(db_utilization)
        return db_utilization
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def deleteUtilization(utilization_id, db):
    try:
        db_utilization = db.query(db_models.CompanyUtilization).filter(db_models.CompanyUtilization.id_company_utilization == utilization_id).first()
        if db_utilization is None:
            return HTTPException(status_code=404, detail="Utilization not found")
        
        db.delete(db_utilization)
        db.commit()
        return db_utilization
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def listUtilization(company_id, db):
    try:
        utilization = db.query(db_models.CompanyUtilization).filter(db_models.CompanyUtilization.id_company == company_id).all()
        if utilization is None:
            return HTTPException(status_code=404, detail="Utilization not found")
        return utilization
    except Exception as e:
        return HTTPException(status_code=404, detail="Utilization not found")
 
  