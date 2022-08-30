# -*- coding: utf-8 -*-
"""
Created on Fri May 27 13:09:12 2022

Get MLB The Show 22 Listing Data for Flips

@author: Robby
"""

#%% Import packages
import pandas as pd
import numpy as np
import time
import json
import requests
import datetime as dt

#%% Read in listings
import concurrent.futures
import requests
import time

types_pages = {}
out = []
CONNECTIONS = 1000
TIMEOUT = 5

types = ['mlb_card','stadium','equipment','unlockable','sponsorship']

for t in types:   
    url = requests.get(f"https://mlb22.theshow.com/apis/listings.json?type={t}")
    text = url.text
    data = json.loads(text)
    types_pages[t] = list(range(1,data['total_pages']+1))

urls = []
for t in types:
    for n in types_pages[t]:
        urls.append(f"https://mlb22.theshow.com/apis/listings.json?type={t}&page={n}")

def load_url(url, timeout):
    ans = requests.get(url, timeout=timeout)
    return ans.text

with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
    future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in urls)
    for future in concurrent.futures.as_completed(future_to_url):
        try:
            data = future.result()
            data = json.loads(data)['listings']
        except Exception as exc:
            data = str(type(exc))
        finally:    
            out.append(data)

import itertools
l = list(itertools.chain.from_iterable(out))
n = 0
for i in l:
    if n == 0:
        items_df = pd.json_normalize(i)
    else:
        items_df = pd.concat([items_df,pd.json_normalize(i)])
    n += 1
    
#%% Split Dataframe by type
listing_dic = {}
listing_dic['mlb_card'] = items_df[items_df['item.type'] == 'mlb_card']
listing_dic['stadium'] = items_df[items_df['item.type'] == 'stadium']
listing_dic['unlockable'] = items_df[items_df['item.type'] == 'unlockable']
listing_dic['sponsorship'] = items_df[items_df['item.type'] == 'sponsorship']
listing_dic['equipment'] = items_df[items_df['item.type'] == 'equipment']

#%% Import Quick Sell Values
path = r"C:\Users\rcpat\Desktop\Personal Projects\Show22\Data"

mlb_qs = pd.read_csv(path+"\Show22_Qs - mlb_card.csv")
stadium_qs = pd.read_csv(path+"\Show22_Qs - stadium.csv")
unlockable_qs = pd.read_csv(path+"\Show22_Qs - unlockable.csv")
equipment_qs = pd.read_csv(path+"\Show22_Qs - equipment.csv")
sponsorship_qs = pd.read_csv(path+"\Show22_Qs - sponsorship.csv")

#%% Add QS Values to cards
listing_dic['mlb_card'] = pd.merge(listing_dic['mlb_card'], mlb_qs, 'left',\
                                   left_on = "item.ovr", right_on = 'Overall')
listing_dic['stadium'] = pd.merge(listing_dic['stadium'], stadium_qs, 'left',\
                                  left_on = 'item.rarity', right_on = 'Rarity')
listing_dic['unlockable'] = pd.merge(listing_dic['unlockable'], unlockable_qs, 'left',\
                                  left_on = 'item.rarity', right_on = 'Rarity')
listing_dic['equipment'] = pd.merge(listing_dic['equipment'], equipment_qs, 'left',\
                                  left_on = 'item.rarity', right_on = 'Rarity')
listing_dic['sponsorship'] = pd.merge(listing_dic['sponsorship'], sponsorship_qs, 'left',\
                                  left_on = 'item.rarity', right_on = 'Rarity')

    
 #%% Dictionary to Table
for t in types:
    if t =='mlb_card':
        items_df = listing_dic[t]
    else:
        items_df = pd.concat([items_df,listing_dic[t]])
        
#%% Subset and rename columns
#print(items_df.columns)

columns_to_keep = ['item.uuid', 'listing_name','best_sell_price','best_buy_price','Value','item.rarity','item.ovr','item.type']
items_df = items_df[columns_to_keep]

# --> Rename Columns
items_df = items_df.rename(columns={
    'item.uuid': 'ID',
    'listing_name': 'Item Name',
    'best_sell_price': 'Buy Now Price',
    'best_buy_price': 'Sell Now Price',
    'Value': 'Quicksell Price',
    'item.rarity': 'Rarity',
    'item.ovr': 'Overall',
    'item.type': 'Type'
    })

#print(items_df.columns)

#%% Replace values < QS w/ QS
items_df['Sell Now Price'] = np.where(items_df['Sell Now Price'] < items_df['Quicksell Price'],\
                    items_df['Quicksell Price'], items_df['Sell Now Price'])
#%% Create Margin Columns
items_df['Margin'] = (((items_df['Buy Now Price'] * .9)-1) - (items_df['Sell Now Price']+1)) / ((items_df['Buy Now Price'] * .9)+1) * 100
 
#%% Get completed sales
import concurrent.futures
import requests
import itertools

out = []
CONNECTIONS = 10
TIMEOUT = 15

urls = [f"https://mlb22.theshow.com/apis/listing.json?uuid={uuid}" for uuid in items_df.ID]

url_list = [urls[i::20] for i in range(1,21)]

for links in url_list:
    def load_url(url, timeout):
        ans = requests.get(url, timeout=timeout)
        return ans.text
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
        future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in links)
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
                data = json.loads(data)
            except Exception:
                future.cancel()
            finally:    
                out.append(data)
    sec = 60
    print(f"Iteration {url_list.index(links)+1} of {len(url_list)} finished; sleeping for {sec} seconds")
    time.sleep(sec)
    
#%%
price_dic = {}
price_df = pd.DataFrame()
for n in out:
    price_dic[n['item']['uuid']] = pd.json_normalize(n['completed_orders'])
    try:
        price_dic[n['item']['uuid']]['date'] = pd.to_datetime(price_dic[n['item']['uuid']]['date'])
    except:
        None
price_dic['uuid'] = price_dic[n['item']['uuid']]
del price_dic[n['item']['uuid']]

for uuid in price_dic.keys():
    price_dic[uuid] = len(price_dic[uuid]['date']>=(dt.datetime.now()-dt.timedelta(hours=1)))

#%% Sort By Descending Order and Create .CSV
# items_df = items_df.sort_values('Margin', ascending = False)

# from datetime import date
# items_df.to_csv(f"C:\\Users\\rcpat\\Desktop\\Personal Projects\\Show22\\Outputs\\Show22_Listings_{date.today()}.csv", index = False)


