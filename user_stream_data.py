# -*- coding: utf-8 -*-
"""
Created on Thu Jan  5 17:12:49 2023

@author: 52811
"""
import os
from dotenv import load_dotenv
import threading
import requests
import websocket
import json
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from datetime import datetime
import time
import psycopg2
from psycopg2 import Error

load_dotenv()


    # Connect to an existing database
connection = psycopg2.connect(user=os.getenv("DB_USERNAME"),
                                password=os.getenv("DB_PASSWORD"),
                                host="127.0.0.1",
                                port="5432",
                                database="bot_websockets")

client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
BINANCE_FUTURES_END_POINT = "https://fapi.binance.com/fapi/v1/listenKey"


def create_futures_listen_key(api_key):
     
    response = requests.post(url=BINANCE_FUTURES_END_POINT, headers={'X-MBX-APIKEY': api_key})
    listen_key = response.json()['listenKey']
    print(listen_key)   
    x1 = threading.Thread(target=ping, args=(listen_key,api_key))        
    x1.start()
    return f"wss://fstream-auth.binance.com/ws/{listen_key}?listenKey={listen_key}"

def ping(listen_key,api_key):
    while True:
        time.sleep(1800)
        ping_response = requests.put(url=BINANCE_FUTURES_END_POINT, headers={'X-MBX-APIKEY': api_key}, params={"listenKey" : listen_key})
        # print(ping_response)
        


def exit_order(symbol,side,quantity):
    
    with connection.cursor() as cursor:
        insert_query = f""" SELECT * FROM Orders where symbol='{symbol}'"""
        cursor.execute(insert_query)
        result = cursor.fetchone()
        sl = result[3]
        tp = result[4]
        connection.commit()
    opp_side = "BUY" if side =="SELL" else "SELL"
    
    try:
        sl_order = client.futures_create_order(symbol=symbol, side=opp_side, type='STOP_MARKET', quantity=quantity, stopPrice=sl, reduceOnly=True, timeInForce="GTC")
        print(f"{datetime.now()} sending order: Stop Loss {opp_side}{quantity}{symbol} @{sl}")
    except BinanceAPIException as err:
                if str(err.message) == "Order would immediately trigger.":
                    client.futures_create_order(symbol=symbol, side=opp_side, type='MARKET', quantity=quantity, reduceOnly=True)
                    print(f"{datetime.now()}: Failed to set SL, Exiting at Market Price")

    try:
        tp_order = client.futures_create_order(symbol=symbol, side=opp_side, type='LIMIT', quantity=quantity, price=tp, reduceOnly=True, timeInForce="GTC")
        print(f"{datetime.now()} sending order: Take Profit Order {opp_side}{quantity}{symbol} @{tp}")      
    except BinanceAPIException as err:
                if str(err.message) == "Order would immediately trigger.":
                    client.futures_create_order(symbol=symbol, side=opp_side, type='MARKET', quantity=quantity, reduceOnly=True)
                    print(f"{datetime.now()}: Failed to set TP, Exiting at Market Price")

    
    return sl_order, tp_order

def on_open(ws):
    now = datetime.now()
    print(f"{now} Open: futures order stream connected")

def on_message(ws, message):
    # print(f"Message: {message}")
    now = datetime.now()
    event_dict = json.loads(message)
    # print(json.dumps(event_dict, indent=2))
    if event_dict["e"] == "ORDER_TRADE_UPDATE":  # event type
        order_status = event_dict["o"]["X"]
        if (order_status == "FILLED" and event_dict["o"]["o"] == "MARKET" and event_dict["o"]["R"] == False):  # order fill
            symbol = event_dict["o"]["s"]
            order_id = event_dict["o"]["i"]  # int
            entry_price = float(event_dict["o"]["ap"] if event_dict["o"] ["sp"] == "0" else event_dict["o"] ["sp"])
            side = event_dict["o"]["S"]  # "BUY" or "SELL"
            quantity = float(event_dict["o"]["q"])  # float as string)
            # # fee = event_dict["o"]["n"]  # float as string
            # timestamp = round(event_dict["o"]["T"]/1000,0)
            # dt_object = datetime.fromtimestamp(timestamp)
            print(f"{now}{symbol}:{side} {quantity} at {entry_price}, order id {order_id}")
            exit_order(symbol,side,quantity)
    if event_dict["e"] == "listenKeyExpired":
        ws.close()
        connect_websocket()

def on_error(ws, error):
    now = datetime.now()
    print(f"{now} Error: {error}")
    if (error == "Connection timed out"):
        ws.close()
        connect_websocket()

def on_close(ws, close_status_code, close_msg):
    now = datetime.now()
    print(f"{now} Close: {close_status_code} {close_msg}")
    ws.close()
    connect_websocket()


def connect_websocket():
    ws = websocket.WebSocketApp(url=create_futures_listen_key(os.getenv("API_KEY")),
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws.run_forever(ping_interval = 300)

if __name__ == "__main__":
    try:
        connect_websocket()
    except Exception as err:
        print(err)
        print("connect failed")
