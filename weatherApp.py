import json
import csv
import requests
import pymongo
from pymongo import MongoClient
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from wordcloud import WordCloud, STOPWORDS
from flask import Flask, flash, redirect, render_template, request, session, abort,send_file,redirect, url_for,make_response
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64
from matplotlib import style




dbclient = pymongo.MongoClient('mongodb://localhost:27017/')

db = dbclient['big_data']
col = db["met"]

col.drop()

col = db["met"]





app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("home.html")


@app.route("/",methods=["POST"]) 
def form():
     global station
     global date
     global inp
     global stdt
     station = request.form.get("Station")
     date = request.form.get("Date")
     station = station.upper()
     refine = "&refine.nom=" + station
     time= "&refine.date="+date
     read = requests.get('https://public.opendatasoft.com/api/records/1.0/search/?dataset=donnees-synop-essentielles-omm&q=&sort=date&facet=date&facet=nom&facet=temps_present&facet=libgeo&facet=nom_epci&facet=nom_dept&facet=nom_reg'+refine+time)
     data = read.json()
     try:
        filt = data["records"]
     except KeyError:
        filt = 0
    
     if filt==0:
         error = "la station et la date sont obligatoires"  
         return render_template("home.html",msg=error)
     else:   
        with open("met.json", 'w') as f:
             json.dump(filt,f, indent = 4, sort_keys=False)
        with open('met.json') as fil:
            file_data = json.load(fil) 
            try:
                col.insert_many(file_data) 
            except TypeError:
                error = "station ou date n’existe pas"
                return render_template("home.html",msg=error)
     os.remove('met.json')
     stdt=(station,date)
     inp= col.find({"fields.nom": station, "fields.date": {'$regex': date}}).sort("fields.date")
     return render_template('weather.html', Kh=inp,H=stdt)
            
 
 
@app.route("/weather",methods=["POST"]) 
def form2():
     global station
     global date
     global inp
     global stdt
     station = request.form.get("Station2")
     station = station.upper()
     date = request.form.get("Date2")
     refine = "&refine.nom=" + station
     time= "&refine.date="+date
     read = requests.get('https://public.opendatasoft.com/api/records/1.0/search/?dataset=donnees-synop-essentielles-omm&q=&sort=date&facet=date&facet=nom&facet=temps_present&facet=libgeo&facet=nom_epci&facet=nom_dept&facet=nom_reg'+refine+time)
     data = read.json()
     try:
        filt = data["records"]
     except KeyError:
        filt = 0
    
     if filt==0:
         error = "la station et la date sont obligatoires" 
         errorsd="--------" 
         return render_template("weather.html",msg=error,H=errorsd)
     else:
        col = db["met"]
        col.drop()
        col = db["met"]
        with open("met.json", 'w') as f:
            json.dump(filt,f, indent = 4, sort_keys=False)
        
        with open('met.json') as fil:
            file_data = json.load(fil) 
            try:
                col.insert_many(file_data) 
            except TypeError:
                error = "station ou date n’existe pas"
                errorsd="--------"
                return render_template("weather.html",msg=error,H=errorsd)
     os.remove('met.json')
     stdt=(station,date)
     inp= col.find({"fields.nom": station, "fields.date": {'$regex': date}}).sort("fields.date")
     return render_template('weather.html', Kh=inp,H=stdt)





@app.route("/download")
def download():
    global data
    try:
        data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    except KeyError:
        data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    try:
         data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    except KeyError:
        data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.ff":1}).sort("fields.date")
    try:
         data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    except KeyError:
        data=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
                  {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1}).sort("fields.date")
            
    path="./data"
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation %s failed" % path)
    else:
        print ("Successfully created  %s " % path)
    with open(path+"/data.json", 'w') as f:
        for doc in data:
          json.dump(doc, f, indent = 4, sort_keys=False)
    p= "./data/data.json"
    return send_file(p, as_attachment=True)

            
    
    

   
