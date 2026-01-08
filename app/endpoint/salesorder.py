from fastapi import HTTPException, status 
from database import db_models, base_models
from datetime import datetime
  
async def createSalesorder(salesorder, db, current_user):
    """Create a new sales order with company and user info from current user."""
    try:
        user_role = current_user.get("role", "")
        user_id = current_user.get("id_user")
        user_company_id = current_user.get("company_id")
        
        # Only admin and user roles can create sales orders
        if user_role not in ["admin", "user", "superadmin"]:
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to create sales orders"
            )
        
        salesorderdata = salesorder.model_dump()
        
        # Convert date strings if needed
        data_lancamento = salesorderdata.get("data_lancamento")
        if isinstance(data_lancamento, str) and data_lancamento:
            data_lancamento = datetime.strptime(data_lancamento, "%Y-%m-%d").date()
        else:
            data_lancamento = datetime.now().date()
            
        data_entrega = salesorderdata.get("data_entrega")
        if isinstance(data_entrega, str) and data_entrega:
            data_entrega = datetime.strptime(data_entrega, "%Y-%m-%d").date()
        
        # Map Pydantic fields to SQLAlchemy model columns (matching actual DB column names)
        db_data = {
            "Redespacho": salesorderdata.get("redespacho", 0),
            "DataLancamento": data_lancamento,
            "DataEntrega": data_entrega,
            "Discount": salesorderdata.get("discount", 0),
            "Observation": salesorderdata.get("observation", ""),
            "CompanyId": user_company_id if user_company_id else None,
            "BusinessPartnerId": salesorderdata.get("id_business_partner"),
            "PaymentMethodId": salesorderdata.get("id_company_payment_method"),
            "PaymentTermId": salesorderdata.get("id_company_payment_term"),
            "UtilizationId": salesorderdata.get("id_company_utilization"),
            "BranchId": salesorderdata.get("id_company_branch"),
            "FreightId": salesorderdata.get("id_company_freight"),
            "CreatedByUserId": user_id,
        }
        
        db_salesorder = db_models.SalesOrder(**db_data) 
        db.add(db_salesorder)
        db.commit()
        db.refresh(db_salesorder)
        
        return {
            "status": "success",
            "message": "Sales order created successfully",
            "id_sales_order": db_salesorder.IdSalesOrder
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )

