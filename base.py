import requests
import json
import time
import datetime
import sqlite3
import ast
import hashlib


#=======MonoBank скачивание транзакций

def makeConnection(xToken ="MonobankAPIToken"):
	 #xToken Ключ доступа с личного кабинета монобанка
	connectionStatusCodes ={100:'Informational', 200: 'Connection OK', 300:'Redirection', 400:"Client error", 500:'Server error'}
	urlForAccMono = 'https://api.monobank.ua/personal/client-info'
	headers = {'content-type': 'application/json', 'X-Token': xToken}
	
	request = requests.get(urlForAccMono, headers=headers)
	statuscode=request.status_code

	if statuscode in connectionStatusCodes:
		print("Подключение к серверу monobank'а: "+ connectionStatusCodes.get(statuscode))
	else: 
		print("Подключение к серверу monobank'а: "+ str(statuscode))

	monoAccountDict=request.json()
	edate=datetime.datetime.now()#время сейчас
	eunixt=time.time()
	sunixt=int(eunixt-2629743.0)
	monoAccountDict=request.json()
	urlForTransMono = 'https://api.monobank.ua/personal/statement/'+monoAccountDict['accounts'][1]['id']+'/'+str(sunixt)
	headers = {'content-type': 'application/json', 'X-Token': xToken}
	req2=requests.get(urlForTransMono, headers=headers)

	statuscode2=req2.status_code
	if statuscode2 in connectionStatusCodes:
		print("Подключение к серверу monobank'а: "+ connectionStatusCodes.get(statuscode2))
	else: 
		print("Подключение к серверу monobank'а: "+ str(statuscode2))

	mtransList = req2.json()
	# ВСТАВИТЬ ПРОВЕРКИ НА ПУСТОЙ СПИСОК
	# if mtransList==[]:  
	# 	print("пустой список")

	#========= PrivatBank

	urlForPrivat = "https://api.privatbank.ua/p24api/rest_fiz"
	password = "PrivatBankAPIPassword"
	headers={'Content-Type': 'application/xml; charset=UTF-8'}
	merchId="PrivatBankMerchID"
	sd="10.10.2020"
	ed=datetime.date.today().strftime("%d.%m.%Y")
	head = """<?xml version="1.0" encoding="UTF-8"?><request version="1.0"><merchant><id>"""+merchId+"""</id><signature>"""

	data = f"""<oper>cmt</oper>
    	    <wait>0</wait>
        	<test>0</test>
        	<payment id="">
        	<prop name="sd" value="{sd}" />
        	<prop name="ed" value="{ed}" />
        	<prop name="card" value="5363542012827151" />
        	</payment>"""
	end_head = """</signature></merchant><data>"""

	footer = """</data></request>"""
    # === Шифрование Ключа ====================================

	signature_md5 = hashlib.md5((data+password).encode('utf-8')).hexdigest()
	signature_done = hashlib.sha1(signature_md5.encode('utf-8')).hexdigest()

	data_done = head + signature_done + end_head + data + footer
# === Запрос ==============================================
	askForTrans=requests.get(urlForPrivat,headers=headers, data=data_done)
	print("Connecting to privat: "+str(askForTrans.status_code))
	string=askForTrans.text
	print(string)
#=======форматирование ответа от привата

	#убирет хеадер 
	i=0
	while i<2:
		i=i+1
		string=string[string.find('">')+2:]
	string=string[:len(string)-39].strip().split('/>')
	del string[len(string)-1]
	ress=string
	#форматирование файла и приведение в удобный вид для создания списка с вложеным елементом словарь. в каждом словаре транзакция
	i=-1
	while i<(len(ress)-1) :
		ress[i]=ress[i].replace("=",":")
		ress[i]=ress[i].replace('" ','", ')
		ress[i]=ress[i].replace('<statement card','{"statementCard"')
		ress[i]=ress[i].replace('appcode','"appcode"')
		ress[i]=ress[i].replace('trandate','"trandate"')
		ress[i]=ress[i].replace('trantime','"trantime"')
		ress[i]=ress[i].replace(' amount','"amount"')
		ress[i]=ress[i].replace('cardamount','"cardamount"')
		ress[i]=ress[i].replace('rest','"balance"')
		ress[i]=ress[i].replace('terminal','"terminal"')
		ress[i]=ress[i].replace('description','"description"')
		ress[i]=ress[i]+"}"
		ress[i]=eval(ress[i])
		i=i+1

	# print(ress)
	# print(type(ress))
	# print(ress[10])
	# print(type(ress[10]))
	# print("")
	# print("monobank:")
	# print(mtransList)
	# print(type(mtransList))
	# print(mtransList[1])
	# print("privat")
	# print(ress)
	# print("privat")
	# print(ress[10])
	# print(type(ress[10]))
	# print("")
	# print("monobank:")
	# print(mtransList[10])
	# print(type(mtransList[10]))

#=======добавление в базу данных
#=======создание базы данных
	transDB = sqlite3.connect("transactions2.db")
	cursor=transDB.cursor()
	cursor.execute("""CREATE TABLE IF NOT EXISTS  transactions (ident INTEGER,cardNumber, transid PRIMARY KEY, transtime, description, category_mcc, amount,
	 	operationAmount, currencyCode, comissionRate,
	  cashbackAmount, balance, hold)""")
	transDB.commit()
	#mono
	for trans in mtransList:
		print(trans)
		cursor.execute('INSERT OR IGNORE INTO transactions (cardNumber, transid, transtime, description, category_mcc, amount,operationAmount, currencyCode, comissionRate, cashbackAmount, balance) VALUES (?,?,?,?,?,?,?,?,?,?,?) ', ["monobankcard5555",trans['id'], trans['time'], trans['description'], trans['mcc'], trans['amount'], trans['operationAmount'], trans['currencyCode'], trans['commissionRate'], trans['cashbackAmount'], trans['balance']] )
	transDB.commit()
	#privat
	print(ress)
	print(type(ress))
	# for trans in ress:
	# 	print(type(ress))
	# 	print(ress[0])
	# 	print(type(ress[0]))
	for trans in ress:
		#print(trans)
		#print(type(trans))
		cursor.execute('INSERT OR IGNORE INTO transactions (cardNumber, transid, transtime, description, category_mcc, amount,operationAmount, currencyCode, comissionRate, cashbackAmount, balance) VALUES (?,?,?,?,?,?,?,?,?,?,?)  ', [trans['statementCard'], trans['appcode'], trans['trantime']+trans['trandate'],trans['description'], "unknown", trans['amount'], trans['cardamount'], "UAH", "unknown comissin", "noCashback", trans['balance']] )
		transDB.commit()

	cursor.execute("SELECT * FROM transactions")
	rows = cursor.fetchall()
	for row in rows: print(row)
	transDB.close()


	
makeConnection()


