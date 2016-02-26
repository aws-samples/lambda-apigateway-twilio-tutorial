'''
Twilio Ingest Lambda handler code

Recieve an image URL from Twilio 
Apply a filter to the image and store in S3
Return filtered image URL to the user

'''

import boto3
import random
import StringIO
import urllib2

from boto3.dynamodb.conditions import Key
from boto3.session import Session
from PIL import ImageOps
from twilio.rest import TwilioRestClient


# create Twilio session
# Add Twilio Keys
account_sid = "account_sid"
auth_token = "auth_token"
client = TwilioRestClient(account_sid, auth_token)

# create an S3 & Dynamo session
s3 = boto3.resource('s3')
session = Session()
# Add Dynamo Region and Table
dynamodb = boto3.resource('dynamodb', '_region_')
table_users = dynamodb.Table('table_name')

def sample_filter(im):
    '''
    A simple filter to be applied to the image
    '''
    black = "#000099"
    white= "#99CCFF"
    filter_image = ImageOps.colorize(ImageOps.grayscale(im), black, white)
    return filter_image

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

        # Apply an Image filter
        im_buffer = image.read()
        im = Image.open(StringIO.StringIO(im_buffer))
        im = sample_filter(im)	

        # Add to S3 Bucket
        bucket = "s3_bucket_name"
        key = "ingest-images/" + str(from_number.replace('+', '')) + "/" + str(random.getrandbits(50)) + ".png"
        resp_url = "https://s3-us-west-2.amazonaws.com/{0}/{1}".format(bucket, str(key))
        twilio_resp = "Hi {0}, your S3 link: ".format(name) + resp_url

        # build meta data
        m_data = {'fromNumber': from_number, 'url': resp_url, 'name': name}
        output = StringIO.StringIO()
        im.save(output)
        im_data = output.getvalue()
        output.close()

        s3.Bucket(bucket).put_object(Key=key, Body=im_data, ACL='public-read', ContentType='image/png', Metadata=m_data)
    else:
        twilio_resp = 'No image found'
    
    return twilio_resp
