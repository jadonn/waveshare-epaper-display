import os
import textwrap
import sys

from datetime import datetime
from datetime import timedelta
from glob import glob
from random import randrange
from PIL import Image, ImageDraw, ImageFont, ImageOps


libdir = "./lib/e-Paper/RaspberryPi_JetsonNano/python/lib"
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2 as epd7in5
from weather_providers import openweathermap

def format_weather_description(weather_description):
    if len(weather_description) < 20:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(weather_description, 20, break_long_words=False,
                           max_lines=2, placeholder='...').split('\n')
    weather_dict = {1: splits[0]}
    weather_dict[2] = splits[1] if len(splits) > 1 else ''
    return weather_dict

def getTimeQuotes(currentTime,depth):
	hour_minute = currentTime.strftime('%H%M')

	firstTry = True
	if depth > 0:
		firstTry = False

	quotes_path = 'images/metadata/quote_%s_*_credits.png' % hour_minute
	quotes = glob(quotes_path)
	if len(quotes) == 0:
		# print("No quotes for "+hour_minute)

		# Call the same request, but 1 minute ago
		return getTimeQuotes(currentTime-timedelta(minutes=1),depth+1)
	else:
		# print("Got quote for "+hour_minute)
		return quotes, firstTry


def main():

	openweathermap_apikey = os.getenv("OPENWEATHERMAP_APIKEY")
	location_lat = os.getenv("WEATHER_LATITUDE")
	location_long = os.getenv("WEATHER_LONGITUDE")

	weather_provider = openweathermap.OpenWeatherMap(
		openweathermap_apikey,
		location_lat,
		location_long,
		"imperial"
	)

	weather = weather_provider.get_weather()

	degrees = "°F"

	weather_desc = format_weather_description(weather["description"])

	output_dict = {
		'LOW_ONE': "{}{}".format(str(round(weather['temperatureMin'])), degrees),
		'HIGH_ONE': "{}{}".format(str(round(weather['temperatureMax'])), degrees),
		'ICON_ONE': weather["icon"],
		'WEATHER_DESC_1': weather_desc[1],
		'WEATHER_DESC_2': weather_desc[2]
	}


	image = Image.new(mode='1', size=(800, 480), color=255)
	iconPath = 'icons/%s.xbm' % output_dict['ICON_ONE']
	iconImage = ImageOps.invert(Image.open(iconPath).resize((64, 64)).convert('L'))
	image.paste(iconImage, (20, 5))

	now = datetime.now()

	quotes,firstTry=getTimeQuotes(now,0)

	# Write the quote to screen
	quote = quotes[randrange(0, len(quotes))]
	quoteImage = Image.open(quote).convert('1')
	image.paste(quoteImage, (0, 80))

	# If not our first try, also write the current time
	if not firstTry:
		now_time = now.strftime('%I:%M %p')
		draw_time = ImageDraw.Draw(image)
		time_font = ImageFont.truetype('Literata72pt-Regular.ttf', 30)
		draw_time.text((670, 30), now_time, font=time_font, fill=0)

	today = now.strftime('%a, %B, %d')
	dayFont = ImageFont.truetype('Literata72pt-Regular.ttf', 48)
	drawImage = ImageDraw.Draw(image)
	drawImage.text((250, 10), today, font=dayFont, fill=0)
	tempFont = ImageFont.truetype('Literata72pt-Regular.ttf', 24)
	temp = '%s / %s' % (output_dict['HIGH_ONE'], output_dict['LOW_ONE'])
	drawImage.text((100, 20), temp, font=tempFont, fill=0)
	drawImage.line([(0, 78), (800, 78)], fill=0, width=4)
	drawImage.line([(225, 0), (225, 78)], fill=0, width=4)
	return image

if __name__ == '__main__':
	image = main()
	try:
		epd = epd7in5.EPD()
		epd.init()
		if datetime.now().minute == 0 and datetime.now().hour == 2:
			epd.Clear()
		epd.display(epd.getbuffer(image))
		epd.sleep()
	
	except IOError as e:
		print(e)
	
	except KeyboardInterrupt:
		epd.sleep()