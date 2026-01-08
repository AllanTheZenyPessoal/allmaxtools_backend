from fastapi import HTTPException, status 
from database import db_models, base_models
from endpoint.address import createAddress 

async def attachUserToCompany( user_to_company, db ): 
    try: 
        user_to_company_data = user_to_company.model_dump()  
        db_user_to_company = db_models.CompanyHasUser(**user_to_company_data) 
        db.add(db_user_to_company)
        db.commit()   
        db.refresh(db_user_to_company) 
        return db_user_to_company, status.HTTP_201_CREATED
    
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of exception
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR

async def createCompany(request, db):     
    try: 
        # Extract AddressBase and CompanyBase from request
        company_data = request.CompanyBase.dict()
       
        db_address = await createAddress(request.AddressBase, db)  # Create Address object
        
        if db_address is None:
            return {"error": "An error occurred while creating the address"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            # Update company_data with the new Address ID
            company_data["id_address"] = db_address.id_address
            company_data["active"] = 1  # Set company as active by default 
        
            # Create and save Company object
            db_company = db_models.Company(**company_data)
            db.add(db_company)
            db.commit()
            db.refresh(db_company)  # Refresh to get the ID

            return db_company, status.HTTP_201_CREATED  # Return the new Company object
    
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of exception
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
      
async def readCompany(company_id, db):
    company = db.query(db_models.Company).filter(db_models.Company.id_company == company_id).first()
    if company is None:
        return HTTPException(status_code=404, detail="Company not found")
    return company

async def readCompanies(db):
    """List all companies (for SuperAdmin use)"""
    try:
        companies = db.query(db_models.Company).filter(db_models.Company.active == True).all()
        return companies
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR

async def updateCompany(company_id, company, db):
    try:
        db_company = db.query(db_models.Company).filter(db_models.Company.id_company == company_id).first()
        if db_company is None:
            return HTTPException(status_code=404, detail="Company not found")
        
        update_data = company.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_company, key, value)
        
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def deleteCompany(company_id, db):
    try:
        db_company = db.query(db_models.Company).filter(db_models.Company.id_company == company_id).first()
        if db_company is None:
            return HTTPException(status_code=404, detail="Company not found")
        
        db.delete(db_company)
        db.commit()
        return db_company
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