@app.route('/plot_t')
def plot_t():
    f=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
            {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hour", "Temperature","Humidité(%)","Vit vent moy10min avt (m/s)"])
        for doc in f:
            dat=doc["fields"]["date"]
            try:
                temp = round(doc["fields"]["tc"])
            except KeyError:
                temp = 0
            try:
                hum=doc["fields"]["u"]
            except KeyError:
                hum=0
            try:
                vit=doc["fields"]["ff"]
            except KeyError:
                vit=0
            writer.writerow([dat[11:16],temp,hum,vit])
    table = pd.read_csv("data.csv", encoding="latin-1")
    file = open("data.csv")
    reader = csv.reader(file)
    lines= len(list(reader))
    plt.style.use('fivethirtyeight')
    plt.figure(figsize=(10,5))
    plt.bar(x=np.arange(1,lines),height=table['Temperature'])
    table.head()
    img = BytesIO()
    plt.xticks(np.arange(1,lines), table['Hour'], rotation='horizontal', fontsize=10)
    plt.yticks(rotation='vertical', fontsize=10)
    plt.ylabel("Temperatures")
    plt.savefig(img, format='png',edgecolor='none')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('plot_t.html', plot_url=plot_url,H=stdt)
    


@app.route('/plot_h')
def plot_h():
    f=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
            {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hour", "Temperature","Humidité(%)","Vit vent moy10min avt (m/s)"])
        for doc in f:
            dat=doc["fields"]["date"]
            try:
                temp = round(doc["fields"]["tc"])
            except KeyError:
                temp = 0
            try:
                hum=doc["fields"]["u"]
            except KeyError:
                hum=0
            try:
                vit=doc["fields"]["ff"]
            except KeyError:
                vit=0
            writer.writerow([dat[11:16],temp,hum,vit])
    table = pd.read_csv("data.csv", encoding="latin-1")
    file = open("data.csv")
    reader = csv.reader(file)
    lines= len(list(reader))
    plt.style.use('fivethirtyeight')
    plt.figure(figsize=(10,5))
    plt.bar(x=np.arange(1,lines),height=table['Humidité(%)'])
    table.head()
    img = BytesIO()
    plt.xticks(np.arange(1,lines), table['Hour'], rotation='horizontal', fontsize=10)
    plt.yticks(rotation='vertical', fontsize=10)
    plt.ylabel("Humidité")
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('plot_t.html', plot_url=plot_url,H=stdt)



@app.route('/plot_v')
def plot_v():
    f=col.find({"fields.nom": station, "fields.date": {'$regex': date}},
            {"_id":0,"fields.nom":1,"fields.date":1,"fields.tc":1,"fields.u":1,"fields.ff":1}).sort("fields.date")
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hour", "Temperature","Humidité(%)","Vit vent moy10min avt (m/s)"])
        for doc in f:
            dat=doc["fields"]["date"]
            try:
                temp = round(doc["fields"]["tc"])
            except KeyError:
                temp = 0
            try:
                hum=doc["fields"]["u"]
            except KeyError:
                hum=0
            try:
                vit=doc["fields"]["ff"]
            except KeyError:
                vit=0
            writer.writerow([dat[11:16],temp,hum,vit])
    table = pd.read_csv("data.csv", encoding="latin-1")
    file = open("data.csv")
    reader = csv.reader(file)
    lines= len(list(reader))
    plt.style.use('fivethirtyeight')
    plt.figure(figsize=(10,5))
    plt.bar(x=np.arange(1,lines),height=table['Vit vent moy10min avt (m/s)'])
    table.head()
    img = BytesIO()
    plt.xticks(np.arange(1,lines), table['Hour'], rotation='horizontal', fontsize=10)
    plt.yticks(rotation='vertical', fontsize=10)
    plt.ylabel("Vit vent")
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('plot_t.html', plot_url=plot_url,H=stdt)




if __name__ == "__main__":
	app.run()
 