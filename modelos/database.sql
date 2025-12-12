CREATE DATABASE iot_db;

CREATE TABLE dados_solo (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Localização
    latitude FLOAT,
    longitude FLOAT,

    -- Solo
    temperatura_solo FLOAT,
    umidade_solo FLOAT,
    condutividade_solo FLOAT,
    ph FLOAT,
    npk_n FLOAT,
    npk_p FLOAT,
    npk_k FLOAT,

    -- Atmosfera
    temperatura_ar FLOAT,
    pressao FLOAT,
    altitude FLOAT,
    umidade_relativa FLOAT,
    radiacao_solar FLOAT,
    indice_uv FLOAT,
    velocidade_vento FLOAT,
    pluviometria_mm FLOAT,

    -- Planta
    altura_planta FLOAT,
    biomassa_estimada FLOAT,
    area_foliar_lai FLOAT,

    -- Dados agrícolas
    cultura VARCHAR(50),
    estagio_fenologico VARCHAR(50),
    data_plantio DATE,
    data_observacao DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Produção
    producao_kg FLOAT NULL
);

CREATE TABLE estagios_culturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cultura VARCHAR(50) NOT NULL,
    codigo_estagio VARCHAR(10) NOT NULL,
    descricao VARCHAR(255) NOT NULL
);

INSERT INTO estagios_culturas (cultura, codigo_estagio, descricao) VALUES
('Soja', 'V0', 'Emergência'),
('Soja', 'V1', '1ª folha trifoliolada'),
('Soja', 'V2', '2ª folha trifoliolada'),
('Soja', 'V3', '3ª folha trifoliolada'),
('Soja', 'V4', '4ª folha trifoliolada'),
('Soja', 'R1', 'Início da floração'),
('Soja', 'R2', 'Floração plena'),
('Soja', 'R3', 'Formação de vagens'),
('Soja', 'R4', 'Enchimento de vagens'),
('Soja', 'R5', 'Enchimento de grãos'),
('Soja', 'R6', 'Grão cheio'),
('Soja', 'R7', 'Pré-colheita'),
('Soja', 'R8', 'Colheita');