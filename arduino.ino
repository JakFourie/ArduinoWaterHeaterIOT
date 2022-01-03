#define aref_voltage 4.096

//Radio
#define TINY_GSM_MODEM_SIM800

// Set serial for debug console (to the Serial Monitor, default speed 115200)
#define SerialMon Serial

// or Software Serial on Uno, Nano
#include <SoftwareSerial.h>
SoftwareSerial SerialAT(3, 4); // tx, rx on sim

//// Define the serial console for debug prints, if needed
//#define TINY_GSM_DEBUG SerialMon

//// Range to attempt to autobaud
#define GSM_AUTOBAUD_MIN 9600
#define GSM_AUTOBAUD_MAX 115200

//// Define how you're planning to connect to the internet
#define TINY_GSM_USE_GPRS true
#define TINY_GSM_USE_WIFI false

// set GSM PIN, if any
#define GSM_PIN ""

// Your GPRS credentials, if any
const char apn[] = "internet";
const char gprsUser[] = "";
const char gprsPass[] = "";

// Your WiFi connection credentials, if applicable
const char wifiSSID[] = "YourSSID";
const char wifiPass[] = "YourWiFiPass";

//// MQTT details
const char* broker = "0.0.0.10";
const char* SIM = "89404x3296728";

#include <TinyGsmClient.h>
#include <PubSubClient.h>

//// Just in case someone defined the wrong thing..
#if TINY_GSM_USE_GPRS && not defined TINY_GSM_MODEM_HAS_GPRS
#undef TINY_GSM_USE_GPRS
#undef TINY_GSM_USE_WIFI
#define TINY_GSM_USE_GPRS false
#define TINY_GSM_USE_WIFI true
#endif
#if TINY_GSM_USE_WIFI && not defined TINY_GSM_MODEM_HAS_WIFI
#undef TINY_GSM_USE_GPRS
#undef TINY_GSM_USE_WIFI
#define TINY_GSM_USE_GPRS true
#define TINY_GSM_USE_WIFI false
#endif

#ifdef DUMP_AT_COMMANDS
  #include <StreamDebugger.h>
  StreamDebugger debugger(SerialAT, SerialMon);
  TinyGsm modem(debugger);
#else
TinyGsm modem(SerialAT);
#endif
TinyGsmClient client(modem);
PubSubClient mqtt(client);

#define LED_PIN 13
int ledStatus = LOW;

int countSendMQTT = 0;
uint32_t lastReconnectAttempt = 0;

void mqttCallback(char* topic, byte* payload, unsigned int len) {
  SerialMon.print("Message arrived [");
  SerialMon.print(topic);
  SerialMon.print("]: ");
  SerialMon.write(payload, len);
  SerialMon.println();
}

boolean mqttConnect() {
  SerialMon.print("Connecting to ");
  SerialMon.print(broker);

  // Or, if you want to authenticate MQTT:
  boolean status = mqtt.connect(SIM, "user", "password");

  if (status == false) {
    SerialMon.println(" fail");
    return false;
  }
  SerialMon.println(" success");

//  mqtt.publish("test", "GsmClientTest started");//For testing

  return mqtt.connected();
}

////////////////////////////////////////////

#include "EmonLib.h"
// Include Emon Library
EnergyMonitor emon1; // Create an instance

/////////////////////////////////////////////////////////////////////////////////////////////
//Temp
////////////////////////////////////////////////////////////////////////////////////////////

// which analog pin to connect
#define THERMISTORPIN A5
// resistance at 25 degrees C
#define THERMISTORNOMINAL 10000
// temp. for nominal resistance (almost always 25 C)
#define TEMPERATURENOMINAL 25
// how many samples to take and average, more takes longer
// but is more 'smooth'
#define NUMSAMPLES 5
// The beta coefficient of the thermistor (usually 3000-4000)
#define BCOEFFICIENT 3950
// the value of the 'other' resistor
#define SERIESRESISTOR 10000

int samples[NUMSAMPLES];

