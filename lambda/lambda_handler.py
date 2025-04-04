from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph,START,END
from langchain_aws import ChatBedrock, ChatBedrockConverse

from pathlib import Path
import base64
from io import BytesIO
from mistralai import Mistral
from typing_extensions import TypedDict
import os
from dotenv import load_dotenv
import boto3
import json

load_dotenv('env.txt')

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
bedrock_runtime_client = boto3.client("bedrock-runtime", region_name='us-east-1')
# Initialize clients
summary_llm = ChatBedrockConverse(
        client=bedrock_runtime_client,
        model="amazon.nova-pro-v1:0",
        temperature=0.1)

analyzer_llm = ChatBedrockConverse(
        client=bedrock_runtime_client,
        model="amazon.nova-pro-v1:0",
        temperature=0.1)


class InvoiceAnalysisState(TypedDict):
    file_content: str
    context: str
    analysis_result: str
    summary: str
    validation_result:str

        
def create_invoice_analysis_chain():    

    def extract_context(state: InvoiceAnalysisState):
        print("----------------------------------------------------")
        print("-----------Extracting context from PDF--------------")
        print("----------------------------------------------------")
        state['context'] = state['file_content']
        return state
    
    def analyze_document(state: InvoiceAnalysisState):
        print("----------------------------------------------------")
        print("-----------Analyzing context from PDF--------------")
        print("----------------------------------------------------")
        messages = state['context']
        document_content = messages
        
    # Use Langchain groq for medical analysis
        messages = [
            SystemMessage(content="""You are a invoice document analyzer. Extract key information and format it in markdown with the following sections:

                ### Seller Details
                - Seller Name
                - Seller Address
        
                ### Buyer Details
                - Name of the buyer
                - Buyer Address
                - GST Number
                - PAN Number
                - State/UT Code

                ### Order Details
                  - Order Number
                  - Order Date

                ### Invoice Details
                - Invoice Number 
                - Invoice Details
                - Invoice Date
                
                ### Item Details
                -  Total Amount
                
                ## Signature Details( Provide Yes if signed, else No)
                - Is it signed ? 

                ### Payment Details
                - List of Transaction Ids
                - List of Timestamp for transactio
                - Mode of Payment
                - Invoice Value
                Please ensure the response is well-formatted in markdown with appropriate headers and bullet points."""),
            HumanMessage(content=document_content)
        ]
        response = analyzer_llm.invoke(messages)
        
        state["analysis_result"] = response.content.split("</think>")[-1]
        return state


    def validate_invoice(state:InvoiceAnalysisState):
        print("----------------------------------------------------")
        print("------------Validating invoice from PDF-----------")
        print("----------------------------------------------------")
        analysis_result = state["analysis_result"]
        
        messages = [
            SystemMessage(content="""You are a invoice  validator. Provide your assessment in markdown format with these sections:

                ### Invoice Analysis
                - Check if there is invoice number in invoice
                - Check if there is Seller/ Billing Details
                - Evaluate if there GST Number/PAN Number in invoice
                - Table exists with item details and total amount
                - Check if payment details exist along with transaction id with invoice value

                Please format your response in clear markdown with appropriate headers and bullet points."""),
            HumanMessage(content=f"""Analysis: {analysis_result}
                         Based on the Analysis  provided please provide whether given invoice is a valid.
                         If not mention its not valid invoice, and also mention what details are missing from the invoice.
                         """)
        ]
        response = analyzer_llm.invoke(messages)
        
        state["validation_result"] = response.content.split("</think>")[-1]
        return state
    
    workflow = StateGraph(InvoiceAnalysisState)

    # Add nodes
    workflow.add_node("extractor", extract_context)
    workflow.add_node("analyzer", analyze_document)
    workflow.add_node("validator", validate_invoice)

    # Define edges
    workflow.add_edge(START, "extractor")
    workflow.add_edge("extractor", "analyzer")  
    workflow.add_edge("analyzer", "validator")
    workflow.add_edge("validator", END)


    # Compile the graph
    chain = workflow.compile()
    
    # Generate graph visualization
    graph_png = chain.get_graph().draw_mermaid_png()
    graph_base64 = base64.b64encode(graph_png).decode('utf-8')
    
    return chain, graph_base64

def handler(event, context):
    text = event.get('pdfcontent', 'Extracted text from pdf content')
    chain, graph_viz = create_invoice_analysis_chain()
    response = chain.invoke({"file_content": text})
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }