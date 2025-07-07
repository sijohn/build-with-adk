from pydantic import BaseModel, Field
from typing import List, Optional

class LineItem(BaseModel):
    description: str = Field(description="Description of the item purchased.")
    quantity: int = Field(description="Quantity of the item purchased.")
    price: float = Field(description="Price of the item purchased.")

class Receipt(BaseModel):
    vendor_name: str = Field(description="Name of the vendor or store.")
    transaction_date: str = Field(description="Date of the transaction in YYYY-MM-DD format.")
    total_amount: float = Field(description="Total amount of the transaction.")
    line_items: List[LineItem] = Field(description="List of items purchased.")
    category: Optional[str] = Field(description="Expense category (e.g., Groceries, Fuel, Dining).", default=None)
