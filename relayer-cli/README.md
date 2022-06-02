# Paradigm Relayer CLI

For creating paradigm auctions and accepting/executing quotes

## Setup

```
poetry install
poetry shell
```


## Arguments

```--i``` instruction name
```--vid``` vrfq (auction) ID
```--qid``` quote ID
```--cid``` client order ID
```--txid``` transaction ID

## Basic Usage 

1. create an auction based on given swap order id (wallet owning swap order will be hardcoded in paradigm backend)

```
python3 src/cli.py --i create --vid 12345
``` 

2. delete an auction based on ID

```
python3 src/cli.py --i delete --vid 12345
``` 


3. choose a quote for given auction ID and quote ID

```
python3 src/cli.py --i choosequote --vid 12345 --qid 2 --cid 1111
``` 


3. set trade transaction as succeeded

```
python3 src/cli.py --i setComplete --vid 12345 --txid 26UFc7ENqbAtKKaqkvbyWxJ4dRRMGwTwXwjwQHHyPL8MzubbbLgFYNhmr3K2yhqznf9aJskArLtqnd9WYrXacvxM
``` 

4. print out details about a given auction (based on ID)

```
python3 src/cli.py --i print --vid 12345
``` 

5. print out live quotes for a given auction

```
python3 src/cli.py --i printQuotes --vid 12345
``` 





