import json
import os
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

def main(event, context):

    pipeline_id = os.environ.get('PIPELINE_ID', 'Unknown')
    table_name = os.environ.get('TABLE_NAME')
    queue_url = os.environ.get('QUEUE_URL')
    bucket_name = os.environ.get('BUCKET_NAME')

    logger.info(f" Execution started for pipeline: {pipeline_id}")
    logger.info(f" Event received: {json.dumps(event)}")

    response_message = f"Processed by {pipeline_id}"

    try:
        if table_name:
            table = dynamodb.Table(table_name)
            timestamp = datetime.utcnow().isoformat()
            request_id = context.aws_request_id
            
            table.put_item(Item={
                'id': request_id,
                'timestamp': timestamp,
                'type': 'execution_log',
                'event_source': 'lambda'
            })
            logger.info(f"✅ Logged to DynamoDB table: {table_name}")
            response_message += " | Saved to DB"

        if queue_url:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({'task': 'process_something', 'source': pipeline_id})
            )
            logger.info(f"✅ Message sent to SQS: {queue_url}")
            response_message += " | Sent to Queue"

        if bucket_name:
            logger.info(f"ℹ Environment has access to bucket: {bucket_name}")

    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}")
        raise e

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': response_message,
            'pipeline': pipeline_id,
            'request_id': context.aws_request_id
        })
    }