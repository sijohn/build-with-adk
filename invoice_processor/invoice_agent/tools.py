import os
from google.cloud import bigquery
from .pydantic_model import Receipt
from google.adk.tools import ToolContext
import json

def log_expense_to_bigquery(receipt: Receipt, tool_context: ToolContext) -> dict:
    """
    Logs a receipt's data into a BigQuery table.

    Args:
        receipt (Receipt): The Pydantic model containing the receipt data.
        tool_context (ToolContext): The context provided by the ADK framework.

    Returns:
        dict: A dictionary with the status of the operation and the inserted record ID.
    """
    try:
        print("########### Starting log_expense_to_bigquery...")
        # --- FIX: Instantiate the Pydantic model from the input dictionary ---
        try:
            receipt_obj = Receipt(**receipt)
        except Exception as pydantic_error:
            print(f"Error creating Receipt model from dict: {pydantic_error}")
            return {"status": "error", "message": f"Invalid receipt data structure: {pydantic_error}"}
        # --- END FIX ---
        project_id = os.environ.get("GCP_PROJECT_ID", "aclarity-saas-platform")
        dataset_id = "finance_data"
        table_id = "expenses"

        client = bigquery.Client(project=project_id)

        # Ensure dataset exists
        dataset_ref = client.dataset(dataset_id)
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            print(f"Dataset {dataset_id} not found, creating it.")
            dataset = bigquery.Dataset(dataset_ref)
            client.create_dataset(dataset, timeout=30)

        # Ensure table exists
        table_ref = dataset_ref.table(table_id)
        print(f"########### Checking for table {table_id} in dataset {dataset_id}...")
        try:
            client.get_table(table_ref)
        except Exception:
            print(f"Table {table_id} not found, creating it.")
            schema = [
                bigquery.SchemaField("vendor_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("transaction_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("total_amount", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("line_items", "STRING", mode="NULLABLE"), # Storing as JSON string
            ]
            table = bigquery.Table(table_ref, schema=schema)
            client.create_table(table, timeout=30)

        # Prepare data for insertion
        print("########### Preparing data for insertion...")
        print(f"##############Receipt data: {receipt_obj}")
        line_items_json = json.dumps([item.model_dump() for item in receipt_obj.line_items])
        row_to_insert = {
            "vendor_name": receipt_obj.vendor_name,
            "transaction_date": receipt_obj.transaction_date,
            "total_amount": receipt_obj.total_amount,
            "category": receipt_obj.category,
            "line_items": line_items_json
        }
        print(f"Inserting row: {row_to_insert}")
        errors = client.insert_rows_json(table_ref, [row_to_insert])
        if not errors:
            print("New expense record has been added to BigQuery.")
            # In a real scenario, you might query for the inserted ID
            return {"status": "success", "record_id": "simulated_id_12345"}
        else:
            print(f"Encountered errors while inserting rows: {errors}")
            return {"status": "error", "message": str(errors)}
    except Exception as e:
        print(f"An error occurred while logging to BigQuery: {e}")
        return {"status": "error", "message": str(e)}
