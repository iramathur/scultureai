from http.client import HTTPException
from fastapi import APIRouter, Depends, FastAPI
from botocore.exceptions import ClientError
import boto3
import datetime
from mangum import Mangum
import cognitojwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb',region_name='eu-north-1')
table_name = "Notes"
table = dynamodb.Table(table_name)
prefix_router = APIRouter(prefix="/api/v1")


app = FastAPI()
app.include_router(prefix_router)

auth_schema = HTTPBearer()

@app.post("/login")
def authenticate_and_get_token(username: str, password: str) -> None:
    client = boto3.client('cognito-idp',region_name='eu-north-1')

    resp = client.admin_initiate_auth(
        UserPoolId="eu-north-1_7RgicS7UF",
        ClientId="4i9ao586uq4ip2s6c6mvg8u56e",
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )
 
    return{
        "Access_token":resp['AuthenticationResult']['AccessToken'],
        "ID_token:":resp['AuthenticationResult']['IdToken']
    }
    

@app.get("/notes")
async def showText(token: HTTPAuthorizationCredentials = Depends(auth_schema)):
    verified_claims: dict = cognitojwt.decode(
        token.credentials,
        'eu-north-1',
        "eu-north-1_7RgicS7UF",
        app_client_id="4i9ao586uq4ip2s6c6mvg8u56e",  # Optional
        testmode=True  # Disable token expiration check for testing purposes
    )
    userId = verified_claims["cognito:username"]
    try:
        note_entry = table.query(KeyConditionExpression=Key("UserID").eq(userId))
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return note_entry

@app.post("/createNote")
async def saveText(note: str, token: HTTPAuthorizationCredentials = Depends(auth_schema)):
    verified_claims: dict = cognitojwt.decode(
        token.credentials,
        'eu-north-1',
        "eu-north-1_7RgicS7UF",
        app_client_id="4i9ao586uq4ip2s6c6mvg8u56e",  # Optional
        testmode=True  # Disable token expiration check for testing purposes
    )
    userId = verified_claims["cognito:username"]
    note_entry = {
        "UserID": userId,
        "note" : note,
        "timestamp": str(datetime.datetime.now())
    }
    try:
        table.put_item(Item=note_entry)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# handler = Mangum(app)
