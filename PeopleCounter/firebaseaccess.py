import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore

#Connect to firebase database
def connDb():
    cred = credentials.Certificate("C:/Users/azzag/Documents/Firebase Credentials/people-counting-device-firebase-adminsdk-cp0i8-64435a2805.json")
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    return db

#Add new count entry to database
def addCount(id, count, threshold, time, deviceName, db):
    doc_ref = db.collection(u'count_data').document(str(id))

    doc_ref.set({
        u'id': id,
        u'count': count,
        u'threshold': threshold,
        u'time': time,
        u'device_name' : deviceName
    })

    print("Database updated. Id = " + str(id))

#get current threshold value from database or default to 10 if not found
def getThreshold(db):
    threshold = 10

    doc_ref = db.collection(u'threshold').document(u'threshold_val')

    doc = doc_ref.get()

    if doc.exists:
        threshold = doc.to_dict()['threshold']
    else:
        print(u'No threshold found! Using default of 10. Update using web app')

    return threshold


#get latest document id for firestore entries
def getLatestFirestoreId(db):
    maxId = 0

    docs = db.collection(u'count_data').stream()

    for doc in docs:
        currentId = int(doc.id)

        if currentId > maxId:
            maxId = currentId

    return maxId + 1

#get latest threshold from database (if it has been updated since program start)
def getLatestThreshold(db):
    threshold = -1

    doc_ref = db.collection(u'threshold').document(u'threshold_val')

    doc = doc_ref.get()
    if doc.exists:
        threshold = doc.to_dict()['threshold']

    return threshold


#get device name from firestore
def getDeviceName(db):
    device_name = "Default name"

    doc_ref = db.collection(u'devices').document(u'device1')

    doc = doc_ref.get()

    if doc.exists:
        device_name = doc.to_dict()['name']
    else:
        print(u'No device name found! Using default of \'Default Name\'. Update using web app!')

    return device_name
