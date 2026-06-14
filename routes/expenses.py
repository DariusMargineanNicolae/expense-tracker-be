import uuid
import csv
import io
import time
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
import dependencies
from schemas import ExpenseCreate, ExpenseResponse
from routes.categories import get_categories

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
)


@router.post("/export-csv", status_code=status.HTTP_201_CREATED)
async def export_expenses_to_csv():
    """
    Get all expenses, format them as CSV, and upload to S3.
    CSV filename matches current timestamp in milliseconds (e.g. 1718365200123.csv).
    Returns information about the uploaded file in S3.
    """
    try:
        # 1. Get all expenses
        expenses = await get_expenses()
        
        # 2. Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["id", "name", "recordType", "categoryId", "amount", "createdAt", "createdAtEpoch", "description"])
        
        # Write rows
        for expense in expenses:
            writer.writerow([
                expense.get("id", ""),
                expense.get("name", ""),
                expense.get("recordType", "EXPENSE"),
                expense.get("categoryId", ""),
                str(expense.get("amount", "0")),
                expense.get("createdAt", ""),
                expense.get("createdAtEpoch", ""),
                expense.get("description", "")
            ])
            
        csv_content = output.getvalue().encode("utf-8")
        
        # 3. Generate filename using timestamp in milliseconds
        timestamp_ms = int(time.time() * 1000)
        filename = f"{timestamp_ms}.csv"
        
        # 4. Upload to S3
        dependencies.s3_service.upload_file_content(
            file_content=csv_content,
            destination_key=filename,
            content_type="text/csv"
        )
        
        output.seek(0)
        return {
            "message": "Successfully exported and saved to S3.",
            "bucket": dependencies.s3_service.bucket_name,
            "filename": filename,
            "record_count": len(expenses)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting expenses to S3: {str(e)}"
        )


@router.get("", response_model=List[ExpenseResponse])
async def get_expenses():
    """
    Get all expenses from database.
    Queries DynamoDB on GSI recordType index.
    """
    try:
        expenses = dependencies.db_service.get_all_by_record_type(
            "EXPENSE", index_name="recordTypeIndex"
        )
        return expenses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving expenses from database: {str(e)}"
        )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_data: ExpenseCreate):
    """
    Add a new expense with GUID ID, name, recordType of EXPENSE, categoryId, createdAt and createdAtEpoch.
    Verifies that the provided categoryId exists first.
    """
    # Verify if categoryId exists in DB (utilize cache)
    categories = await get_categories()
    category_ids = {cat["id"] for cat in categories}
    if expense_data.categoryId not in category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provided categoryId '{expense_data.categoryId}' does not exist. Please create category first or use a valid ID."
        )
        
    # Generate timestamp properties on the backend
    created_at = datetime.utcnow().isoformat() + "Z"
    created_at_epoch = int(time.time())
        
    expense_id = str(uuid.uuid4())
    new_expense = {
        "id": expense_id,
        "name": expense_data.name,
        "recordType": "EXPENSE",
        "categoryId": expense_data.categoryId,
        "createdAt": created_at,
        "createdAtEpoch": created_at_epoch,
        "description": expense_data.description,
        "amount": expense_data.amount
    }
    
    try:
        # Save to DDB
        dependencies.db_service.create_record(new_expense)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating expense in database: {str(e)}"
        )
        
    return new_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str):
    """
    Remove an expense from the database by its ID.
    Raises 404 if the record does not exist or is not an EXPENSE.
    """
    try:
        # Check if record exists first
        record = dependencies.db_service.get_record(expense_id)
        if not record or record.get("recordType") != "EXPENSE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with ID '{expense_id}' not found."
            )
        
        dependencies.db_service.delete_record(expense_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting expense from database: {str(e)}"
        )

