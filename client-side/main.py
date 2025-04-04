import streamlit
from mistralai import Mistral

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def extracttpdf(client, content, file_name):
  uploaded_pdf = client.files.upload(
    file={
        "file_name": "pdf_name",
        "content": open(pdf_name, "rb"),
    },
    purpose="ocr"
  )
  #
  signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
  #
  ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": signed_url.url,
    }
  )
  #
  text = "\n\n".join([page.markdown for page in ocr_response.pages])
  return text

def invoke_invoice_analyze_lambda(query:str):
     lambda_client = boto3.client(
          'lambda',
          region_name='us-east-1',
          aws_access_key_id=workspace_credentials['AccessKeyId'],
          aws_secret_access_key=workspace_credentials['SecretAccessKey'],
          aws_session_token=workspace_credentials['SessionToken'])

    payload = {
        "query": query
    }

    # Invoke the Lambda function
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',  # 'Event' for async invocation
        Payload=json.dumps(payload)
    )

    # Parse the response
    response_payload = json.loads(response['Payload'].read())
     # Check if statusCode is 200
    if response_payload.get('statusCode') == 200:
        print("Lambda function invocation successful")
        text=response_payload['body']
        plain_text = text.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"").replace("\\'", "'")
        return plain_text
    else:
        print("Lambda function invocation failed")
        print("Response:")
        return response_payload



st.title("Invoice Anayzer and Extractor 🧾📝")
uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"])

if uploaded_file and st.button("Analyze Document"):
    content = uploaded_file.read()
