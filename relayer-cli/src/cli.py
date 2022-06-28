from argparse import ArgumentParser
import sqlite3
from xml.dom.minidom import Document
from tinydb import TinyDB, Query
from paradigm import *
import json

def get_new_client_order_id(db: TinyDB):
    order = Query()
    all_orders = db.search(order.type == 'order')
    most_recent_order = max(all_orders, key = int(all_orders['client_order_id']))
    return int(most_recent_order['client_order_id'])

def get_vrfq_from_db(db: TinyDB, vid: int) -> Document:
    vrfq = Query()
    auction_deets = db.search(
        vrfq.id == vid and vrfq.type == "vrfq"
    )[0]
    return auction_deets

def main():

    db = TinyDB('./relayer-db.json')

    parser = ArgumentParser(prog='cli')
    parser.add_argument("--i", help="instruction to run (aka http request to paradigm api", type=str)
    parser.add_argument('--vid', help="id of vrfq", type=int)
    parser.add_argument('--sid', help="id of swap in simple-swap program", type=int)
    parser.add_argument('--qid', help="id of quote provided by paradigm maker", type=int)
    parser.add_argument('--txid', help="transaction id of failed or succesful transaction", type=str)
    parser.add_argument('--errormsg', help="error messsage to descrbie failure", type=str)

    args = parser.parse_args()

    i = args.i

    if i == "create":
        response = create_vrfq(
            args.sid
        )
        print(response)
        db.insert(
            {
                **json.loads(response)
                **{
                    'type': 'vfrq'
                }
            }
        )
    elif i == 'delete':
        response = delete_vrfq(
            args.sid
        )
        print(response)
        vrfq = Query()
        db.remove(
            vrfq.id == args.vid
        )
    elif i == "choosequote":
        auction_deets = get_vrfq_from_db(db, args.vid)
        quotes_for_auction = json.loads(get_vrfqs_with_quotes(args.vid))
        
        # TODO: some logic confirming the quote id exists in valid quotes for the auction
        response = create_order_for_quote(
            args.vid,
            args.qid,
            get_new_client_order_id(db)
        )
        db.insert(
            {
                **json.loads(response)
                **{
                    'type': 'order'
                }
            } 
        )
        print(response)
    elif i == 'list':
        all_user_vrfqs = get_vrfqs()
        print('all vrfqs: ', all_user_vrfqs)
    elif i == 'print':
        auction_deets = get_vrfq_from_db(db, args.vid)
        auction_newest = get_vrfq(args.vid)
        print(auction_deets)
        print(auction_newest)
    elif i == 'printQuotes':
        auction_deets = get_vrfq_from_db(db, args.vid)
        print('AUCTION\n--------')
        print(auction_deets)
        quotes_for_auction = json.loads(get_vrfqs_with_quotes(args.vid))
        print('QUOTES\n--------')
        print(quotes_for_auction)
    elif i == 'setComplete':
        Order = Query()
        order = db.search(
            Order.type == 'order' and Order.rfq_id == args.vid   
        )[0]
        # set "order" transaction as executed
        print(set_tx_successful(order.id, args.txid))
    elif i == 'setFailed':
        # set "order" transaction as rejected
        print(set_tx_rejected(order.id, args.txid, args.errormsg))

  



if __name__ == '__main__':
    main()