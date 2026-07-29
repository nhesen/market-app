from fastapi import HTTPException
from app.models.domain import Role, User

def market_id(user:User)->str:
    value=user.selected_organisation_id if user.role==Role.CUSTOMER else user.organisation_id
    if not value:raise HTTPException(422,"Market context is not selected")
    return value
