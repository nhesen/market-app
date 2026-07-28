from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.models.customer import SuggestionStatus

class RegisterIn(BaseModel):
    first_name:str=Field(min_length=2,max_length=80); last_name:str=Field(min_length=2,max_length=80)
    phone:str=Field(min_length=7,max_length=30); email:EmailStr; password:str=Field(min_length=8,max_length=72); password_confirmation:str
    organisation_id:str; privacy_accepted:bool
    @model_validator(mode="after")
    def valid(self):
        if self.password!=self.password_confirmation: raise ValueError("Passwords do not match")
        if not self.privacy_accepted: raise ValueError("Privacy acceptance is required")
        return self

class ProfileUpdate(BaseModel):
    full_name:str=Field(min_length=3,max_length=160); phone:str|None=Field(default=None,max_length=30); language:str=Field(pattern="^(az|en)$")
    profile_image_url:str|None=Field(default=None,max_length=255)
    preferred_branch_id:str|None=None

class PreferencesUpdate(BaseModel):
    news:bool=True; discounts:bool=True; report_status:bool=True; suggestion_status:bool=True; expiring_points:bool=True; branch_updates:bool=True

class DeleteRequestIn(BaseModel):
    reason:str|None=Field(default=None,max_length=1000)

class ForgotPasswordIn(BaseModel):
    email:EmailStr

class PreferredBranchIn(BaseModel):
    branch_id:str

class SuggestionCreate(BaseModel):
    branch_id:str|None=None; category:str=Field(min_length=2,max_length=80); title:str=Field(min_length=4,max_length=180); description:str=Field(min_length=10,max_length=3000); anonymous:bool=False

class SuggestionUpdate(BaseModel):
    status:SuggestionStatus; admin_note:str=Field(min_length=2,max_length=2000)

class SuggestionOut(BaseModel):
    id:str; tracking_number:str; branch_id:str|None; category:str; title:str; description:str; anonymous:bool; status:SuggestionStatus; admin_note:str|None; created_at:datetime; updated_at:datetime
