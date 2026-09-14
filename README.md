# Jan-SahayakAI

Jan-SahayakAI is an AI-powered Good Neighbour Agent for civic assistance and government scheme guidance. It uses Strands Agents with Amazon Bedrock to understand a resident's request, select the appropriate Python tool, and explain the next practical step.

## What it can do

- Identify likely departments for potholes, damaged roads, garbage, sanitation, water, drainage, streetlight, and electricity issues.
- Collect the required issue, location, and description before preparing a structured complaint.
- Detect identical complaints and return the existing complaint reference instead of creating a duplicate.
- Track a complaint and suggest a follow-up action when it is unresolved.
- Search the JSON-backed scheme catalogue by category and location.
- Show scheme details and perform preliminary, non-binding eligibility comparisons.
- Search official scheme documents through an optional Amazon Bedrock Knowledge Base.
- Provide a Streamlit chat interface with conversation history, quick actions, loading states, and retrieved-source details.

## Requirements

- Python 3.10 or newer
- AWS credentials available through the AWS CLI, AWS SSO, an AWS profile, or another boto3-supported method
- Amazon Bedrock access to the configured model in your selected AWS region

The agent currently uses the Amazon Nova Lite model `apac.amazon.nova-lite-v1:0`.

## Installation

Create and activate a virtual environment, then install the project dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Windows, PowerShell may require this temporary execution-policy command before activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Configuration

The optional `.env` file is loaded automatically by the agent and tools. Do not commit credentials or other secrets.

```dotenv
AWS_DEFAULT_REGION=ap-south-1
AWS_REGION=ap-south-1
BEDROCK_KNOWLEDGE_BASE_ID=your-knowledge-base-id
PM_KISAN_API_URL=https://your-backend.example/api/ask
```

Variables:

| Variable                    | Purpose                                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `AWS_DEFAULT_REGION`        | Default Bedrock region for the agent. Defaults to `ap-south-1`.                                                   |
| `AWS_REGION`                | Region used for Bedrock Knowledge Base retrieval. Defaults to `ap-south-1`.                                       |
| `BEDROCK_KNOWLEDGE_BASE_ID` | Optional Knowledge Base ID for official-document search.                                                          |
| `PM_KISAN_API_URL`          | Required by the Streamlit UI. The endpoint must accept `POST {"question": "..."}` and return `{"answer": "..."}`. |

Configure AWS separately, for example with `aws configure` or AWS SSO. Never place AWS access keys in `.env`.

## Running the application

### Terminal agent

```powershell
python app.py
```

The terminal agent accepts free-form questions. Type `exit` or `quit` to stop.

### Streamlit interface

```powershell
streamlit run ui/app.py
```

The Streamlit application is a frontend client. It sends each question to the service configured by `PM_KISAN_API_URL`; it does not directly create a Strands agent or call Bedrock.

## Architecture

```text
User
  |
  +--> app.py --> agents/jan_sahayak.py --> Amazon Bedrock Nova Lite
  |                                      |
  |                                      +--> Civic and complaint tools
  |                                      +--> Scheme JSON tools
  |                                      +--> Optional Bedrock Knowledge Base
  |
  +--> ui/app.py --> external API configured by PM_KISAN_API_URL
```

Important modules:

- `agents/jan_sahayak.py`: Creates the agent, system prompt, model configuration, and tool list.
- `tools/civic.py`: Identifies departments and prepares civic complaints.
- `tools/complaint.py`: Looks up complaint status.
- `tools/followup.py`: Provides next steps for existing complaints.
- `tools/schemes.py`: Searches `data/schemes/schemes.json`, returns details, and performs preliminary eligibility checks.
- `tools/knowledge_base.py`: Retrieves official-document content from Amazon Bedrock Knowledge Bases when configured.
- `data/store.py`: Stores complaints in the local in-memory demo database.
- `ui/app.py`: Streamlit chat frontend and external API client.

## Data sources and limitations

- Scheme discovery uses the intermediate JSON catalogue at `data/schemes/schemes.json`.
- Official scheme documents are stored under `data/official_schemes`, but they are not read directly by the application. Retrieval requires a configured Bedrock Knowledge Base.
- Complaint records are stored only in memory and disappear when the process stops.
- Complaint creation prepares a record with `READY_FOR_SUBMISSION`; it does not submit anything to a real government department.
- Eligibility results are preliminary and must be verified against the current official government source.
- Knowledge Base search returns only retrieved content and source information. If the Knowledge Base is unavailable or insufficient, the agent should say so rather than guess.

## Testing

Run the local suite without live AWS integrations:

```powershell
pytest --ignore=test_nova.py --ignore=testbedrock.py
```

The tests cover agent behavior, civic workflows, scheme tools, optional Knowledge Base behavior, and Streamlit request handling. The following tests require live AWS/Bedrock access and should be run only when those services are configured:

```powershell
pytest test_nova.py testbedrock.py
```

For the deeper design notes and module-level tool documentation, see [documentation.md](documentation.md). Security guidance is in [SECURITY.md](SECURITY.md).
