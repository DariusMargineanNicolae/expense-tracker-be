import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
import dependencies
from schemas import CategoryCreate, CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("", response_model=List[CategoryResponse])
async def get_categories(refresh: bool = False):
    """
    Get all categories. Uses an in-memory cache to optimize database calls.
    Pass `refresh=true` as a query parameter to force database refetch and update cache.
    """
    if refresh or dependencies.categories_cache is None:
        try:
            # Query DynamoDB Table on the recordType GSI index
            categories = dependencies.db_service.get_all_by_record_type("CATEGORY")
            dependencies.categories_cache = categories
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving categories from database: {str(e)}"
            )
    return dependencies.categories_cache


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_data: CategoryCreate):
    """
    Add a new category with GUID ID, name, and recordType of CATEGORY.
    Updates the categories memory cache upon success.
    """
    category_id = str(uuid.uuid4())
    new_category = {
        "id": category_id,
        "name": category_data.name,
        "recordType": "CATEGORY"
    }
    
    try:
        # Save to DDB
        dependencies.db_service.create_record(new_category)
        
        # Keep cache in sync
        if dependencies.categories_cache is not None:
            dependencies.categories_cache.append(new_category)
        else:
            dependencies.categories_cache = [new_category]
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating category in database: {str(e)}"
        )
        
    return new_category
