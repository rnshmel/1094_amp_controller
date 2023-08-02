// arduino amp control board code
// serial comms with python script tointeract with user
// I2C with DAC for VVA gain
// ADC for temp and current sensor
// digital out to toggle amp on/off
// author: RNS

#include <Wire.h>
#define MCP4725_ADDR 0x60

// pins
// A0 = ADC in - current sense
int currentPin = A0;
int currentVal = 0;
// A1 = ADC in - temp sense
int tempPin = A1;
int tempVal = 0;
// VVA gain value, 0-100
char vvaGain = 0;
// amp is pulled low, 5V for shutdown
// start in shutdown
// (stat = 0, val = HIGH)
// (stat = 1, val = LOW)
char ampStat = 0;
// amp pin
int ampPin = A3;
// amp voltage ref
int dacBits = 0;
// control msg for comms
const byte sizeControlMsg = 2;
char controlMsg[sizeControlMsg];

void setup() 
{
  // setup, run once
  pinMode(ampPin, OUTPUT);
  digitalWrite(ampPin, HIGH);
  Wire.begin();
  Serial.begin(9600);
  Serial.println("<good morning, dave>");

}

void loop() 
{
  // main code loop
  // wait for serial input
  if (Serial.available() > 0)
  {
    // serial input RX
    delay(1);
    // dump message into control message array
    recvControlMsg();
    // get message type
    char msgType = controlMsg[0];
    // debug prints
    /*
    for (int i = 0; i < sizeControlMsg; i++)
    {
      Serial.print(controlMsg[i], DEC);
      Serial.print(" : ");
    }
    Serial.print("\n");
    Serial.println(msgType, DEC);*/

    // do message action
    msgAction(msgType);
  }

}

void msgAction(int msgType)
{
  switch(msgType)
  {
    case 0:
      // msg 0 =  current sense A0
      // get value
      currentVal = analogRead(currentPin);
      // return value
      Serial.print(currentVal);
      break;
    case 1:
      // msg 1 = temp sens A1
      // get val
      tempVal = analogRead(tempPin);
      // return val
      Serial.print(tempVal);
      break;
    case 2:
      // msg 2 = gain VVA set
      vvaGain = controlMsg[1];
      // send vva gain to DAC
      // 12 bit DAC = 4096 values
      // data is fractional value of ref voltage (5V)
      dacBits = int((vvaGain/100.0)*4095);
      // write to I2C
      Wire.beginTransmission(MCP4725_ADDR);
      // from MCP4725 datasheet, figure 6-2, pg 25
      Wire.write(64); // cmd to update the DAC
      Wire.write(dacBits >> 4); // the 8 MSB
      Wire.write((dacBits & 15) << 4); // the 4 LSB
      Wire.endTransmission();
      Serial.print(vvaGain);
      break;
    case 3:
      // msg 3 = amp toggle
      if (ampStat == 0)
      {
        // turn amp on
        ampStat = 1;
        digitalWrite(ampPin, LOW);
      }
      else
      {
        // turn amp off
        ampStat = 0;
        digitalWrite(ampPin, HIGH);
      }
      Serial.print(ampStat);
      break;
    default:
      // default
      Serial.print(7);
    }

}

void recvControlMsg()
{
  char rxc;
  for (int i = 0; i < sizeControlMsg; i++)
  {
    rxc = Serial.read();
    delay(1);
    controlMsg[i] = rxc;
    //Serial.print("i: ");
    //Serial.println(i, DEC);
    //Serial.print("rxc: ");
    //Serial.println(rxc, DEC);
  }
  // flush serial input
  delay(2);
  while (Serial.available() > 0)
  {
    Serial.read();
    delay(2);
  }
}