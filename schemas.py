import time
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: str = Field(..., description="GUID identifier of the category")
    name: str = Field(..., description="Name of the category")
    recordType: str = Field("CATEGORY", description="Type of record, must be CATEGORY")


class CategoryCreate(BaseModel):
    name: str = Field(..., description="Name of the category", min_length=1)


class ExpenseResponse(BaseModel):
    id: str = Field(..., description="GUID identifier of the expense")
    name: str = Field(..., description="Name of the expense")
    recordType: str = Field("EXPENSE", description="Type of record, must be EXPENSE")
    categoryId: str = Field(..., description="Identifier of the category")
    createdAt: str = Field(..., description="ISO 8601 UTC timestamp string when the record was created")
    createdAtEpoch: int = Field(..., description="UNIX Epoch time in seconds when the record was created")


class ExpenseCreate(BaseModel):
    name: str = Field(..., description="Name of the expense", min_length=1)
    categoryId: str = Field(..., description="Identifier of the category")
