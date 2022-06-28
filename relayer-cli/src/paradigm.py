import http.client
import time
from typing import Union
import json
import hmac
import hashlib
import base64

# API_URL = "https://api.stage.paradigm.co/"
API_URL = "api.test.paradigm.co"
API_KEY_DATA = json.load(open('./.api-key.txt','r'))
ACCESS_KEY = API_KEY_DATA['accessKey']
SECRET_KEY = API_KEY_DATA['secretKey']
BASE_VRFQ_URL =  "/v1/vrfq/rfqs/"

def generate_signature(timestamp: int, method: str, url: str, body: str, secret_key: str):
    print([str(timestamp), method.upper(), url, body])
    buffer = '\n'.join([str(timestamp), method.upper(), url, body])
    print(buffer)
    print(secret_key)
    print(base64.b64decode(secret_key))
    hmac_code = hmac.new(base64.b64decode(secret_key), bytes(buffer, 'UTF-8'), hashlib.sha256)
    return base64.b64encode(hmac_code.digest())

def _do_paradigm_request(method: str, url: str, payload='', headers={}):
    timestamp = int(time.time() * 1000)
    additional_url = BASE_VRFQ_URL + url
    full_url = API_URL + additional_url

    headers['Paradigm-API-Timestamp'] = timestamp 
    headers['cache-control'] = 'no-cache'
    headers['Paradigm-API-Signature'] = generate_signature(timestamp, method.upper(), additional_url, str(payload or ''), SECRET_KEY)
    headers['Authorization'] = 'Bearer %s' % ACCESS_KEY
    headers['Content-Type'] = 'application/json'

    print('signature = ',  headers['Paradigm-API-Signature'])
    print('hitting url = \'%s\'' % full_url)
    print('headers = ', headers)
    conn = http.client.HTTPSConnection(API_URL)
    conn.request(method, additional_url, headers=headers, body=payload.encode('UTF-8'))
    res = conn.getresponse()
    data = res.read()
    
    return data.decode("utf-8")

# create vrfq endpoint
def create_vrfq(swap_id: int):
    # TODO: specify what chain_id should be. might be an artifact of evm chains?
    # NOTE: verifying_contract address different than 0x... format of evm chains.
    # TODO: is "venue" field required as shown in api docs? also do we make it FRK? was set to RBN before
    # swap_id: id of swap order created in friktion swap contract
    payload = """
    {
        "venue": "FRK",\n
        "domain": 
            {\n    
                "contract_name":  "FRIKTION SWAP",\n
                "version": "1",\n
                "chain_id": -1,\n
                "verifying_contract": "SwpWEbAhitpix22gbX28zah7g8JiA1FRwVdPe4XohQb"\n  
            },\n  
        "swap_id": %d\n
    }
    """ % swap_id

    print(payload)


    return _do_paradigm_request('POST', '', payload)

# delete vrfq endpoint
def delete_vrfq(vrfq_id: int):

    return _do_paradigm_request('DELETE','%d' % vrfq_id)


# list single vrfq by id endpoint
def get_vrfq(vrfq_id: int):

    return _do_paradigm_request('GET','%d' % vrfq_id)

# list all vrfqs
def get_vrfqs():
    return _do_paradigm_request('GET','')


# list vrfq endpoint
def get_vrfqs_with_quotes(vrfq_id: int):

    return _do_paradigm_request('GET', '%d/quotes' % vrfq_id)

# create order for quote endpoint
# NOTE: paradigm "order" terminology refers to the action of a taker hitting a given quote from the makers
def create_order_for_quote(vrfq_id: int, quote_id: int,  client_order_id: str = None):
    payload = """
        {\n  
            %s
            "quote_id": %d\n
        }\n
    """ % (("\"client_order_id\": %s" % client_order_id) if client_order_id is not None else "", quote_id)


    return _do_paradigm_request('POST','%d/orders' % vrfq_id, payload)

# get "trade_id" from the "id" field returned in the response of POST on rfqs/{id}/orders/
def set_tx_successful(trade_id: int, tx_id: str):
    payload = """
        {\n  
            "status": "COMPLETED",\n  
            "transaction_id": "%s"\n
        }"
    """ % tx_id

    return _do_paradigm_request('PATCH','trades/%d' % trade_id, payload)

# get "trade_id" from the "id" field returned in the response of POST on rfqs/{id}/orders/
def set_tx_rejected(trade_id: int, tx_id: str, error_msg: str):
    payload = """
        {\n  
            "status": "REJECTED",\n
            "error": "%s",\n  
            "transaction_id": "%s"\n
        }"
    """ % (error_msg, tx_id)

    return _do_paradigm_request('PUT','trades/%d' % trade_id, payload)

