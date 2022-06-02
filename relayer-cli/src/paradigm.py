import http.client
import time
from typing import Union
API_URL = "https://api.stage.paradigm.co/"


def _do_paradigm_request(method: str, url: str, payload=None, headers={}):
    headers['paradigm-api-timestamp'] = int(time.time())
    headers['cache-control'] = 'no-cache'

    conn = http.client.HTTPSConnection(API_URL)

    conn.request(method, "//v1/vrfq/rfqs/" + url, body=payload, headers=headers)

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
    {\n  
        \"venue\": \"FRK\",\n
        \"domain\": 
            {\n    
                \"contract_name\":  \"FRIKTION SWAP\",\n
                \"version\": \"1\",\n
                \"chain_id\": -1,\n
                \"verifying_contract\": \"SwpWEbAhitpix22gbX28zah7g8JiA1FRwVdPe4XohQb\"\n  
            },\n  
        \"swap_id\": %d\n
    }\n
    """ % swap_id

    headers = {
        # what is this?
        'paradigm-api-signature': "{{requestSignature}}",
    }

    return _do_paradigm_request('POST', '', payload, headers)

# delete vrfq endpoint
def delete_vrfq(vrfq_id: int):
    headers = {
        'paradigm-api-signature': "{{requestSignature}}",
    }

    return _do_paradigm_request('DELETE','%d' % vrfq_id, headers=headers)


# list vrfq endpoint
def get_vrfqs(vrfq_id: int):
    headers = {
        'paradigm-api-signature': "{{requestSignature}}",
    }

    return _do_paradigm_request('GET','%d' % vrfq_id, headers=headers)


# list vrfq endpoint
def get_vrfqs_with_quotes(vrfq_id: int):
    headers = {
        'paradigm-api-signature': "{{requestSignature}}",
    }

    return _do_paradigm_request('GET', '%d/quotes' % vrfq_id, headers=headers)

# create order for quote endpoint
# NOTE: paradigm "order" terminology refers to the action of a taker hitting a given quote from the makers
def create_order_for_quote(vrfq_id: int, quote_id: int,  client_order_id: str = None):
    payload = """
        {\n  
            %s
            \"quote_id\": %d\n
        }\n
    """ % (("\"client_order_id\": \"%s\"," % client_order_id) if client_order_id is not None else "", quote_id)

    headers = {
        'paradigm-api-signature': "{{requestSignature}}",
    }

    return _do_paradigm_request('POST','%d/orders' % vrfq_id, payload, headers=headers)

# get "trade_id" from the "id" field returned in the response of POST on rfqs/{id}/orders/
def set_tx_successful(trade_id: int, tx_id: str):
    payload = """
        {\n  
            \"status\": \"COMPLETED\",\n  
            \"transaction_id\": \"%s\"\n
        }"
    """ % tx_id

    return _do_paradigm_request('PATCH','trades/%d' % trade_id, payload)

# get "trade_id" from the "id" field returned in the response of POST on rfqs/{id}/orders/
def set_tx_successful(trade_id: int, tx_id: str, error_msg: str):
    payload = """
        {\n  
            \"status\": \"REJECTED\",\n
            \"error\": \"%s\",\n  
            \"transaction_id\": \"%s\"\n
        }"
    """ % (error_msg, tx_id)

    return _do_paradigm_request('PUT','trades/%d' % trade_id, payload)