///////////////////////////////////////////////////////////////////////////////////////////////
//DC Voltage
//////////////////////////////////////////////////////////////////////////////////////////////
// number of analog samples to take per reading
#define NUM_SAMPLES 10
int sum = 0;                    // sum of samples taken
unsigned char sample_count = 0; // current sample number
float voltage = 0.0;            // calculated voltage

/////////////////////////////////////////////////////////////////////////////////////////////////
////DC Current
////////////////////////////////////////////////////////////////////////////////////////////////
const int analogIn = A0;
int mVperAmp = 100; // use 100 for 20A Module and 66 for 30A Module
int RawValue= 0;
int ACSoffset = 2500;
double Voltage = 0;
double Amps = 0;

//
/////////////////////////////////////////////////////////////////////////////////////////////////////
void modemSetup()
{
   
  SerialMon.println("Modem Setup - Wait...");

  // Set GSM module baud rate
  // TinyGsmAutoBaud(SerialAT,GSM_AUTOBAUD_MIN,GSM_AUTOBAUD_MAX);
  SerialAT.begin(9600);
  delay(6000);

  // Restart takes quite some time
  // To skip it, call init() instead of restart()
  SerialMon.println("Initializing modem...");
  //modem.restart();
  modem.init();

  String modemInfo = modem.getModemInfo();
  SerialMon.print("Modem Info: ");
  SerialMon.println(modemInfo);

#if TINY_GSM_USE_GPRS
  // Unlock your SIM card with a PIN if needed
  if ( GSM_PIN && modem.getSimStatus() != 3 ) {
    modem.simUnlock(GSM_PIN);
  }
#endif


  SerialMon.print("Waiting for network...");
  if (!modem.waitForNetwork()) {
    SerialMon.println(" fail");
    delay(10000);
    return;
  }
  SerialMon.println(" success");

  if (modem.isNetworkConnected()) {
    SerialMon.println("Network connected");
  }

#if TINY_GSM_USE_GPRS
  // GPRS connection parameters are usually set after network registration
    SerialMon.print(F("Connecting to "));
    SerialMon.print(apn);
    if (!modem.gprsConnect(apn, gprsUser, gprsPass)) {
      SerialMon.println(" fail");
      delay(10000);
      return;
    }
    SerialMon.println(" success");

  if (modem.isGprsConnected()) {
    SerialMon.println("GPRS connected");
  }
#endif
}
//////////////////////////////////////////////////////////////////////////////////////////////////

void setup()
{
  // Set console baud rate
//  SerialMon.begin(115200);
    Serial.begin(115200);
  delay(10);

  pinMode(LED_PIN, OUTPUT);
//  initializeResetSim();  
  modemSetup();

  // MQTT Broker setup
  mqtt.setServer(broker, 1883);
  mqtt.setCallback(mqttCallback);

  analogReference(EXTERNAL);

///////////////////////////////////////////////////////////////////////////////////////////////
//AC Current
//////////////////////////////////////////////////////////////////////////////////////////////
  emon1.current(1, 74.074);             // Current: input pin, calibration. Pin A1// Calibration calc is (100 ÷ 0.050) ÷ (Burden resistor of 18) = 111.11 from https://learn.openenergymonitor.org/electricity-monitoring/ctac/ct-and-ac-power-adaptor-installation-and-calibration-theory


}

