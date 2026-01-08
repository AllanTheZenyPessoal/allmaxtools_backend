from fastapi import HTTPException, status 
from database import db_models
 
async def readAddress(address_id, db):
    address = db.query(db_models.Address).filter(db_models.Address.id_address == address_id).first()
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address
 
async def createAddress(address, db):
    try:  
        db_address = db_models.Address(**address.dict()) 
        db.add(db_address) 
        db.commit()
        db.refresh(db_address)
        return db_address 
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updateAddress(address_id, address, db):
    try:
        db_address = db.query(db_models.Address).filter(db_models.Address.id_address == address_id).first()
        if db_address is None:
            return HTTPException(status_code=404, detail="Address not found")
        
        update_data = address.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_address, key, value)
        
        db.add(db_address)
        db.commit()
        return db_address
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR

async def deleteAddress(address_id, db):
    try:
        db_address = db.query(db_models.Address).filter(db_models.Address.id_address == address_id).first()
        if db_address is None:
            return HTTPException(status_code=404, detail="Address not found")
        
        db.delete(db_address)
        db.commit()
        return db_address
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
