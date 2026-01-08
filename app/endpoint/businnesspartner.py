from fastapi import HTTPException, status 
from database import db_models, base_models

async def readBusinnespartner( businnespartner_id, db ):
    try:
        businnespartner = db.query(db_models.BusinessPartner).filter(db_models.BusinessPartner.id_business_partner == businnespartner_id).first() 
        if businnespartner is None:
            return HTTPException(status_code=404, detail="Businnes Partner not found")
        return businnespartner
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR

async def createBusinnespartner( businnespartner, db ):   
    try:        
        adress: base_models.AddressBase = businnespartner.id_address.dict()
        db_address = db_models.Address(**adress)
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        
        if db_address.id_address != None:
            businnespartner_data = businnespartner.model_dump();
            businnespartner_data["id_address"] = db_address.id_address;  #Por padrao ativa o usuario logo no cadastro  
            db_businnespartner = db_models.BusinessPartner(**businnespartner_data) 
            db.add(db_businnespartner)
            db.commit()   
            db.refresh(db_businnespartner)
            return db_businnespartner
        else:
            return {"error": f"An error occurred: Address not created"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of exception
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        
async def listBusinnespartners( db ):
    try:
        businnespartners = db.query(db_models.BusinessPartner).all() 
        return businnespartners
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updateBusinnespartner( businnespartner_id, businnespartner, db ):
    try:
        db_businnespartner = db.query(db_models.BusinessPartner).filter(db_models.BusinessPartner.id_business_partner == businnespartner_id).first()
        if db_businnespartner is None:
            return HTTPException(status_code=404, detail="Businnes Partner not found")
        
        update_data = businnespartner.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_businnespartner, key, value)
        
        db.add(db_businnespartner)
        db.commit()
        db.refresh(db_businnespartner)
        return db_businnespartner
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def deleteBusinnespartner( businnespartner_id, db ):
    try:
        db_businnespartner = db.query(db_models.BusinessPartner).filter(db_models.BusinessPartner.id_business_partner == businnespartner_id).first()
        if db_businnespartner is None:
            return HTTPException(status_code=404, detail="Businnes Partner not found")
        
        db.delete(db_businnespartner)
        db.commit() 
        return db_businnespartner
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
  
       

   
 