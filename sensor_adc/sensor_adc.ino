#include <Wire.h>
#include <Adafruit_ADS1015.h>

Adafruit_ADS1115 ads(0x48);
unsigned long timer = 0;
long loopTime = 50000;   // microseconds
 
void setup() {
  Serial.begin(38400);
  
  ads.setGain(GAIN_TWOTHIRDS);  // +/- 6.144V  1 bit = 0.1875mV (default)
  // ads.setGain(GAIN_ONE);        +/- 4.096V  1 bit = 0.125mV
  // ads.setGain(GAIN_TWO);        +/- 2.048V  1 bit = 0.0625mV
  // ads.setGain(GAIN_FOUR);       // +/- 1.024V  1 bit = 0.03125mV
  // ads.setGain(GAIN_EIGHT);      +/- 0.512V  1 bit = 0.015625mV
  // ads.setGain(GAIN_SIXTEEN);    +/- 0.256V  1 bit = 0.0078125mV
  ads.begin();
    
  timer = micros();
}

void loop() {
  timeSync(loopTime);
  int16_t val0 = ads.readADC_SingleEnded(0);
  int16_t val1 = ads.readADC_SingleEnded(1);
  int16_t val2 = ads.readADC_SingleEnded(2);
  int16_t val3 = ads.readADC_SingleEnded(3);
  sendToPC(&val0, &val1, &val2, &val3);
}

void timeSync(unsigned long deltaT) {
  unsigned long currTime = micros();
  long timeToDelay = deltaT - (currTime - timer);
  if (timeToDelay > 50000)
  {
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0)
  {
    delayMicroseconds(timeToDelay);
  }
  else
  {
      // timeToDelay is negative so we start immediately
  }
  timer = currTime + timeToDelay;
}
 
void sendToPC(int16_t* data0, int16_t* data1, int16_t* data2, int16_t* data3) {
  byte* byteData0 = (byte*)(data0);
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte buf[8] = {byteData0[0], byteData0[1],
                  byteData1[0], byteData1[1],
                  byteData2[0], byteData2[1],
                  byteData3[0], byteData3[1]};
  Serial.write(buf, 8);
}
