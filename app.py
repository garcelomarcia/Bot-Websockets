import json
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import pandas as pd
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


app = Flask(__name__)

#List the symbols that you whish to trade here
symbols_list = ["BTCUSDT", "ETHUSDT"]

client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))

#We need to create a dictionary conatining the Price Decimals and Order Decimals to calculate positions sizes later
table = {}
exchange_info = client.futures_exchange_info().get('symbols')

for key in exchange_info:
    if key["symbol"] in symbols_list:
        table[key["symbol"]] = {}
        table[key["symbol"]]['Price Decimals'] = int(len(key['filters'][0]['tickSize'])-3)
        if int(len(key['filters'][1]['stepSize'])) >=3:
            table[key["symbol"]]['Order Decimals'] = int(len(key['filters'][1]['stepSize'])-2)
        else:
            table[key["symbol"]]['Order Decimals'] = 0

#We define our entry order here
def entry_order(side, quantity,symbol,price):
    if float(client.futures_position_information(symbol=symbol)[0]['positionAmt']) == 0.0:
        client.futures_cancel_all_open_orders(symbol=symbol)        
        try:    
            order = client.futures_create_order(symbol=symbol, side=side, type='STOP_MARKET', quantity=quantity, stopPrice=price)
            print(f"sending order: Stop Market Order {side}{quantity}{symbol} @{price}")

        except BinanceAPIException as err:
                if str(err.message) == "Order would immediately trigger.":
                    order = client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=quantity)
                    print(f"{side}ing {quantity}{symbol} @ Market Price")
        print(f"order id: {order['orderId']}")
    else:
        order = None
    return order

#This endpoint receives the JSON with all the corresponding info for the trade
@app.route("/webhook", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    if data['passphrase'] != os.getenv("WEBHOOK_PASSPHRASE"):
        return {
            "code": "error",
            "message": "Invalid passhprase"
        }
    symbol = data['ticker'].upper()
    #If there are any unfilled orders, we cancel them
    if client.futures_get_open_orders(symbol=symbol) and client.futures_get_open_orders(symbol=symbol)[0]['reduceOnly'] == "False":
        print("Cancelling previous order")
        client.futures_cancel_all_open_orders(symbol=symbol)
    acc_balance = client.futures_account_balance()
    for check_balance in acc_balance:
        if check_balance["asset"] == "USDT":
            usdt_balance = float(check_balance["balance"])    
    quantity_round = table[f"{symbol}"]['Order Decimals']
    side = data['order_action'].upper()
    
    #************* Rank is defined as how many times our account balance would be put to each order, Adjust levels accordingly*******
    rank = float(7.5) if symbol == "ETHUSDT" else float(13)
    price = float(data['order_price'])
    quantity = round((usdt_balance*rank)/price,quantity_round)
    sl = float(data['sl'])
    tp = float(data['tp'])
    #We update our database for the particular traded symbol to include the last sl and takeprofit info
    with connection.cursor() as cursor:
        update_query = f""" UPDATE Orders 
        SET side='{side}', price={price}, sl={sl}, tp ={tp}
        WHERE symbol='{symbol}'"""
        cursor.execute(update_query)
        connection.commit()
    #We call our entry_order function to create our order
    new_order = entry_order(side, quantity,symbol,price)

    if new_order:
        return {
            "code": "success",
            "message": "stop order created"
        }
    else:
        
        return {
            "code": "error",
            "message": "stop order failed"
        }
    
   
        
        
@app.route("/")
def hello_world():
    with connection.cursor() as cursor:
        orders_query = """ SELECT * FROM Orders;"""
        cursor.execute(orders_query)
        last_orders = cursor.fetchall()
        connection.commit()

    return f"<p>{last_orders}</p>"


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
    
