import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from strands import tool


load_dotenv()


@tool
def search_scheme_knowledge(query: str) -> str:
    """
    Search official government scheme documents using the
    Amazon Bedrock Knowledge Base.
    """

    if not query or not query.strip():
        return "Please provide a question about an official government scheme document."

    knowledge_base_id = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")

    if not knowledge_base_id or knowledge_base_id == "YOUR_REAL_KNOWLEDGE_BASE_ID":
        return "Knowledge Base is not configured yet."

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=os.getenv("AWS_REGION", "ap-south-1")
    )

    try:
        response = client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                "text": query
            }
        )
    except (BotoCoreError, ClientError):
        return "Official document search is currently unavailable. Please try again later."

    results = response.get("retrievalResults", [])

    if not results:
        return "No relevant information was found in the official documents."

    output = []

    for result in results[:5]:
        text = result.get("content", {}).get("text", "")
        location = result.get("location", {})

        output.append(
            f"Source: {location}\n"
            f"Content: {text}"
        )

    return "\n\n---\n\n".join(output)