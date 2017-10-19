import jinja2, os, urllib.request, urllib.parse, json, hashlib, config, datetime
from collections import OrderedDict
from flask import Flask, redirect, render_template, request
app = Flask(__name__)

port=int(os.environ.get('PORT',5000))

def generateHash(parameters):
	'''
	Generates sign hash using mandatory request parameters and password.
	'''
	ordered_parameters=OrderedDict(sorted(parameters.items()))
	hash_string=":".join([str(e) for e in ordered_parameters.values()]) + config.password	
	hash=hashlib.md5(hash_string.encode("utf-8")).hexdigest()
	return hash
	
log=[]
				
@app.route("/", methods = ["GET", "POST"])
def index():
	data={"shop_id":config.shop_id}
	if request.method == "GET":
		return render_template("main.html", log=log)
	
	elif request.method == "POST":		
		currency = request.form["currency"]
		amount = request.form["amount"]
		description = request.form["description"]
		try:
			if float(amount)<0.01:
				return render_template("main.html", 
						error="Сумма оплаты должна быть более или равна 0.01", log=log)
			else:
				amount="%.2f" % float(amount)
		except:
			return render_template("main.html", 
					error="Указана неправильная сумма оплаты.", log=log)
		config.shop_invoice_id+=1
		data.update({"shop_invoice_id":config.shop_invoice_id})
		data.update({"amount":amount})
		#case for currency USD
		if currency == "USD":
			data.update({"currency":"840"})
			data["sign"]=generateHash(data)
			log.append((config.shop_invoice_id, 
						amount, 
						currency, 
						description, 
						datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			
			return render_template("form.html", 
									url=config.url_tip, 
									parameters=data, 
									form_method="POST")
		
		#case for currency EUR	
		elif currency == "EUR":
			data.update({"currency":"978", "payway":"payeer_eur"})
			data["sign"]=generateHash(data)
			data=json.dumps(data).encode("utf-8")
			api_invoice_request=urllib.request.Request(config.url_invoice, data=data, headers={"Content-Type":"application/json"})
			api_incoive_response=urllib.request.urlopen(api_invoice_request).read().decode("utf-8")
			log.append((config.shop_invoice_id, 
						amount, 
						currency, 
						description, 
						datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

			payment_request_form=json.loads(api_incoive_response)
			
			return render_template("form.html", 
					url=payment_request_form["data"]["source"], 
					parameters=payment_request_form["data"]["data"], 
					form_method=payment_request_form["data"]["method"])

if __name__=="__main__":
	app.run(host="0.0.0.0", port=port, debug = False)