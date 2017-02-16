#!/usr/bin/env python

from pymongo import MongoClient
import matplotlib.pyplot as plt

#Zugriff auf Datenbank
db_client = MongoClient("mongodb://TestDBAccessForGil:Ikemigoku754@ds145639.mlab.com:45639/mom-trainer_cloud")
db = db_client['mom-trainer_cloud']
#Access some data
testData = db.testData
data = testData.find({"trainset": "_TRAINSET14022017163905"}).limit(100)

plt.plot([1,2,3,4], [1,2,3,4], 'ro')
plt.axis([0, , 0, 20])
plt.xlabel('time [microSeconds]')
plt.ylabel('Value')
plt.show()
