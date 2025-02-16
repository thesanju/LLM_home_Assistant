#include <DHT.h>

// DHT11 Configuration
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// MQ-2 Configuration
const int gasSensorPin = A0;
float R0 = 39.52;
float Rs = 0;
float ratio = 0;
float voltage = 0;

String getAQICategory(float AQI) {
    if (AQI <= 50) return "Good";
    else if (AQI <= 100) return "Moderate";
    else if (AQI <= 150) return "Unhealthy for Sensitive Groups";
    else if (AQI <= 200) return "Unhealthy";
    else if (AQI <= 300) return "Very Unhealthy";
    else return "Hazardous";
}

void setup() {
    Serial.begin(9600);
    dht.begin();
    delay(1000);
}

void loop() {
    // Read DHT11 Data
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    // Read MQ-2 Data
    int sensorValue = analogRead(gasSensorPin);
    voltage = sensorValue * (5.0 / 1023.0);
    Rs = (5.0 - voltage) / voltage * 10.0;
    ratio = Rs / R0;
    
    // Calculate AQI
    float AQI = log(ratio) * 20;
    if (AQI < 0) AQI = 0;
    if (AQI > 300) AQI = 300;
    
    String airQuality = getAQICategory(AQI);
    
    // Send data including air quality category
    if (!isnan(temperature) && !isnan(humidity)) {
        Serial.print(temperature, 1);
        Serial.print(",");
        Serial.print(humidity, 1);
        Serial.print(",");
        Serial.print(sensorValue);
        Serial.print(",");
        Serial.print(AQI, 1);
        Serial.print(",");
        Serial.println(airQuality);
    }
    
    delay(2000);
}