# ABOUT
This bot was made to receive webhook alerts from a private breakout strategy on tradingview. Its best feature is that it can place stop market orders for entries, and a Take Profit and Stop loss once the order is filled.

This type of bot outperforms other webhook third party bots, specially when markets have low volume since it greatly reduces slippage and latency.

Using cloud platform services like Heroku is recommended to avoid orders not being placed due to connection problems.

### HOW TO USE
1. Clone this repository or download as zip and extract it.
2. Make sure that you have installed POSTGRESQL and have a username and password.
3. Create a database and name it 'bot_websockets'
4. Use the create_table.sql query to create a table.
5. Make sure you create an API key and secret on Binance futures.
6. Create a .env file and define the following variables: WEBHOOK_PASSPHRASE, API_KEY, API_SECRET, DB_USERNAME, DB_PASSWORD.
7. Open a terminal in the root directory and execute "flask run".
8. Configure ngrok using this guide: "https://ngrok.com/docs/getting-started/"
9. Open a new terminal with and execute "ngrok http 5000" to match your flask port.
10. Open one last terminal and run "python user_stream_data.py" to start the websockets process that will listen for filled orders and place SL and TP orders.

### HOW TO USE WITH TRADINGVIEW
Read about tradingview webhooks here https://www.tradingview.com/support/solutions/43000529348-about-webhooks/#:~:text=Webhooks%20allow%20you%20to%20send,the%20body%20of%20the%20request.
1. Create a new alert with ALT+A.
2. Go to Notifications tab, and tick on WebhookUrl.
3. Write down your Ngrok domain and add "/webhook" so that your flask app can receive this request. Example: "https://ffd2-167-192-116-201.ngrok-free.app/webhook".
4. The alert content must match the example.json from this repository. 

Here is a pinescript code example to make you alert message match the example.json, make sure you have a variable for each (pair,side,price,sl,tp):

alert_messge = str.replace_all('{\n\"passphrase\": \"abcd1234\",\n\"ticker\": \"{pair}\",\n\"order_action\": \"{side}",\n\"order_price\": {price},\n\"sl\": {sl},\n\"tp\": {tp}\n}',"{pair}",pair)
    alert_messge := str.replace_all(alert_messge,"{side}",side)
    alert_messge := str.replace_all(alert_messge,"{price}",str.tostring(price))
    alert_messge := str.replace_all(alert_messge,"{sl}",str.tostring(sl))
    alert_messge := str.replace_all(alert_messge,"{tp}",str.tostring(tp))
    alert(alert_messge)
