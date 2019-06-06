#!/usr/bin/env python

# cattle_druid: A Web service created to work in combination with druid,
# able to react to incoming webhooks (from druid) by downloading the new files,
# converting them to linked data, and uploading the new graphs to druid.

from flask import Flask, request, render_template, make_response, redirect, jsonify, session
import logging
import requests
from time import sleep, time

from updateWebhooks import update_webhooks
from druid_integration import druid2cattle, make_hash_folder


# The Flask app
app = Flask(__name__)

# Uploading
UPLOAD_FOLDER_BASE = '/home/cattle/storage'
ALLOWED_EXTENSIONS = set(['csv', 'json'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_BASE

# Logging
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] (%(module)s.%(funcName)s) %(message)s'
app.debug_log_format = LOG_FORMAT
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
cattlelog = logging.getLogger(__name__)


AUTH_TOKEN = "xxx"
ERROR_MAIL_ADDRESS = "xyxyxy"

# Routes

@app.route('/', methods=['GET', 'POST'])
def visit_index():
	cattlelog.info("Received request to render index")
 	return make_response(render_template('index.html'))

@app.route('/druid/<username>/<dataset>', methods=['POST'])
def druid(username, dataset):
	# Retrieves a list of Druid files in a dataset; if .csv and .json present, downloads them, converts them, uploads results
	# if only a csv is present a json will be created for it.
	cattlelog.debug("Starting Druid-based conversion")

	try:
		if request.json['assets'][0]['assetName'].endswith('.csv'):
			cattlelog.debug("Waiting for possible json-files...")
			sleep(10) #wait for possible json files to be uploaded.
	except:
		pass

	resp = make_response()

	# cattlelog.debug("UPLOAD_FOLDER=== {}".format(app.config['UPLOAD_FOLDER']))
	d2c = druid2cattle(username, dataset, cattlelog, app.config['UPLOAD_FOLDER'], requests, AUTH_TOKEN)
	candidates, singles = d2c.get_candidates()
 	#################
	try: ####UGLY FOR TESTING!!!!!!!!!!
		basename = request.json['assets'][0]['assetName'][:request.json['assets'][0]['assetName'].find(".csv")+4]
	except:
		basename = "imf.csv" 
	candidates, singles = d2c.select_candidate(candidates, singles, basename)

	if len(candidates.keys()) > 0:
		d2c.handle_pairs(candidates)
	if len(singles.keys()) > 0:
		d2c.handle_singles(singles)

	return resp, 200

@app.route('/webhook_shooter', methods=['GET', 'POST'])
def webhook_shooter():
	update_webhooks("Cattle", AUTH_TOKEN)
	cattlelog.debug("Webhook_shooter was called!")
	return render_template('webhook.html') #?make_response()?

# @app.route('/info', methods=['GET'])
# @app.route('/info/<username>/<dataset>', methods=['GET'])
# def info(username=None, dataset=None):
# 	if username == None:
# 		try:
# 			username = session['user_location']
# 			dataset='web_interface'
# 		except:
# 			cattlelog.debug("NO USERNAME WAS FOUND!!!")
# 			return render_template('info_spec.html', log_data={"no user has been specified, so there isn't any information available.": [{}]})
# 	total_log = info_log.get_combined_log(UPLOAD_FOLDER_BASE)
# 	# cattlelog.debug(json.dumps(total_log[username][dataset], indent=4))
# 	# return render_template('info.html', log_data=total_log)
# 	try:
# 		return render_template('info_spec.html', log_data=total_log[username][dataset])
# 	except:
# 		return render_template('info_spec.html', log_data={"no user has been specified, so there isn't any information available.": [{}]})

# Error handlers

@app.errorhandler(404)
def pageNotFound(error):
	return render_template('error.html', error_message="Page not found", error_mail_address=ERROR_MAIL_ADDRESS)

@app.errorhandler(500)
def pageNotFound(error):
	return render_template('error.html', error_message=error.message, error_mail_address=ERROR_MAIL_ADDRESS)

if __name__ == '__main__':
	app.run(port=8088, debug=False)
