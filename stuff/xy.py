#!/usr/bin/env python

from pymongo import MongoClient
import matplotlib.pyplot as plt

#Zugriff auf Datenbank
db_client = MongoClient("mongodb://TestDBAccessForGil:Ikemigoku754@ds145639.mlab.com:45639/mom-trainer_cloud")
db = db_client['mom-trainer_cloud']
#Access some data
testData = db.testData
trainsetId = "_TRAINSET14022017163905"
trainsetMetaData = testData.find({"_id":trainsetId}).limit(1)[0]
hands = trainsetMetaData["parkour"]["subject"]["hands"]
rightHand = hands["right"]
leftHand = hands["left"]

print rightHand["id"]
print rightHand["uuid"]

cursor1 = testData.find({"$and":[ {"trainset":trainsetId}, {"collector.id":rightHand["uuid"]}]}).limit(50)

t = []
xAcceleration = []
yAcceleration = []
zAcceleration = []

xRotation = []
yRotation = []
zRotation = []

rfid = []

zeroTime = 0
firstEntry = True

for record in cursor1:
    if firstEntry:
        zeroTime = record["data"]["stamp"]["microSeconds"]
        firstEntry = False
    time = (record["data"]["stamp"]["microSeconds"] - zeroTime)
    t.extend([time])
    xAcceleration.extend([record["data"]["acceleration"]["x"]])
    yAcceleration.extend([record["data"]["acceleration"]["y"]])
    zAcceleration.extend([record["data"]["acceleration"]["z"]])

    xRotation.extend([record["data"]["rotation"]["x"]])
    yRotation.extend([record["data"]["rotation"]["y"]])
    zRotation.extend([record["data"]["rotation"]["z"]])

    if record["data"]["rfid"] == "000000000000":
        rfid.extend([False])
    else:
        rfid.extend([True])


#plt.plot(timeStamp, xAcceleration, linestyle='-', marker='o', timeStamp, yAcceleration, linestyle='-', marker='x', timeStamp, zAcceleration, linestyle='-', marker='o')
#plt.plot(t, xAcceleration, '-x', t, yAcceleration, '-x', t, zAcceleration, '-x')

plt.figure(1)
plt.subplot(211)
plt.plot(t, xAcceleration, '-*', t, yAcceleration, '-*', t, zAcceleration, '-*')
plt.xlabel('time [microSeconds]')
plt.ylabel('acceleration []')
plt.subplot(212)
plt.plot(t, xRotation, '-*', t, yRotation, '-*', t, zRotation, '-*')
plt.xlabel('time [microSeconds]')
plt.ylabel('rotation []')

#plt.axis([0, 1, 0, 20])
plt.show()


##source: http://stackoverflow.com/questions/14399689/matplotlib-drawing-lines-between-points-ignoring-missing-data
"""
import numpy as np
import matplotlib.pyplot as plt

xs = np.arange(8)
series1 = np.array([1, 3, 3, None, None, 5, 8, 9]).astype(np.double)
s1mask = np.isfinite(series1)
series2 = np.array([2, None, 5, None, 4, None, 3, 2]).astype(np.double)
s2mask = np.isfinite(series2)

plt.plot(xs[s1mask], series1[s1mask], linestyle='-', marker='o')
plt.plot(xs[s2mask], series2[s2mask], linestyle='-', marker='o')

plt.show()
"""
