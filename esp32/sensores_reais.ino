// sensores_reais.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

// Configurações Wi-Fi
const char* ssid = "SEU_WIFI";
const char* password = "SUA_SENHA";
const char* serverName = "http://SEU_IP:5000/api/solo";

// Pinos dos sensores
#define ONE_WIRE_BUS 4        // DS18B20 para temperatura do solo
#define SOIL_MOISTURE_PIN 34  // Sensor de umidade do solo capacitivo
#define SOIL_PH_PIN 35        // Sensor de pH do solo
#define SOIL_EC_PIN 32        // Sensor de condutividade (EC)
#define LDR_PIN 33            // Sensor de luz (radiação solar)
#define RAIN_SENSOR_PIN 25    // Sensor de chuva
#define WIND_SPEED_PIN 26     // Sensor de velocidade do vento
#define WIND_DIR_PIN 27       // Sensor de direção do vento

// Objetos dos sensores
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature soilTempSensor(&oneWire);
Adafruit_BME280 bme;  // BME280 para temperatura, pressão, umidade do ar

// Variáveis para medição de vento e chuva
volatile unsigned long windCount = 0;
volatile unsigned long rainCount = 0;
unsigned long lastWindCheck = 0;
unsigned long lastRainCheck = 0;
const float WIND_FACTOR = 2.4;    // Fator de calibração do anemômetro (km/h por pulso)
const float RAIN_FACTOR = 0.2794; // mm por pulso do pluviômetro

// Interrupções
void IRAM_ATTR countWindPulse() {
  windCount++;
}

void IRAM_ATTR countRainPulse() {
  rainCount++;
}

