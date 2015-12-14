
import boto3
import urllib2
import random

from boto3.session import Session
from twilio.rest import TwilioRestClient
from boto3.dynamodb.conditions import Key

# create Twilio session
# 1) Add Twilio Keys
account_sid = "account_sid"
auth_token = "auth_token"
client = TwilioRestClient(account_sid, auth_token)

# create an S3 & Dynamo session
s3 = boto3.resource('s3')
session = Session()
# 2) Add Dynamo Region and Table
dynamodb = boto3.resource('dynamodb', '_region_')
table_users = dynamodb.Table('table_name')


def lambda_handler(event, context):

    message = event['body']
    from_number = event['fromNumber']
    pic_url = event['image']
    num_media = event['numMedia']

    # check if we have their number
    response_dynamo = table_users.query(KeyConditionExpression=Key('fromNumber').eq(from_number))

    # a new user
    if response_dynamo['Count'] == 0:
        if len(message) == 0:
            return "Please send us an SMS with your name first!"
        else:
            name = message.split(" ")
            table_users.put_item(Item={'fromNumber': from_number, 'name': name[0]})
            return "We've added {0} to the system! Now send us a selfie! ".format(name[0])
    else:
        name = response_dynamo['Items'][0]['name']

    if num_media != '0':
        # get photo from s3
        twilio_pic = urllib2.Request(pic_url, headers={'User-Agent': "Magic Browser"})
        image = urllib2.urlopen(twilio_pic)
        # 3) Add S3 Bucket
        bucket = "s3_bucket_name"
        key = "ingest-images/" + str(from_number.replace('+', '')) + "/" + str(random.getrandbits(50)) + ".png"
        resp_url = "https://s3-us-west-2.amazonaws.com/{0}/{1}".format(bucket, str(key))
        twilio_resp = "Hi {0}, your S3 link: ".format(name) + resp_url
        # build meta data
        m_data = {'fromNumber': from_number, 'url': resp_url, 'name': name}
        s3.Bucket(bucket).put_object(Key=key, Body=image.read(), ACL='public-read', ContentType='image/png', Metadata=m_data)
    else:
        twilio_resp = 'No image found'
    
    return twilio_resp
