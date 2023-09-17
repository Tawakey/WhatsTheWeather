import httpx
import os
from pyowm.owm import OWM



def get_forecast(place_name):
    '''
        Send a http request to an API, then parse it into readable content
    '''
    owm = OWM(os.getenv("OPENWEATHER_TOKEN"))
    mgr = owm.weather_manager()
    try: 
        return mgr.forecast_at_place(place_name, "3h").forecast
    except:
        return None

if __name__ == "__main__":
    print(get_forecast("Боровичи"))