async def listSalesOrders(db, current_user, filters):
    """List sales orders filtered by user's company and optional filters."""
    try:
        user_role = current_user.get("role", "")
        user_company_id = current_user.get("company_id")
        
        # Start building the query
        query = db.query(db_models.SalesOrder)
        
        # Filter by company (except for superadmin who can see all)
        if user_role != "superadmin" and user_company_id:
            query = query.filter(db_models.SalesOrder.CompanyId == user_company_id)
        
        # Apply optional filters
        if filters.start_date:
            start = datetime.strptime(filters.start_date, "%Y-%m-%d").date()
            query = query.filter(db_models.SalesOrder.DataLancamento >= start)
        
        if filters.end_date:
            end = datetime.strptime(filters.end_date, "%Y-%m-%d").date()
            query = query.filter(db_models.SalesOrder.DataLancamento <= end)
        
        if filters.created_by:
            query = query.filter(db_models.SalesOrder.CreatedByUserId == filters.created_by)
        
        if filters.business_partner_id:
            query = query.filter(db_models.SalesOrder.BusinessPartnerId == filters.business_partner_id)
        
        # Order by most recent first
        query = query.order_by(db_models.SalesOrder.IdSalesOrder.desc())
        
        orders = query.all()
        
        # Transform to response format
        result = []
        for order in orders:
            result.append({
                "id_sales_order": order.IdSalesOrder,
                "redespacho": order.Redespacho,
                "data_lancamento": str(order.DataLancamento) if order.DataLancamento else None,
                "data_entrega": str(order.DataEntrega) if order.DataEntrega else None,
                "discount": order.Discount,
                "observation": order.Observation,
                "id_company": order.CompanyId,
                "id_business_partner": order.BusinessPartnerId,
                "id_company_branch": order.BranchId,
                "id_company_payment_method": order.PaymentMethodId,
                "id_company_payment_term": order.PaymentTermId,
                "id_company_freight": order.FreightId,
                "id_company_utilization": order.UtilizationId,
                "created_by_user_id": order.CreatedByUserId,
                "created_at": str(order.CreatedAt) if order.CreatedAt else None,
                # TODO: Add related names when joins are implemented
                "business_partner_name": None,
                "branch_name": None,
                "payment_method_name": None,
                "payment_term_name": None,
                "freight_name": None,
                "utilization_name": None,
                "created_by_username": None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
       
async def readSalesorder(salesorder_id, db, current_user):
    """Read a single sales order by ID."""
    user_role = current_user.get("role", "")
    user_company_id = current_user.get("company_id")
    
    salesorder = db.query(db_models.SalesOrder).filter(
        db_models.SalesOrder.IdSalesOrder == salesorder_id
    ).first()
    
    if salesorder is None:
        raise HTTPException(status_code=404, detail="SalesOrder not found")
    
    # Check if user has permission (same company or superadmin)
    if user_role != "superadmin" and salesorder.CompanyId != user_company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id_sales_order": salesorder.IdSalesOrder,
        "redespacho": salesorder.Redespacho,
        "data_lancamento": str(salesorder.DataLancamento) if salesorder.DataLancamento else None,
        "data_entrega": str(salesorder.DataEntrega) if salesorder.DataEntrega else None,
        "discount": salesorder.Discount,
        "observation": salesorder.Observation,
        "id_company": salesorder.CompanyId,
        "id_business_partner": salesorder.BusinessPartnerId,
        "id_company_branch": salesorder.BranchId,
        "created_by_user_id": salesorder.CreatedByUserId
    }


async def updateSalesorder(salesorder_id, salesorder_data, db, current_user):
    """Update an existing sales order."""
    try:
        user_role = current_user.get("role", "")
        user_id = current_user.get("id_user")
        user_company_id = current_user.get("company_id")
        
        # Find the existing sales order
        existing_order = db.query(db_models.SalesOrder).filter(
            db_models.SalesOrder.IdSalesOrder == salesorder_id
        ).first()
        
        if not existing_order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        
        # Check if user has permission (same company or superadmin)
        if user_role != "superadmin" and existing_order.CompanyId != user_company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Only admin and user roles can update sales orders
        if user_role not in ["admin", "user", "superadmin"]:
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to update sales orders"
            )
        
        update_data = salesorder_data.model_dump(exclude_unset=True)
        
        # Convert date strings if needed (skip empty strings)
        if "data_lancamento" in update_data:
            if isinstance(update_data["data_lancamento"], str) and update_data["data_lancamento"]:
                update_data["data_lancamento"] = datetime.strptime(
                    update_data["data_lancamento"], "%Y-%m-%d"
                ).date()
            elif not update_data["data_lancamento"]:
                del update_data["data_lancamento"]  # Remove empty value
                
        if "data_entrega" in update_data:
            if isinstance(update_data["data_entrega"], str) and update_data["data_entrega"]:
                update_data["data_entrega"] = datetime.strptime(
                    update_data["data_entrega"], "%Y-%m-%d"
                ).date()
            elif not update_data["data_entrega"]:
                del update_data["data_entrega"]  # Remove empty value
        
        # Map fields to database column names
        field_mapping = {
            "redespacho": "Redespacho",
            "data_lancamento": "DataLancamento",
            "data_entrega": "DataEntrega",
            "discount": "Discount",
            "observation": "Observation",
            "id_business_partner": "BusinessPartnerId",
            "id_company_branch": "BranchId",
            "id_company_payment_method": "PaymentMethodId",
            "id_company_payment_term": "PaymentTermId",
            "id_company_freight": "FreightId",
            "id_company_utilization": "UtilizationId"
        }
        
        # Update only the provided fields
        for key, value in update_data.items():
            if key in field_mapping:
                setattr(existing_order, field_mapping[key], value)
        
        # Set the user who updated the order (if you have this field)
        # existing_order.UpdatedByUserId = user_id
        # existing_order.UpdatedAt = datetime.now()
        
        db.commit()
        db.refresh(existing_order)
        
        return {
            "status": "success",
            "message": "Sales order updated successfully",
            "id_sales_order": existing_order.IdSalesOrder
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
 