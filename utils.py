def entry_order(side, quantity,symbol,price, opp_side, tp,sl):
    if float(client.futures_position_information(symbol=symbol)[0]['positionAmt']) == 0.0:
        client.futures_cancel_all_open_orders(symbol=symbol)
        
    try:    
        print(f"sending order: Stop Market Order {side}{quantity}{symbol} @{price}")
        order = client.futures_create_order(symbol=symbol, side=side, type='STOP_MARKET', quantity=quantity, stopPrice=price)
        time.sleep(0.5)        
        order_executed = False
        while order_executed == False:
            if float(client.futures_position_information(symbol=symbol)[0]['positionAmt']) != 0.0:            
                try:
                    print(f"sending order: Take Profit Order {opp_side}{quantity}{symbol} @{tp}")
                    tp_order = client.futures_create_order(symbol=symbol, side=opp_side, type='LIMIT', quantity=quantity, price=tp, reduceOnly=True, timeInForce="GTC")
                    print(f"sending order: Stop Loss {opp_side}{quantity}{symbol} @{sl}")
                    sl_order = client.futures_create_order(symbol=symbol, side=opp_side, type='STOP_MARKET', quantity=quantity, stopPrice=sl, reduceOnly=True, timeInForce="GTC")
                except BinanceAPIException as err:
                    if str(err.message) == "Order would immediately trigger.":
                        print(f"Exiting trade at Market Price")
                        client.futures_create_order(symbol=symbol, side=opp_side, type='MARKET', quantity=quantity, reduceOnly=True)
                        client.futures_cancel_all_open_orders(symbol=symbol)
                    return False
                order_executed = True
                break
            else:
                order_executed = False
    except BinanceAPIException as e:
        
        # print("an exception occured - {}".format(e))    
        if not client.futures_get_open_orders(symbol=symbol) and float(client.futures_position_information(symbol=symbol)[0]['positionAmt']) == 0.0 and str(e.message) == "Order would immediately trigger.":                        
            print("sending order at market price")
            order = client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=quantity)
            time.sleep(0.5)
            try:
                print(f"sending order: Take Profit Order {opp_side}{quantity}{symbol} @{tp}")
                tp_order = client.futures_create_order(symbol=symbol, side=opp_side, type='LIMIT', quantity=quantity, price=tp, reduceOnly=True, timeInForce="GTC")
                print(f"sending order: Stop Loss {opp_side}{quantity}{symbol} @{sl}")
                sl_order = client.futures_create_order(symbol=symbol, side=opp_side, type='STOP_MARKET', quantity=quantity, stopPrice=sl, reduceOnly=True, timeInForce="GTC")
            except BinanceAPIException as err:
                if str(err.message) == "Order would immediately trigger.":
                    print(f"Exiting trade at Market Price")
                    client.futures_create_order(symbol=symbol, side=opp_side, type='MARKET', quantity=quantity, reduceOnly=True)
                    client.futures_cancel_all_open_orders(symbol=symbol)
                return False
                

        
    return order,tp_order,sl_order