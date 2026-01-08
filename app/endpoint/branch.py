from fastapi import HTTPException, status 
from endpoint.sincronization import createSincronization
from database import db_models


async def readBranch(branch_id: int, db):
    try:
        branch = db.query(db_models.CompanyBranch).filter(db_models.CompanyBranch.id_company_branch == branch_id).first() 
        if branch is None:
            return HTTPException(status_code=404, detail="Branch not found")
        return branch
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def listBranch(compnay_id:int, db):
    try:
        branch = db.query(db_models.CompanyBranch).filter(db_models.CompanyBranch.id_company == compnay_id).all()
        if branch is None:
            return HTTPException(status_code=404, detail="Branch not found")
        return branch
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def createBranch(branch, db):
    try: 
        sincronization = await createSincronization(db) 
        branch.id_sincronization_status = sincronization.id_sincronization_status
        
        branch_data = branch.model_dump()
        db_branch = db_models.CompanyBranch(**branch_data)    
        db.add(db_branch)
        db.commit()
        db.refresh(db_branch)
        return db_branch
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
async def updateBranch(branch_id: int, branch, db):
    try:
        db_branch = db.query(db_models.CompanyBranch).filter(db_models.CompanyBranch.id_company_branch == branch_id).first()
        if db_branch is None:
            return HTTPException(status_code=404, detail="Branch not found")
        
        update_data = branch.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_branch, key, value)
        
        db.add(db_branch)
        db.commit()
        db.refresh(db_branch)
        return db_branch
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        
async def deleteBranch(branch_id: int, db):
    try:
        db_branch = db.query(db_models.CompanyBranch).filter(db_models.CompanyBranch.id_company_branch == branch_id).first()
        if db_branch is None:
            return HTTPException(status_code=404, detail="Branch not found")
        
        db.delete(db_branch)
        db.commit()
        db.refresh(db_branch)
        return db_branch
    except Exception as e:
        db.rollback()
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    

async def readBranchByName(branch_name: str, db):
    try:
        branch = db.query(db_models.CompanyBranch).filter(db_models.CompanyBranch.name == branch_name).first()
        if branch is None:
            return HTTPException(status_code=404, detail="Branch not found")
        return branch
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    
