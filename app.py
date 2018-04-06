import sys, json, requests
from flask import Flask, request
import pyowm
import apiai


app = Flask(__name__)

FB_ACCESS_TOKEN = 'EAAWdZBwuv89kBADQazYyfdP0t8SzEzFT66A7GDtUcuks9nkmXUEhd5Yko3X1Xy0sP7ZB4udRPm0a5TF2Lsga26Roq1iipmPz1vOPu7V31oRXWDAHjzUeK4s8fF7UJHstD8IdgTiLNDUvhIBMPeMovKB8W0wCu9fZCuJ5q0UdQZDZD'

CLIENT_ACCESS_TOKEN = '4e3744e00ef548fb81c465eeeb9b0d4b'

VERIFY_TOKEN = 'weather'

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)


HELP_MSG = """
Hey! I am Weatherbot. 
I can provide you with weather in your region or anywhere in the world! I'm here to tell you when you got to take your umbrella out with you! :)
"""

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "hello", 200


@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]        
                recipient_id = messaging_event["recipient"]["id"] 
                if messaging_event.get("message"):  

                     
                    message_text = messaging_event["message"]["text"]  
                    query=  messaging_event['message']['text']
                    send_message_response(sender_id, parse_user_message(message_text)) 

                    if query =="button":
                        buttons =[{"type":"web url",
                                    "url":'https://openweathermap.org/',
                                    "title": "search for weather"
                                    }]

                        send_message_response(sender_id, "check out this link", buttons)

                       

                elif messaging_event.get('postback'):
                    
                    payload = messaging_event['postback']['payload']
                    if payload ==  'SHOW_HELP':
                        send_message_response(sender_id, HELP_MSG)
                
    return "ok", 200


def send_message(sender_id, message_text):
   
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",

        params={"access_token": FB_ACCESS_TOKEN},

        headers={"Content-Type": "application/json"}, 

        data=json.dumps({
        "recipient": {"id": sender_id},
        "message": {"text": message_text}
    }))



def parse_user_message(user_text):
   
    request = ai.text_request()
    request.query = user_text

    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']
    if (responseStatus == 200):

        print("API AI response", response['result']['fulfillment']['speech'])
        try:
            
            weather_report = ''

            input_city = response['result']['parameters']['geo-city']
            print("City ", input_city)

            owm = pyowm.OWM('bd5e378503939ddaee76f12ad7a97608') 

            forecast = owm.daily_forecast(input_city)

            observation = owm.weather_at_place(input_city)
            w = observation.get_weather()
            print(w)                      
            print(w.get_wind())                 
            print(w.get_humidity())      
            max_temp = str(w.get_temperature('celsius')['temp_max'])  
            min_temp = str(w.get_temperature('celsius')['temp_min'])
            current_temp = str(w.get_temperature('celsius')['temp'])
            wind_speed = str(w.get_wind()['speed'])
            humidity = str(w.get_humidity())

            weather_report = ' max temp: ' + max_temp + ' min temp: ' + min_temp + ' current temp: ' + current_temp + ' wind speed :' + wind_speed + ' humidity ' + humidity + '%'
            print("Weather report ", weather_report)

            return (response['result']['fulfillment']['speech'] + weather_report)
        except:
            return (response['result']['fulfillment']['speech'])

    else:
        return ("Sorry, I couldn't understand that question")


def send_message_response(sender_id, message_text):

    sentenceDelimiter = ". "
    messages = message_text.split(sentenceDelimiter)
    
    for message in messages:
        send_message(sender_id, message)

def set_greeting_text():
    headers = {
        'Content-Type':'application/json'
        }
    data = {
        "setting_type":"greeting",
        "greeting":{
                "text":"Hi {{user_first_name}}! I am a weather bot!"

            }
        }
    ENDPOINT = "https://graph.facebook.com/v2.8/me/thread_settings?access_token=%s"%(FB_ACCESS_TOKEN)
    r = requests.post(ENDPOINT, headers = headers, data = json.dumps(data))
    print(r.content)


def set_persistent_menu():
    headers = {
        'Content-Type':'application/json'
        }
    data = {
        "setting_type":"call_to_actions",
        "thread_state" : "existing_thread",
        "call_to_actions":[
            {
                "type":"web_url",
                "title":"search for weather!",
                "url":"https://openweathermap.org/" 
            },
            {
                "type":"postback",
                "title":"Help",
                "payload":"SHOW_HELP"
            }]
        }
    ENDPOINT = "https://graph.facebook.com/v2.8/me/thread_settings?access_token=%s"%(FB_ACCESS_TOKEN)
    r = requests.post(ENDPOINT, headers = headers, data = json.dumps(data))
    print(r.content)

set_persistent_menu()
set_greeting_text() 


if __name__ == '__main__':
    app.run()