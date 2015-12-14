#Lambda + API Gateway Example  

This example uses [Twilio](https://www.twilio.com/) to save an image from your mobile phone to the AWS cloud. A user sends an image using MMS to a Twilio phone number which sends a request to an Amazon API Gateway endpoint that triggers a Lambda function. The app then returns a publicly accessible link to the image in AWS S3. This app uses AWS Lambda, API Gateway, DynamoDB & S3. It is also 100% serverless!

###AWS Lambda

[Lambda](https://aws.amazon.com/lambda/) is a compute service that runs your code in response to events. Events are triggered or invoked by resources in your AWS environment or via API Gateway. Here our Lambda function is triggered by an API Gateway endpoint that Twilio hits after an MMS is received. The Lambda function is responsible for writing user info to DynamoDB, writing the image to S3 with meta data and returning a response to Twilio. 

###Amazon API Gateway 
[API Gateway](https://aws.amazon.com/api-gateway/) is a fully managed API as a service where you can create, publish, maintain, monitor, and secure APIs at any scale. In this app, we use API Gateway to create an endpoint for Twilio to make a GET request. API Gateway transforms Twilio's URL encoded request into a JSON object, so that Lambda can process it. Lastly, API Gateway takes Lambda's response and builds an XML object for Twilio. 

###Amazon DynamoDB & Amazon S3
[DynamoDB](https://aws.amazon.com/dynamodb/) is Amazon's non-relational database service. This app leverages DynamoDB to store user data. [S3](https://aws.amazon.com/s3/) provides developers with object level storage that is endlessly scalable. We use S3 to store images received via MMS. 

#Usage 

Try it by sending an MMS to (650) 200-1944. 

![Example](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/screenshot2.png)

S3 Link: https://s3-us-west-2.amazonaws.com/mauerbac-selfie/ingest-images/19145824224/795221908928951.png


# Building the App

Step-by-step on how to configure, develop & deploy this app on AWS.

###Housekeeping
1. Sign-in to AWS or [Create an Account](https://us-west-2.console.aws.amazon.com).
2. Pick a region in the console and be consistent throughout this app. Use either `us-east-1`, `us-west-2` & `eu-west-1`. 
3. Create a table in DynamoDB with a single Hash for primary key of type String. We don't need any additional indexes and you can keep the read/write capacity at 1 for this example. [Screenshot](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/dynamoDB.png)
4. Create an S3 bucket to ingest MMS images. Ex. mauerbac-ingest
5. Create an IAM role with access to the S3 bucket & the DynamoDB table.
6. Create/login to a Twilio account & create a phone number with MMS capability. 

###Lambda
1. Create a new Lambda function. I've provided the function, so we can skip a blueprint.
2. Give it a name and description. Use Python 2.7 for runtime. 
3. Use the given Lambda function, `lambda_function.py`. Read through the module and provide a few variables: Twilio credentials, DynamoDB table name & region and S3 ingest bucket. We will upload as a .zip because our function requires a few external libraries, such as Twilio Python SDK. Compress httplib2, pytz, twilio & lambda_function.py and upload as a .zip file. 
4. The Lambda function handler tells Lambda what .py module to use and corresponding method. Ex. `main_function.lambda_handler` would call the method `def lambda_handler()` inside `main_function.py`. Let's call it `lambda_function.lambda_handler` to match `lambda_function.py`. 
5. Select the role we created earlier in the housekeeping steps. 
6. In advanced settings, I recommend changing Timeout to 10 seconds (httplib2 is a bit needy). Currently, max timeout is 60 seconds. 
7. Review & create function. 

###API Gateway
1. Create a new API. Give it a name and description. This will be our RESTful endpoint. 
2. Create a resource. The path should be `/addphoto` , for example.
3. We need to add a method to this resource. Create a GET method with Lambda integration and select the function we created earlier. API Gateway isn't able to process POST requests that are URL encoded, so we are using GET as a workaround.
4. Now let's setup the Integration Request. Twilio's GET request will be of type `application-x-www-form-urlencoded`. This Integration step will map this type to a JSON object, which Lambda requires. In the Integration Requests page create a mapping template. Content-type is `application/json` and template:
```
{
    "body" : "$input.params('Body')",
    "fromNumber" :  "$input.params('From')",
    "image" : "$input.params('MediaUrl0')",
    "numMedia" : "$input.params('NumMedia')"
}
```

 More on [Intergration Requests](http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html).
 `$input.params()` parse the request object for the corresponding variable and allows the mapping template to build a JSON object. 
    [Screenshot](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/intergration.png)  
5.  Let's ensure the response is correct. Twilio requires valid XML. Change the response model for 200 to Content-type: `application/xml`. Leave models empty. 
    [Screenshot](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/response.png)  
6. Lambda cannot return proper XML, so API Gateway needs to build this. This is done in Integration response as another mapping template. This time we want to create Content-type: application/xml and template: 

```
#set($inputRoot = $input.path('$'))
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>
            $inputRoot
        </Body>
    </Message>
</Response> 
```
Our Lambda function solely returns a string of the SMS body. Here we build the XML object and use `$inputRoot` as the string.     [Screenshot](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/responseModel.png)  
7. Now let's deploy this API, so we can test it! Click the Deploy API button.

###Connecting the dots & Testing

1. We should now have a publically accessible GET endpoint. Ex: `https://xxxx.execute-api.us-west-2.amazonaws.com/prod/addphoto`
2. Point your Twilio number to this endpoint. [Screenshot](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/twilio.png)
3. Our app should now be connected. Let's review: Twilio sends a GET request with MMS image, fromNumber and body to API Gateway. API Gateway transforms the GET request into a JSON object, which is passed to a Lambda function. Lambda processes the object and writes the user to DynamoDB and writes the image to S3. Lambda returns a string which API Gateway uses to create an XML object for Twilio's response to the user. 
4. First, let's test the Lambda function. Click the Actions dropdown and Configure sample event. We need to simulate the JSON object passed by API Gateway. Example:      
```
{ 
  "body" : "hello",
  "fromNumber" : "+19145554224" ,
  "image" : "https://api.twilio.com/2010-04-01/Accounts/AC361180d5a1fc4530bdeefb7fbba22338/Messages/MM7ab00379ec67dd1391a2b13388dfd2c0/Media/ME7a70cb396964e377bab09ef6c09eda2a",
  "numMedia" : "1"
}
```
Click Test. At the bottom of the page you view Execution result and the log output in Cloudwatch logs. This is very helpful for debugging.  
    5. Testing API Gateway requires a client that sends requests to the endpoint. I personally like the Chrome Extension [Advanced Rest Client](https://chrome.google.com/webstore/detail/advanced-rest-client/hgmloofddffdnphfgcellkdfbfbjeloo?hl=en-US) Send the endpoint a GET request and view its response. Ensure the S3 link works. You can also test by sending an MMS to phone number and checking the Twilio logs.

##Troubleshooting

1. Ensure your Lambda function is using the correct IAM role. The role must have the ability to write/read to DynamoDB and S3. 
2. All Lambda interactions are logged in Cloudwatch logs. View the logs for debugging. 
3. Lambda/API Gateway Forums

##Architecture

![Architecture](https://s3-us-west-2.amazonaws.com/mauerbac-hosting/Screen+Shot+2015-09-30+at+4.00.47+PM.png)


