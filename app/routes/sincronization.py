from fastapi import APIRouter 

# from endpoint.sincronization import  

router = APIRouter(
    # prefix="/address",
    tags=["sincronization"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}}
)