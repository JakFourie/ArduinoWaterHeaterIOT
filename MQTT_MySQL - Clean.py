import paho.mqtt.client as mqtt #import the client1
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import datetime

############
def on_message(client, userdata, message):
    
    #print("message received " ,str(message.payload.decode("utf-8")))
    
    strData = str(message.payload.decode("utf-8")) + "," + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recordTuple = tuple(strData.split(","))
    print(recordTuple)#('89797x7899359', '30.16', '-0.22', '17.81', '84.08', '2020-06-24 10:29:26')
    
    try:
        cnx = mysql.connector.connect(user='user', password='pass', host='0.0.0.0', database='db')
        row_ins_temp = 'INSERT INTO UsageTable VALUES (%s, %s, %s, %s, %s, %s)'
        cursor = cnx.cursor()
        cursor.execute(row_ins_temp, recordTuple)
        cnx.commit()
        print(cursor.rowcount, "Record inserted successfully into Usage table")
        cursor.close()
    
    except mysql.connector.Error as error:
        print("Failed to insert record into Usage table {}".format(error))

    finally:
        if (cnx.is_connected()):
            cnx.close()
            print("MySQL connection is closed")

########################################
# MQTT Settings 
MQTT_Broker = "0.0.0.0"
MQTT_Port = 1883
Keep_Alive_Interval = 60
MQTT_Topic = "db"

print("creating new instance")
client = mqtt.Client("p1", clean_session=False) #create new instance
client.on_message=on_message #attach function to callback
print("connecting to broker")
client.username_pw_set("user", "pass")
client.connect(MQTT_Broker, int(MQTT_Port), int(Keep_Alive_Interval))

print("Subscribing to topic", MQTT_Topic)
client.subscribe(MQTT_Topic)

client.loop_forever()