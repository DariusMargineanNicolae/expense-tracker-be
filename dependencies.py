from typing import List, Dict, Any, Optional
from services.AWSDdbService import DynamoDbService
from options import Options

# Initialize DynamoDbService using Options
db_service = DynamoDbService(table_name=Options.EXPENSES_TABLE_NAME)

# In-memory cache for categories
categories_cache: Optional[List[Dict[str, Any]]] = None

def get_db_service() -> DynamoDbService:
    return db_service
