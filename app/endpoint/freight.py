from fastapi import HTTPException, status 
from database import db_models, base_models
 
 
async def createFreight(freight, db):     
    try: 
        freight_data = freight.dict()
        db_freight = db_models.CompanyFreight(**freight_data)
        db.add(db_freight)
        db.commit()
        db.refresh(db_freight)
        return db_freight, status.HTTP_201_CREATED
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
 
async def readFreight(freight_id, db):
    try:
        freight = db.query(db_models.CompanyFreight).filter(db_models.CompanyFreight.id_company_freight == freight_id).first()
        if freight is None:
            return HTTPException(status_code=404, detail="Freight not found")
        return freight
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR

async def updateFreight(freight_id, freight, db):
    try:
        db_freight = db.query(db_models.CompanyFreight).filter(db_models.CompanyFreight.id_company_freight == freight_id).first()
        if db_freight is None:
            return HTTPException(status_code=404, detail="Freight not found")
        
        update_data = freight.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_freight, key, value)
        
        db.add(db_freight)
        db.commit()
        db.refresh(db_freight)
        return db_freight
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def deleteFreight(freight_id, db):
    try:
        db_freight = db.query(db_models.CompanyFreight).filter(db_models.CompanyFreight.id_company_freight == freight_id).first()
        if db_freight is None:
            return HTTPException(status_code=404, detail="Freight not found")
        
        db.delete(db_freight)
        db.commit()
        return db_freight
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
 
async def listFreight(company_id, db):
    try:
        freight = db.query(db_models.CompanyFreight).filter(db_models.CompanyFreight.id_company == company_id).all()
        
        if freight is None:
            return HTTPException(status_code=404, detail="Freight not found")
        
        return freight
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
  