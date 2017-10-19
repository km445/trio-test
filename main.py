import jinja2, os, urllib.request, urllib.parse, json, hashlib, config, datetime
from collections import OrderedDict
from flask import Flask, redirect, render_template, request
app = Flask(__name__)

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
	data={"shop_id":config.shop_id, "shop_invoice_id":config.shop_invoice_id}
	if request.method == "POST":
		currency=request.form["currency"]
		amount=request.form["amount"]
		description=request.form["description"]
		try:
			if float(amount)<0.01:
				return render_template("main.html", 
					error="Сумма должна быть более или равна 0.01", log=log)
			else:
				amount="%.2f" % float(amount)
		except:
			return render_template("main.html", 
				error="Указана неправильная сумма оплаты.", log=log)
		
		#case for currency USD
		if currency == "USD":
			url=config.url_tip
			data["currency"]="840"
			data["amount"]=amount
			
			data["sign"]=generateHash(data)
			log.append((config.shop_invoice_id, 
						amount, 
						currency, 
						description, 
						datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			config.shop_invoice_id+=1
			return render_template("form.html", 
									url=url, 
									parameters=data, 
									form_method="POST")
		
		#case for currency EUR	
		elif currency == "EUR":
			url=config.url_invoice
			data["currency"]="978"
			data["amount"]=amount
			data["payway"]="payeer_eur"
			data["sign"]=generateHash(data)
			data=json.dumps(data).encode("utf-8")
			api_invoice_request=urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
			api_incoive_response=urllib.request.urlopen(api_invoice_request).read().decode("utf-8")
			log.append((config.shop_invoice_id, 
						amount, 
						currency, 
						description, 
						datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			config.shop_invoice_id+=1
			payment_request_form=json.loads(api_incoive_response)
			
			return render_template("form.html", 
					url=payment_request_form["data"]["source"], 
					parameters=payment_request_form["data"]["data"], 
					form_method=payment_request_form["data"]["method"])
			
	elif request.method == "GET":
		return render_template("main.html", log=log)

if __name__=="__main__":
	app.run(host="0.0.0.0", debug = False)