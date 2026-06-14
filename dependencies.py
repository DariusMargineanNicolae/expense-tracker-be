from typing import List, Dict, Any, Optional
from services.AWSDdbService import DynamoDbService
from services.AWSS3Service import S3Service
from options import Options

# Initialize DynamoDbService using Options
db_service = DynamoDbService(table_name=Options.EXPENSES_TABLE_NAME)

# Initialize S3Service using Options
s3_service = S3Service(bucket_name=Options.EXPENSES_S3_BUCKET_NAME)

# In-memory cache for categories
categories_cache: Optional[List[Dict[str, Any]]] = None

def get_db_service() -> DynamoDbService:
    return db_service

def get_s3_service() -> S3Service:
    return s3_service
