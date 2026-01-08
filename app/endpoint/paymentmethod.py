from fastapi import HTTPException, status 
from database import db_models, base_models
 
async def readPaymentMethodById(payment_method_id: int, db):
    try:
        payment_method = db.query(db_models.CompanyPaymentMethod).filter(db_models.CompanyPaymentMethod.id_company_payment_method == payment_method_id).first()
        if payment_method is None:
            return HTTPException(status_code=404, detail="Payment Method not found")
        return payment_method
    except Exception as e:
        return HTTPException(status_code=404, detail="Payment Method not found")
 
async def listPaymentMethod(company_id, db):
    try:
        payment_method = db.query(db_models.CompanyPaymentMethod).filter(db_models.CompanyPaymentMethod.id_company == company_id).all()
        if payment_method is None:
            return HTTPException(status_code=404, detail="Payment Method not found")
        return payment_method
    except Exception as e:
        return HTTPException(status_code=404, detail="Payment Method not found") 
    
async def createPaymentMethod(payment_method, db):     
    try: 
        payment_method_data = payment_method.dict()
        db_payment_method = db_models.CompanyPaymentMethod(**payment_method_data)
        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)
        return db_payment_method, status.HTTP_201_CREATED
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updatePaymentMethod(payment_method_id, payment_method, db):
    try:
        db_payment_method = db.query(db_models.CompanyPaymentMethod).filter(db_models.CompanyPaymentMethod.id_company_payment_method == payment_method_id).first()
        if db_payment_method is None:
            return HTTPException(status_code=404, detail="Payment Method not found")
        
        update_data = payment_method.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment_method, key, value)
        
        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)
        return db_payment_method
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def deletePaymentMethod(payment_method_id, db):
    try:
        db_payment_method = db.query(db_models.CompanyPaymentMethod).filter(db_models.CompanyPaymentMethod.id_company_payment_method == payment_method_id).first()
        if db_payment_method is None:
            return HTTPException(status_code=404, detail="Payment Method not found")
        
        db.delete(db_payment_method)
        db.commit()
        return db_payment_method
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
 
  
