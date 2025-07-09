## Run Locally 

uv init 

uv add google-adk

uv run adk create doc_processor_agent


## Deploy to Cloud Run

### Set your Google Cloud Project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

### Set your desired Google Cloud Location
export GOOGLE_CLOUD_LOCATION="us-central1"

### Set the path to your agent code directory
export AGENT_PATH="./doc_processor_agent"

### Set a name for your Cloud Run service (optional)
export SERVICE_NAME="doc-processor-agent-service"

### Set an application name (optional)
export APP_NAME="doc-processor-agent-app"

adk deploy cloud_run \
--project=$GOOGLE_CLOUD_PROJECT \
--region=$GOOGLE_CLOUD_LOCATION \
--service_name=$SERVICE_NAME \
--app_name=$APP_NAME \
--with_ui \
$AGENT_PATH