void loop()
{

  String strData(SIM); //= "89467x8876232";
  strData += ","; //"89467x8876232,"
///////////////////////////////////////////////////////////////////////////////////////////////
//AC Current
//////////////////////////////////////////////////////////////////////////////////////////////
  double Irms = emon1.calcIrms(1480);  // Calculate Irms only
//  Serial.print(Irms*230.0);           // Apparent power
  strData += Irms*230.0;
//  Serial.print(" w AC, ");
  strData += ",";


/////////////////////////////////////////////////////////////////////////////////////////////
//DC Current
////////////////////////////////////////////////////////////////////////////////////////////
   RawValue = analogRead(analogIn);
   Voltage = (RawValue / 1024.0) * 4096; // Gets you mV - Vref is 4096 with LM4040
   Amps = ((Voltage - ACSoffset) / mVperAmp);

//   Serial.print(Amps,3); // the '3' after voltage allows you to display 3 digits after decimal point
   strData += Amps;
//   Serial.print(" AmpsDC, "); // shows the voltage measured
   strData += ",";

/////////////////////////////////////////////////////////////////////////////////////////////
//Temp
////////////////////////////////////////////////////////////////////////////////////////////
  uint8_t i;
  float average;

  // take N samples in a row, with a slight delay
  for (i=0; i< NUMSAMPLES; i++) {
   samples[i] = analogRead(THERMISTORPIN)* (aref_voltage/5);
   delay(10);
  }

  // average all the samples out
  average = 0;
  for (i=0; i< NUMSAMPLES; i++) {
     average += samples[i];
  }
  average /= NUMSAMPLES;

//  Serial.print("Average analog reading ");
//  Serial.println(average);

  // convert the value to resistance
  average = 1023 / average - 1;
  average = SERIESRESISTOR / average;
//  Serial.print("Thermistor resistance ");
//  Serial.println(average);

  float steinhart;
  steinhart = average / THERMISTORNOMINAL;     // (R/Ro)
  steinhart = log(steinhart);                  // ln(R/Ro)
  steinhart /= BCOEFFICIENT;                   // 1/B * ln(R/Ro)
  steinhart += 1.0 / (TEMPERATURENOMINAL + 273.15); // + (1/To)
  steinhart = 1.0 / steinhart;                 // Invert
  steinhart -= 273.15;                         // convert to C

//  Serial.print(steinhart);
  strData += steinhart;
//  Serial.print(" C, ");
  strData += ",";

/////////////////////////////////////////////////////////////////////////////////////////////
//DC Voltage
////////////////////////////////////////////////////////////////////////////////////////////
      // take a number of analog samples and add them up
    while (sample_count < NUM_SAMPLES)
    {
        sum += analogRead(A4);
        sample_count++;
        delay(10);
    }
    // calculate the voltage
    // use 5.0 for a 5.0V ADC reference voltage
    // 5.015V is the calibrated reference voltage
    voltage = ((float)sum / (float)NUM_SAMPLES * aref_voltage) / 1024.0;
    // send voltage for display on Serial Monitor
    // voltage multiplied by 11 when using voltage divider that
    // divides by 11. 11.132 is the calibrated voltage divide
    // value
    // InV/OutV = 230/3.956 = 58.13953488372093‬ vir 200 en 3.5 k netwerk
//    Serial.print(voltage * 63.5);
    strData += voltage * 63.5;
//    Serial.println (" vDC");
    sample_count = 0;
    sum = 0;

    Serial.println(strData);

////////////////////////////////////////////////////////////////////////
  if (countSendMQTT >= 60){
    if (!mqtt.connected()) {
      SerialMon.println("=== MQTT NOT CONNECTED ===");
      // Reconnect every 10 seconds
      uint32_t t = millis();
      if (t - lastReconnectAttempt > 10000L)
      {
        lastReconnectAttempt = t;
        SerialMon.print(t);
        SerialMon.println(" since connection attempt");
  
        if (mqttConnect())
        {
          lastReconnectAttempt = 0;
        }
        else
        {
          modemSetup();
        }
      }
      delay(100);
      countSendMQTT = 0;
      return;
    }

    mqtt.publish("Elon", (char*) strData.c_str());
    countSendMQTT = 0;
  }

///////////////////////////////////////////////////////////////////////

  delay(1000); //Take measurement every second
  countSendMQTT++;

}

// any pin connected to the sim reset pin
// or if you use it for global reset put it on the microcontroller reset pin,
// but that will make it more sensitive without a 10K resistor
uint8_t pinReset = 2;

void initializeResetSim(void) {
  pinMode(pinReset, OUTPUT);
  digitalWrite(pinReset, HIGH);
}

void resetSim(void) {
  digitalWrite(pinReset, LOW);
  // use enough delay so that the sim can actually be reset
  delay(100);
  digitalWrite(pinReset, HIGH);
  delay(100);
}