void setup() {
  Serial.begin(115200);
  
  // Inicializar sensores
  Serial.println("Inicializando sensores...");
  
  // Temperatura do solo (DS18B20)
  soilTempSensor.begin();
  
  // BME280
  if (!bme.begin(0x76)) {
    Serial.println("Não foi possível encontrar o BME280. Verifique a conexão!");
  }
  
  // Configurar pinos
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(SOIL_PH_PIN, INPUT);
  pinMode(SOIL_EC_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(RAIN_SENSOR_PIN, INPUT_PULLUP);
  pinMode(WIND_SPEED_PIN, INPUT_PULLUP);
  pinMode(WIND_DIR_PIN, INPUT);
  
  // Configurar interrupções
  attachInterrupt(digitalPinToInterrupt(WIND_SPEED_PIN), countWindPulse, RISING);
  attachInterrupt(digitalPinToInterrupt(RAIN_SENSOR_PIN), countRainPulse, FALLING);
  
  // Conectar ao Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Conectando ao Wi-Fi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println("\nWi-Fi conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// Funções de leitura dos sensores
float readSoilTemperature() {
  soilTempSensor.requestTemperatures();
  return soilTempSensor.getTempCByIndex(0);
}

float readSoilMoisture() {
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  // Calibração: 0% = 4095 (seco), 100% = 1500 (molhado) - ajustar conforme sensor
  float percentage = map(rawValue, 4095, 1500, 0, 100);
  return constrain(percentage, 0, 100);
}

float readSoilPH() {
  int rawValue = analogRead(SOIL_PH_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  // Fórmula de calibração - ajustar com soluções padrão pH 4.0 e 7.0
  float phValue = 7.0 - ((voltage - 2.5) * 3.5);
  return constrain(phValue, 0, 14);
}

float readSoilEC() {
  int rawValue = analogRead(SOIL_EC_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  // Calibração - ajustar com soluções padrão
  float ecValue = voltage * 1000;  // dS/m
  return ecValue;
}

float readSolarRadiation() {
  int rawValue = analogRead(LDR_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  // Converter para W/m² (aproximado - calibrar com piranômetro)
  float radiation = voltage * 800;
  return radiation;
}

float readWindSpeed() {
  unsigned long currentTime = millis();
  unsigned long timeDiff = currentTime - lastWindCheck;
  
  if (timeDiff >= 5000) {  // Medir a cada 5 segundos
    float windSpeed = (windCount * WIND_FACTOR) / (timeDiff / 1000.0 / 3600.0);
    windCount = 0;
    lastWindCheck = currentTime;
    return windSpeed;
  }
  return -1;  // Indica que ainda não passou tempo suficiente
}

float readRainfall() {
  unsigned long currentTime = millis();
  unsigned long timeDiff = currentTime - lastRainCheck;
  
  if (timeDiff >= 60000) {  // Medir a cada minuto
    float rainfall = rainCount * RAIN_FACTOR;
    rainCount = 0;
    lastRainCheck = currentTime;
    return rainfall;
  }
  return 0;
}

int readWindDirection() {
  int rawValue = analogRead(WIND_DIR_PIN);
  // Converter para direção (0-360 graus)
  int direction = map(rawValue, 0, 4095, 0, 360);
  return direction;
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Ler todos os sensores
    float soilTemp = readSoilTemperature();
    float soilMoisture = readSoilMoisture();
    float soilPH = readSoilPH();
    float soilEC = readSoilEC();
    float solarRadiation = readSolarRadiation();
    float windSpeed = readWindSpeed();
    float rainfall = readRainfall();
    int windDirection = readWindDirection();
    
    // Ler BME280
    float airTemp = bme.readTemperature();
    float pressure = bme.readPressure() / 100.0F;  // hPa
    float altitude = bme.readAltitude(1013.25);    // Ajustar pressão ao nível do mar
    float humidity = bme.readHumidity();
    
    // Calcular índice UV aproximado (baseado na radiação solar)
    float uvIndex = solarRadiation / 100.0;
    
    // Simular dados de planta (seriam de sensores específicos)
    float plantHeight = soilMoisture * 0.5 + soilTemp * 0.3;  // Exemplo simplificado
    float biomass = plantHeight * 0.02;
    float leafArea = plantHeight * 0.05;
    
    // NPK (seriam de sensores específicos - aqui simulados)
    float npkN = soilMoisture * 0.8 + soilTemp * 0.2;
    float npkP = soilMoisture * 0.6 + soilTemp * 0.1;
    float npkK = soilMoisture * 0.7 + soilTemp * 0.15;
    
    // Criar JSON
    StaticJsonDocument<1024> doc;
    
    // Localização fixa (configurar conforme instalação)
    doc["latitude"] = -23.123456;
    doc["longitude"] = -47.123456;
    
    // Dados do solo
    doc["temperatura_solo"] = soilTemp;
    doc["umidade_solo"] = soilMoisture;
    doc["condutividade_solo"] = soilEC;
    doc["ph"] = soilPH;
    doc["npk_n"] = npkN;
    doc["npk_p"] = npkP;
    doc["npk_k"] = npkK;
    
    // Dados ambientais
    doc["temperatura_ar"] = airTemp;
    doc["pressao"] = pressure;
    doc["altitude"] = altitude;
    doc["umidade_relativa"] = humidity;
    doc["radiacao_solar"] = solarRadiation;
    doc["indice_uv"] = uvIndex;
    doc["velocidade_vento"] = windSpeed;
    doc["pluviometria_mm"] = rainfall;
    
    // Dados da planta
    doc["altura_planta"] = plantHeight;
    doc["biomassa_estimada"] = biomass;
    doc["area_foliar_lai"] = leafArea;
    
    // Dados agrícolas (configurar conforme plantio)
    doc["cultura"] = "Soja";
    doc["estagio_fenologico"] = "V3";
    doc["data_plantio"] = "2025-01-10";
    
    // Serializar e enviar
    String json;
    serializeJson(doc, json);
    
    Serial.println("Dados coletados:");
    Serial.println(json);
    
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
    
    int resposta = http.POST(json);
    
    if (resposta > 0) {
      Serial.println("Resposta: " + String(resposta));
      String respostaBody = http.getString();
      Serial.println("Corpo: " + respostaBody);
    } else {
      Serial.println("Erro: " + String(resposta));
    }
    
    http.end();
  }
  
  // Intervalo de envio (5 minutos para sensores reais)
  delay(300000);
}