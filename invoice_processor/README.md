# Invoice Processor Agent Codelab

Welcome to the Invoice Processor Agent project! This document serves as a detailed guide and the basis for a codelab to help you understand and build a multi-agent system using the Google Agent Development Kit (ADK).

This agent automates the process of expense tracking by taking a receipt image, extracting its details, classifying the expense category, and logging it into a financial database in BigQuery.

## Table of Contents
1.  [Project Overview](#project-overview)
2.  [Project Structure](#project-structure)
3.  [Core Concepts: Data Models](#core-concepts-data-models)
4.  [Core Components: The Agents](#core-components-the-agents)
    *   [1. OCR Extractor Agent](#1-ocr-extractor-agent)
    *   [2. Category Classifier Agent](#2-category-classifier-agent)
    *   [3. Finance Logger Agent](#3-finance-logger-agent)
5.  [Core Components: The Tool](#core-components-the-tool)
6.  [Workflow Orchestration](#workflow-orchestration)
7.  [Setup and How to Run](#setup-and-how-to-run)
    *   [Prerequisites](#prerequisites)
    *   [Configuration](#configuration)
    *   [Testing with the ADK Web UI](#testing-with-the-adk-web-ui)
    *   [Running the Agent Programmatically](#running-the-agent-programmatically)
8.  [Conclusion](#conclusion)

---

## Project Overview

The goal of this project is to create a robust, autonomous agent that can process expense receipts. The workflow is broken down into three main steps, each handled by a specialized agent:

1.  **Extraction:** An Optical Character Recognition (OCR) agent analyzes a receipt image to extract structured data (vendor, date, total, line items).
2.  **Classification:** A classifier agent takes the extracted data and determines the appropriate expense category (e.g., Dining, Groceries, Travel).
3.  **Logging:** A finance agent takes the structured, categorized data and logs it into a BigQuery table for permanent storage and analysis.

This entire process is orchestrated by a "root" agent that ensures each step is executed in the correct sequence.

A key feature of this project is its use of **multimodality**. The first agent in the chain (`ocr_extractor_agent`) leverages the power of Gemini's multimodal capabilities to understand the content of an image. It takes an unstructured input (the receipt image) and transforms it into a structured, predictable output that conforms to a Pydantic schema. This demonstrates how to bridge the gap between visual data and type-safe, structured data that can be reliably used in downstream automated workflows.

## Project Structure

The project code is organized into the following files within the `invoice_agent/` directory:

```
invoice_agent/
├── __init__.py           # Makes the directory a Python package.
├── agent.py              # Defines the core agents and their orchestration.
├── pydantic_model.py     # Defines the data structures (schemas) for the workflow.
└── tools.py              # Defines custom tools the agents can use (e.g., BigQuery logger).
```

-   **`pydantic_model.py`**: Contains the Pydantic models that define the shape of the data passed between agents, ensuring type safety and clear structure.
-   **`tools.py`**: Holds the `log_expense_to_bigquery` function, a custom tool that allows the agent to interact with an external service (Google BigQuery).
-   **`agent.py`**: This is the heart of the project. It defines the three specialized `LlmAgent`s and the `SequentialAgent` that coordinates their execution.

## Core Concepts: Data Models

Clear data schemas are essential for a reliable multi-agent system. We use Pydantic to define our data models.

**File: `pydantic_model.py`**

1.  **`LineItem`**: Represents a single item on a receipt.
    ```python
    class LineItem(BaseModel):
        description: str = Field(description="Description of the item purchased.")
        quantity: int = Field(description="Quantity of the item purchased.")
        price: float = Field(description="Price of the item purchased.")
    ```

2.  **`Receipt`**: Represents the entire receipt. It contains vendor details and a list of `LineItem`s. The `category` field is initially empty and gets populated by the classification agent.
    ```python
    class Receipt(BaseModel):
        vendor_name: str = Field(description="Name of the vendor or store.")
        transaction_date: str = Field(description="Date of the transaction in YYYY-MM-DD format.")
        total_amount: float = Field(description="Total amount of the transaction.")
        line_items: List[LineItem] = Field(description="List of items purchased.")
        category: Optional[str] = Field(description="Expense category...", default=None)
    ```

## Core Components: The Agents

Our workflow is powered by three distinct agents, each built using the ADK's `LlmAgent`.

**File: `agent.py`**

### 1. OCR Extractor Agent

This is the first agent in our sequence. Its job is to simulate OCR extraction.

-   **Name**: `ocr_extractor_agent`
-   **Description**: "Parses a receipt image and extracts structured data."
-   **Model**: `gemini-2.0-flash` (A multimodal model)
-   **Input Schema**: `OcrInput` (which just contains an `image_path`).
-   **Output Schema**: `Receipt` (our detailed Pydantic model).
-   **Instruction**: The agent is prompted to act as an OCR engine. Given an image path, it must extract key details. For this codelab, it's instructed to **generate realistic mock data** that conforms to the `Receipt` schema. This allows us to simulate the OCR process without needing a real OCR API.

```python
ocr_extractor_agent = LlmAgent(
    name="ocr_extractor_agent",
    model="gemini-2.0-flash",
    description="Parses a receipt image and extracts structured data.",
    instruction="""You are an OCR (Optical Character Recognition) agent...
    You must return the extracted information in a structured JSON format conforming to the Receipt model...
    """,
    input_schema=OcrInput,
    output_schema=Receipt,
    output_key="extracted_receipt"
)
```
The `output_key="extracted_receipt"` tells the ADK to store this agent's output in the session state under the key `extracted_receipt` so subsequent agents can access it.

### 2. Category Classifier Agent

This agent takes the data from the OCR agent and adds intelligence by categorizing it.

-   **Name**: `category_classifier_agent`
-   **Description**: "Classifies the expense category based on receipt data."
-   **Model**: `gemini-2.0-flash`
-   **Input**: It implicitly reads the `extracted_receipt` from the session state.
-   **Output Schema**: `ClassificationOutput` (which contains a single `category` string).
-   **Instruction**: The agent is told to analyze the vendor name and line items from the receipt data to determine the best category from a predefined list: `Dining, Groceries, Fuel, Travel, Entertainment, Other`.

```python
category_classifier_agent = LlmAgent(
    name="category_classifier_agent",
    model="gemini-2.0-flash",
    description="Classifies the expense category based on receipt data.",
    instruction="""You are an expense categorization agent...
    The receipt data will be available in the session state under the key 'extracted_receipt'.
    """,
    output_schema=ClassificationOutput,
    output_key="classified_category"
)
```
Its output is stored in the session state under the key `classified_category`.

### 3. Finance Logger Agent

The final agent in the chain performs an action: logging the data to an external system.

-   **Name**: `finance_logger_agent`
-   **Description**: "Logs the classified expense into a financial system (BigQuery)."
-   **Model**: `gemini-2.0-flash`
-   **Tools**: It is equipped with the `log_expense_to_bigquery` tool.
-   **Instruction**: The agent is instructed to take the final categorized data (from `extracted_receipt` and `classified_category` in the session state) and call the provided tool to log it.

```python
finance_logger_agent = LlmAgent(
    name="finance_logger_agent",
    model="gemini-2.0-flash",
    description="Logs the classified expense into a financial system (BigQuery).",
    instruction="""You are a finance logging agent...
    You must call the tool with the correct data...
    """,
    tools=[log_expense_to_bigquery]
)
```

## Core Components: The Tool

Agents become powerful when they can interact with the outside world. Our `finance_logger_agent` uses a tool to do just that.

**File: `tools.py`**

The `log_expense_to_bigquery` function is a standard Python function decorated to be a tool.

-   **Functionality**: It connects to Google BigQuery, creates a dataset (`finance_data`) and a table (`expenses`) if they don't already exist, and inserts the final receipt data as a new row.
-   **Schema**: The BigQuery table schema is defined within the tool itself. Note that the `line_items` list is converted to a JSON string for storage.
-   **Authentication**: It uses the application default credentials via the `bigquery.Client()`. The GCP Project ID is fetched from the `GCP_PROJECT_ID` environment variable.

```python
def log_expense_to_bigquery(receipt: Receipt, tool_context: ToolContext) -> dict:
    """
    Logs a receipt's data into a BigQuery table.
    """
    # ... (BigQuery client setup)
    project_id = os.environ.get("GCP_PROJECT_ID", "your-default-project-id")
    # ... (Dataset and table creation logic)
    # ... (Row insertion logic)
    return {"status": "success", "record_id": "simulated_id_12345"}
```

## Workflow Orchestration

With the individual agents defined, we need a way to run them in the correct order. The ADK's `SequentialAgent` is perfect for this.

**File: `agent.py`**

The `root_agent` defines the end-to-end workflow.

```python
root_agent = SequentialAgent(
    name="expense_tracker_orchestrator",
    sub_agents=[
        ocr_extractor_agent,
        category_classifier_agent,
        finance_logger_agent
    ],
    description="Orchestrates the entire expense tracking workflow from OCR to logging."
)
```

When this agent is run, it will execute the `sub_agents` in the provided list, one after the other. The session state (containing `extracted_receipt` and `classified_category`) is automatically passed between them, creating a data pipeline.

## Setup and How to Run

### Prerequisites

1.  Python 3.10+
2.  Google Cloud SDK installed and authenticated (`gcloud auth application-default login`).
3.  A Google Cloud Project with the BigQuery API enabled.
4.  The required Python packages installed (e.g., `google-cloud-bigquery`, `google-adk`, `uv`).

### Configuration

Before running the agent, you must set the following environment variable:

```bash
export GCP_PROJECT_ID="your-gcp-project-id"
```
Replace `"your-gcp-project-id"` with your actual Google Cloud Project ID.

### Testing with the ADK Web UI

The Google ADK comes with a built-in web server for interactively testing your agents. This is the easiest way to get started.

1.  **Start the web server:**
    ```bash
    uv run adk web
    ```

2.  **Open your browser:** Navigate to the URL provided in the terminal (usually `http://127.0.0.1:8000`).

3.  **Interact with the agent:**
    *   From the dropdown menu, select the `expense_tracker_orchestrator` agent.
    *   In the input box, provide the path to a receipt image, like so:
        ```json
        {"image_path": "path/to/your/receipt.jpg"}
        ```
    *   Click "Run" to start the workflow. You will see the outputs from each agent in the sequence.

### Running the Agent Programmatically

You can also invoke the agent workflow from a simple Python script. Create a file named `main.py` at the root of the project:

```python
# main.py
import asyncio
from invoice_agent.agent import root_agent

async def main():
    # The input for the first agent in the sequence
    initial_input = {"image_path": "receipts/grocery_receipt_01.jpg"}

    # Invoke the sequential agent
    final_result = await root_agent.invoke(initial_input)

    # Print the final output from the last agent
    print("
--- Agent Workflow Complete ---")
    print(final_result)
    print("-----------------------------
")

if __name__ == "__main__":
    asyncio.run(main())

```

To run the script, execute the following command in your terminal:

```bash
python main.py
```

The agent will then:
1.  Generate mock receipt data.
2.  Classify the category.
3.  Log the data to your BigQuery project.
4.  Print the confirmation message from the `finance_logger_agent`.

## Conclusion

This project demonstrates how to build a powerful, modular, and stateful multi-agent system using the Google Agent Development Kit. By breaking down a complex task into smaller, specialized agents, leveraging multimodality, and equipping them with tools, you can automate sophisticated workflows. This codelab provides a solid foundation for building your own production-ready agents.
