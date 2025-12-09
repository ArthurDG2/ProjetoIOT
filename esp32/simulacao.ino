// simulacao.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "SEU_WIFI";
const char* password = "SUA_SENHA";
const char* serverName = "http://SEU_IP:5000/api/solo";

// Função para gerar valores randômicos float
float randFloat(float minVal, float maxVal) {
  return minVal + (float)random(0, 10000) / 10000.0 * (maxVal - minVal);
}

// Função para simular crescimento da planta baseado no tempo
float simularCrescimento(int cicloDias) {
  // Simula crescimento sigmoidal
  if (cicloDias < 20) return randFloat(5, 30);        // Fase vegetativa inicial
  else if (cicloDias < 40) return randFloat(30, 70);  // Fase vegetativa
  else if (cicloDias < 60) return randFloat(70, 120); // Fase reprodutiva
  else if (cicloDias < 80) return randFloat(100, 150);// Maturação
  else return randFloat(120, 160);                    // Pré-colheita
}

// Função para determinar estágio fenológico baseado no tempo
String determinarEstagio(int cicloDias) {
  if (cicloDias < 10) return "V0";
  else if (cicloDias < 20) return "V1";
  else if (cicloDias < 30) return "V2";
  else if (cicloDias < 40) return "V3";
  else if (cicloDias < 45) return "V4";
  else if (cicloDias < 50) return "R1";
  else if (cicloDias < 55) return "R2";
  else if (cicloDias < 65) return "R3";
  else if (cicloDias < 75) return "R4";
  else if (cicloDias < 85) return "R5";
  else if (cicloDias < 95) return "R6";
  else if (cicloDias < 105) return "R7";
  else return "R8";
}

void setup() {
  Serial.begin(115200);
  
  // Inicializa random seed
  randomSeed(analogRead(0));
  
  // Conecta ao Wi-Fi
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

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
    
    // Simula dias desde o plantio (0-120 dias)
    int diasDesdePlantio = random(0, 121);
    
    // Criar objeto JSON
    StaticJsonDocument<1024> doc;
    
    // Localização (fazenda simulada)
    doc["latitude"] = randFloat(-23.0, -22.0);
    doc["longitude"] = randFloat(-47.0, -46.0);
    
    // Parâmetros do solo
    doc["temperatura_solo"] = randFloat(18, 30);
    doc["umidade_solo"] = randFloat(15, 45);
    doc["condutividade_solo"] = randFloat(0.1, 1.5);
    doc["ph"] = randFloat(5.5, 7.0);
    doc["npk_n"] = randFloat(20, 70);
    doc["npk_p"] = randFloat(10, 40);
    doc["npk_k"] = randFloat(20, 60);
    
    // Parâmetros ambientais
    float tempAr = randFloat(15, 35);
    doc["temperatura_ar"] = tempAr;
    doc["pressao"] = randFloat(950, 1050);
    doc["altitude"] = randFloat(500, 800);
    doc["umidade_relativa"] = randFloat(40, 90);
    doc["radiacao_solar"] = randFloat(200, 1200);
    doc["indice_uv"] = randFloat(1, 11);
    doc["velocidade_vento"] = randFloat(0, 15);
    doc["pluviometria_mm"] = randFloat(0, 20);
    
    // Parâmetros da planta
    float altura = simularCrescimento(diasDesdePlantio);
    doc["altura_planta"] = altura;
    doc["biomassa_estimada"] = altura * randFloat(0.01, 0.03);
    doc["area_foliar_lai"] = altura * randFloat(0.02, 0.05);
    
    // Dados agrícolas
    doc["cultura"] = "Soja";
    doc["estagio_fenologico"] = determinarEstagio(diasDesdePlantio);
    
    // Data de plantio (simula plantio há X dias)
    char dataPlantio[11];
    snprintf(dataPlantio, sizeof(dataPlantio), "2025-01-%02d", random(1, 29));
    doc["data_plantio"] = dataPlantio;
    
    // Serializar JSON
    String json;
    serializeJson(doc, json);
    
    Serial.println("Enviando dados...");
    Serial.println(json);
    
    // Enviar dados
    int resposta = http.POST(json);
    
    if (resposta > 0) {
      String respostaBody = http.getString();
      Serial.println("Resposta HTTP: " + String(resposta));
      Serial.println("Corpo da resposta: " + respostaBody);
    } else {
      Serial.println("Erro na requisição: " + String(resposta));
    }
    
    http.end();
  } else {
    Serial.println("Wi-Fi desconectado. Tentando reconectar...");
    WiFi.reconnect();
  }
  
  // Intervalo entre envios (1-5 minutos)
  int intervalo = random(60000, 300000);
  Serial.println("Aguardando " + String(intervalo/1000) + " segundos...");
  delay(intervalo);
}