#!/usr/bin/env python
import os
import sys
import json
import argparse
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError
## predefined inference profiles:
# us.meta.llama3-1-8b-instruct-v1:0
# us.meta.llama3-2-90b-instruct-v1:0
# us.meta.llama3-3-70b-instruct-v1:0
# us.deepseek.r1-v1:0
# us.anthropic.claude-3-haiku-20240307-v1:0
# us.anthropic.claude-3-5-haiku-20241022-v1:0
# us.anthropic.claude-3-5-sonnet-20241022-v2:0
# us.anthropic.claude-3-7-sonnet-20250219-v1:0

##### this should work:
# uv run ./testrock.py -D -p 'who are you' -m 'arn:aws:bedrock:us-east-1::inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0'
## or without specify region:
# uv run ./testrock.py -D -p 'who are you' -m 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'

def showDiag(response, client, model_id):
  # Extract diagnostic information
  response_metadata = response.get('ResponseMetadata', {})
  request_id = response_metadata.get('RequestId', 'Unknown')
  http_status_code = response_metadata.get('HTTPStatusCode', 'Unknown')
  service_endpoint = client._endpoint.host
  client_region = client.meta.region_name
  env_region = os.getenv('AWS_REGION')
  headers = response_metadata.get('HTTPHeaders', {})
  # Print diagnostic information
  print("\n=== BEDROCK INVOCATION DIAGNOSTICS ===")
  print(f"Request ID: {request_id}")
  print(f"HTTP Status Code: {http_status_code}")
  print(f"Service Endpoint: {service_endpoint}")
  print(f"Client Region: {client_region}")
  print(f"Environment Region: {env_region}")
  print(f"Model ID: {model_id}")
  print(f"Response Headers:")
  for key, value in headers.items():
      print(f"  {key}: {value}")
  print("=====================================\n")# Extract diagnostic information
  response_metadata = response.get('ResponseMetadata', {})
  request_id = response_metadata.get('RequestId', 'Unknown')
  http_status_code = response_metadata.get('HTTPStatusCode', 'Unknown')
  service_endpoint = client._endpoint.host
  client_region = client.meta.region_name
  env_region = os.getenv('AWS_REGION')
  headers = response_metadata.get('HTTPHeaders', {})

  # Print diagnostic information
  print("\n=== BEDROCK INVOCATION DIAGNOSTICS ===")
  print(f"Request ID: {request_id}")
  print(f"HTTP Status Code: {http_status_code}")
  print(f"Service Endpoint: {service_endpoint}")
  print(f"Client Region: {client_region}")
  print(f"Environment Region: {env_region}")
  print(f"Model ID: {model_id}")
  print(f"Response Headers:")
  for key, value in headers.items():
      print(f"  {key}: {value}")
  print("=====================================\n")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Interact with Amazon Bedrock models')
    
    parser.add_argument('-l', '--list', action='store_true', help='List inference profiles')
    parser.add_argument('-p', '--prompt', type=str, help='Prompt to send to the model')
    parser.add_argument('-m', '--model', type=str, help='Model to use for the prompt')
    parser.add_argument('-t', '--max_tokens', type=int, default=1024, help='Max tokens to use for the prompt')
    parser.add_argument('-D', '--diag', action='store_true', help='Show diagnostics of model invocation')
    parser.add_argument('-T', '--temp', type=float, default=0.5, help='Temperature')

    if len(sys.argv) == 1:
       parser.print_help(sys.stderr)
       sys.exit(1)

    args = parser.parse_args()

    # Load environment variables from .env file
    if not os.path.exists('.env'):
        print("Error: .env file not found in current directory")
        sys.exit(1)

    load_dotenv()

    # Check if required AWS credentials are in the .env file
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        sys.exit(1)
    # Handle list vs model inference use cases
    if bool(args.list) and (bool(args.prompt) or bool(args.model)):
        print("Error:  -l/--list option cannot be used with other options")
        sys.exit(1)
    # Initialize Bedrock client
    client = None
    try:
        if args.list:
          # For listing models, we need the bedrock client (not bedrock-runtime)
          client = boto3.client(
                'bedrock',
                region_name=os.getenv('AWS_REGION'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
          )
        else:
          client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
          )
    except Exception as e:
        print(f"Error initializing Bedrock client: {str(e)}")
        sys.exit(1)
    # List foundation models if -l flag is provided
    if args.list:
      try:
        #response = client.list_foundation_models()
        response = client.list_inference_profiles(typeEquals='SYSTEM_DEFINED')
        print("Available inference profiles:")
        #print(json.dumps(response, indent=2, default=str))
        if 'inferenceProfileSummaries' in response:
          for profile in response['inferenceProfileSummaries']:
              # Get detailed information for each profile
              detail_response = client.get_inference_profile(
                  inferenceProfileIdentifier=profile['inferenceProfileArn']
              )
              # Extract model ARNs
              model_arns = []
              if 'models' in detail_response:
                  model_arns = [model['modelArn'] for model in detail_response['models']]
              print("> "+detail_response.get('inferenceProfileName', 'N/A')+" : modelId: "+
                  detail_response.get('inferenceProfileId', 'N/A'))
              print(detail_response.get('inferenceProfileArn', 'N/A') +
                 " | "+model_arns[0])
        else:
          print("No inference profiles found.")
        sys.exit(0)
      except Exception as e:
        print(f"Error listing foundation models: {str(e)}")
        sys.exit(1)
    # Handle prompt and model arguments
    if bool(args.prompt) != bool(args.model):
      print("Error: Both -p/--prompt and -m/--model must be provided together")
      sys.exit(1)
    if args.prompt and args.model:
      model_id=args.model
      #model_id = "amazon.titan-text-express-v1"
      prompt=args.prompt
      isClaude=("claude" in args.model.lower())
      isTitan=("titan" in args.model.lower())
      isLlama=("llama" in args.model.lower())
      isDeepseek=("deepseek" in args.model.lower())
      try:
          # Format the request payload using the model's native structure.
          request = None
          if isClaude:
             request = json.dumps({
              "max_tokens": args.max_tokens,
              "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
              "anthropic_version": "bedrock-2023-05-31"
            })
          elif isLlama:
            request = json.dumps({
                "prompt": args.prompt,
                "max_gen_len": args.max_tokens,
                "temperature": args.temp,
            })
          elif isDeepseek:
            request = json.dumps({
                "prompt": args.prompt,
                "max_tokens": args.max_tokens,
                "temperature": args.temp,
            })
          elif isTitan: ## Titan models etc. work like this
            request = json.dumps({
                "inputText": args.prompt,
                "textGenerationConfig": {
                    "maxTokenCount": args.max_tokens,
                    "temperature": args.temp,
                },
            })
          else:
            print("Error: Model not supported for now.")
            sys.exit(1)
            # Invoke the model with the request.
          response = client.invoke_model(modelId=model_id, body=request,
             contentType="application/json",  accept="application/json")
          if args.diag:
             showDiag(response, client, model_id)
          model_response = json.loads(response["body"].read())
          # Extract and print the response text.
          if isClaude:
            response_text = model_response["content"][0]["text"]
          elif isTitan: ## Titan models
            response_text = model_response["results"][0]["outputText"]
          elif isLlama:
            response_text = model_response["generation"]["text"]
          elif isDeepseek:
            response_text = model_response.get("choices", [{}])[0].get("text", "")
          else:
            print("Error: Model not supported for now.")
            sys.exit(1)
          print(response_text)
      except ClientError as e:
          # Get the specific AWS error code and message
          error_code = e.response.get('Error', {}).get('Code', 'Unknown')
          error_message = e.response.get('Error', {}).get('Message', 'No message')
          print(f"AWS ClientError: {error_code} - {error_message}")
          print(f"Full error response: {e.response}")
          exit(1)
      except Exception as e:
          # For other types of exceptions
          import traceback
          print(f"ERROR: Failed invoking '{model_id}'. Reason: {e}")
          print(f"Error type: {type(e).__name__}")
          print(f"Traceback: {traceback.format_exc()}")
          exit(1)          # Decode the response body.

if __name__ == "__main__":
    main()
