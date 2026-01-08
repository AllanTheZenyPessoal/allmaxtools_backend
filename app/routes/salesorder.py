from fastapi import APIRouter, Depends, status, HTTPException, Query
from dependencies import db_dependency
from token_utils.apikey_generator import verify_token
from typing import Annotated, Optional
from database import base_models, db_models

from endpoint.salesorder import createSalesorder, readSalesorder, listSalesOrders, updateSalesorder

router = APIRouter(
    tags=["salesorder"],
    responses={404: {"description": "Not found"}}
)


# ----------------------------------------------------------------------------------------------------------
# SALES ORDER TABLE ENDPOINTS

@router.post("/salesorder/save/", status_code=status.HTTP_201_CREATED)
async def create_salesorder(
    salesorder: base_models.SalesOrderCreateRequest, 
    db: db_dependency, 
    current_user: Annotated[dict, Depends(verify_token)]
):   
    """Create a new sales order. Company and user ID are set automatically."""
    return await createSalesorder(salesorder, db, current_user)

@router.put("/salesorder/update/{salesorder_id}", status_code=status.HTTP_200_OK)
async def update_salesorder(
    salesorder_id: int,
    salesorder: base_models.SalesOrderUpdateRequest, 
    db: db_dependency, 
    current_user: Annotated[dict, Depends(verify_token)]
):   
    """Update an existing sales order."""
    return await updateSalesorder(salesorder_id, salesorder, db, current_user)

@router.get("/salesorder/list/", status_code=status.HTTP_200_OK)
async def list_salesorders(
    db: db_dependency, 
    current_user: Annotated[dict, Depends(verify_token)],
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    business_partner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """List sales orders with optional filters."""
    filters = base_models.SalesOrderFilter(
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
        business_partner_id=business_partner_id,
        status=status
    )
    return await listSalesOrders(db, current_user, filters)
      
@router.get("/salesorder/{salesorder_id}", status_code=status.HTTP_200_OK)
async def read_salesorder(
    salesorder_id: int, 
    db: db_dependency, 
    current_user: Annotated[dict, Depends(verify_token)]
):
    return await readSalesorder(salesorder_id, db, current_user)

@router.delete("/salesorder/delete/{salesorder_id}", status_code=status.HTTP_200_OK)
async def delete_salesorder(
    salesorder_id: int, 
    db: db_dependency, 
    current_user: Annotated[dict, Depends(verify_token)]
):
    """Delete a sales order."""
    # Find the sales order
    order = db.query(db_models.SalesOrder).filter(
        db_models.SalesOrder.IdSalesOrder == salesorder_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Check if user has permission (same company or superadmin)
    user_role = current_user.get("role", "")
    user_company_id = current_user.get("company_id")
    
    if user_role != "superadmin" and order.CompanyId != user_company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(order)
    db.commit()
    
    return {"message": "Sales order deleted successfully"}
# ----------------------------------------------------------------------------------------------------------