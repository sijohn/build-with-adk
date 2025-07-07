# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent,BaseAgent,SequentialAgent
from pydantic import BaseModel, Field

from .pydantic_model import Receipt

# Import the tools
from .tools import log_expense_to_bigquery


class OcrInput(BaseModel):
    image_path: str = Field(description="The path to the receipt image file.")

class ClassificationOutput(BaseModel):
    category: str = Field(description="The classified expense category.")



ocr_extractor_agent = LlmAgent(
    name="ocr_extractor_agent",
    model="gemini-2.0-flash",
    description="Parses a receipt image and extracts structured data.",
    instruction="""You are an OCR (Optical Character Recognition) agent.
    Given the path to an image of a receipt, your task is to extract the following information:
    - Vendor Name
    - Transaction Date
    - Total Amount
    - A list of all line items, including their description, quantity, and price.

    You must return the extracted information in a structured JSON format conforming to the Receipt model.
    For the purpose of this simulation, you will generate realistic mock data based on the image path.
    For example, if the image_path contains 'grocery', generate grocery-related items.
    """,
    input_schema=OcrInput,
    output_schema=Receipt,
    output_key="extracted_receipt"
)

category_classifier_agent = LlmAgent(
    name="category_classifier_agent",
    model="gemini-2.0-flash",
    description="Classifies the expense category based on receipt data.",
    instruction="""You are an expense categorization agent.
    Given the structured data from a receipt (vendor name and line items), determine the most appropriate expense category.
    The possible categories are: Dining, Groceries, Fuel, Travel, Entertainment, and Other.
    Analyze the vendor name and the descriptions of the line items to make your classification.
    Return only the determined category as a string.

    The receipt data will be available in the session state under the key 'extracted_receipt'.
    """,
    output_schema=ClassificationOutput,
    output_key="classified_category"
)

finance_logger_agent = LlmAgent(
    name="finance_logger_agent",
    model="gemini-2.0-flash",
    description="Logs the classified expense into a financial system (BigQuery).",
    instruction="""You are a finance logging agent.
    Your task is to take the final, categorized expense data and log it into the company's financial system using the 'log_expense_to_bigquery' tool.
    The receipt data will be in the session state under 'extracted_receipt' and the category under 'classified_category'.
    You must call the tool with the correct data.
    After successfully calling the tool, respond with a confirmation message including the status and record ID returned by the tool.
    """,
    tools=[log_expense_to_bigquery]
)

root_agent = SequentialAgent(
    name="expense_tracker_orchestrator",
    sub_agents=[
        ocr_extractor_agent,
        category_classifier_agent,
        finance_logger_agent
    ],
    description="Orchestrates the entire expense tracking workflow from OCR to logging."
)
