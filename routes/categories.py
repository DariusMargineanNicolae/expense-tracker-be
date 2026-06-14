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
            categories = dependencies.db_service.get_all_by_record_type(
                "CATEGORY", index_name="recordTypeIndex"
            )
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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str):
    """
    Remove a category from the database by its ID.
    Safety Layer: Raises 400 Bad Request if there is any expense associated with this category.
    Raises 404 if the category does not exist.
    """
    try:
        # 1. Verify if category exists
        record = dependencies.db_service.get_record(category_id)
        if not record or record.get("recordType") != "CATEGORY":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' not found."
            )
            
        # 2. Check for associated expenses (query direct standard filter or get all expenses)
        expenses = dependencies.db_service.get_all_by_record_type(
            "EXPENSE", index_name="recordTypeIndex"
        )
        
        # Look if any expense uses this categoryId
        has_associated_expenses = any(exp.get("categoryId") == category_id for exp in expenses)
        if has_associated_expenses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category '{category_id}' because it has active, associated expenses. Please delete or migrate the expenses first."
            )
            
        # 3. Delete from DDB
        dependencies.db_service.delete_record(category_id)
        
        # 4. Synchronize the local in-memory categories cache
        if dependencies.categories_cache is not None:
            dependencies.categories_cache = [cat for cat in dependencies.categories_cache if cat["id"] != category_id]
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting category from database: {str(e)}"
        )

