'''
Basic Twilio handler function
'''

import boto3
import random
import StringIO
import urllib2

from boto3.dynamodb.conditions import Key
from boto3.session import Session

# create an S3 & Dynamo session
s3 = boto3.resource('s3')
session = Session()

def lambda_handler(event, context):

    message = event['body']
    from_number = event['fromNumber']
    pic_url = event['image']
    num_media = event['numMedia']

    if num_media != '0':
        twilio_resp = "Hi I got an image @ location %s" % pic_url
    else:
        twilio_resp = 'No image found'
    
    return twilio_resp
