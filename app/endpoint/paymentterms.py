from fastapi import HTTPException, status 
from database import db_models, base_models
 
async def readPaymentTermById(payment_term_id: int, db):
    try:
        payment_term = db.query(db_models.CompanyPaymentTerm).filter(db_models.CompanyPaymentTerm.id_company_payment_term == payment_term_id).first()
        if payment_term is None:
            return HTTPException(status_code=404, detail="Payment Term not found")
        return payment_term
    except Exception as e:
        return HTTPException(status_code=404, detail="Payment Term not found")
    
async def listPaymentTerm(company_id, db):
    try:
        payment_term = db.query(db_models.CompanyPaymentTerm).filter(db_models.CompanyPaymentTerm.id_company == company_id).all()
        if payment_term is None:
            return HTTPException(status_code=404, detail="Payment Term not found")
        return payment_term
    except Exception as e:
        return HTTPException(status_code=404, detail="Payment Term not found")
    
async def createPaymentTerm(payment_term, db):     
    try: 
        payment_term_data = payment_term.dict()
        db_payment_term = db_models.CompanyPaymentTerm(**payment_term_data)
        db.add(db_payment_term)
        db.commit()
        db.refresh(db_payment_term)
        return db_payment_term, status.HTTP_201_CREATED
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updatePaymentTerm(payment_term_id, payment_term, db):
    try:
        db_payment_term = db.query(db_models.CompanyPaymentTerm).filter(db_models.CompanyPaymentTerm.id_company_payment_term == payment_term_id).first()
        if db_payment_term is None:
            return HTTPException(status_code=404, detail="Payment Term not found")
        
        update_data = payment_term.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment_term, key, value)
        
        db.add(db_payment_term)
        db.commit()
        db.refresh(db_payment_term)
        return db_payment_term
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
         
async def deletePaymentTerm(payment_term_id, db):
    try:
        db_payment_term = db.query(db_models.CompanyPaymentTerm).filter(db_models.CompanyPaymentTerm.id_company_payment_term == payment_term_id).first()
        if db_payment_term is None:
            return HTTPException(status_code=404, detail="Payment Term not found")
        
        db.delete(db_payment_term)
        db.commit()
        return db_payment_term
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
 
 
 
 
# async def readCompanyPaymentTermById(company_payment_term_id: int, db):
#     return db.query(db_models.Company_PaymentTerm).filter(db_models.Company_PaymentTerm.id_company_payment_term == company_payment_term_id).first()

# async def readCompanyPaymentTermAll(db):
#     return db.query(db_models.Company_PaymentTerm).all()

# async def readCompanyPaymentTermByName(company_payment_term_name: str, db):
#     return db.query(db_models.Company_PaymentTerm).filter(db_models.Company_PaymentTerm.name == company_payment_term_name).first() 
