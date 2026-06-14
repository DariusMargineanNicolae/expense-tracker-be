import os
import boto3

def main():
    table_name = os.getenv("EXPENSES_TRACKER_DDB_TABLE_NAME", "ExpenseTracker")
    print(f"Table Name: {table_name}")
    try:
        client = boto3.client("dynamodb")
        desc = client.describe_table(TableName=table_name)
        table = desc["Table"]
        print("KeySchema:", table.get("KeySchema"))
        gsis = table.get("GlobalSecondaryIndexes", [])
        print(f"Found {len(gsis)} GSIs:")
        for gsi in gsis:
            print(f" - IndexName: {gsi['IndexName']}")
            print(f"   KeySchema: {gsi['KeySchema']}")
            print(f"   Projection: {gsi['Projection']}")
    except Exception as e:
        print("Error describing table:", e)

if __name__ == "__main__":
    main()
