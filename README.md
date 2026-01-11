# Easy Smart Monitor

Custom Component para Home Assistant destinado ao monitoramento inteligente de
câmaras frias, freezers e geladeiras industriais ou comerciais.

A integração permite agrupar sensores físicos existentes em **EQUIPAMENTOS**,
aplicar lógica de negócio (porta aberta → sirene), persistir eventos localmente
e enviá-los de forma confiável para uma API REST externa.

---

## ✨ Recursos Principais

- Configuração **100% via UI (Config Flow)**
- Suporte a **múltiplos equipamentos**
- Criação **dinâmica de entidades**
- Lógica industrial de alarme:
  - Porta aberta por 120s → sirene
  - Reset reinicia o ciclo se a porta continuar aberta
- Fila local persistente (sem perda de dados)
- Envio assíncrono em lote para API REST
- Autenticação com token + refresh automático
- Totalmente assíncrono (não bloqueia o HA)
- Testes unitários com pytest

---

## 🧱 Arquitetura

Sensores existentes (HA)
↓
Entidades do Easy Smart Monitor
↓
Coordinator (lógica e timers)
↓
Fila local persistente
↓
Client HTTP assíncrono
↓
API REST

yaml
Copiar código

---

## 📦 Entidades Criadas

Para cada **EQUIPAMENTO** configurado:

| Tipo | Entidade |
|----|----|
| Temperatura | `sensor.<equipamento>_temperatura` |
| Porta | `binary_sensor.<equipamento>_porta` |
| Sirene | `switch.<equipamento>_sirene` |
| Reset | `button.<equipamento>_reset_sirene` |

---

## 🔧 Instalação

### 1️⃣ Copiar arquivos

Copie a pasta para:

/config/custom_components/easy_smart_monitor

shell
Copiar código

### 2️⃣ Estrutura esperada

easy_smart_monitor/
├── init.py
├── manifest.json
├── const.py
├── client.py
├── coordinator.py
├── sensor.py
├── binary_sensor.py
├── switch.py
├── button.py
├── config_flow.py
└── tests/

yaml
Copiar código

### 3️⃣ Reiniciar o Home Assistant

---

## ⚙️ Configuração

### 🔐 Primeira tela
- URL da API
- Usuário
- Senha

### 🧊 Gerenciamento de Equipamentos
- Nome do equipamento
- Local
- Sensores vinculados:
  - Temperatura
  - Porta
  - Energia (opcional)
  - Sirene
  - Botão

Tudo é feito via **Configurações → Dispositivos & Serviços**.

---

## 🚨 Lógica da Sirene

- Porta abre → inicia timer
- Porta permanece aberta por 120s → sirene dispara
- Porta fecha → timer cancelado
- Reset pressionado:
  - Sirene desliga
  - Timer reinicia se porta continuar aberta

---

## 📤 Fila Local & API

- Eventos são salvos localmente a cada mudança relevante
- Persistência via `.storage`
- Envio em lote a cada 60s
- Retry automático
- Token com refresh em caso de expiração
- Nenhum evento é perdido

---

## 🧪 Testes

### Estrutura
tests/
├── test_client.py
├── test_coordinator_queue.py
└── test_coordinator_siren.py

bash
Copiar código

### Executar testes
```bash
pip install pytest pytest-asyncio
pytest custom_components/easy_smart_monitor/tests
🛡️ Requisitos Técnicos
Home Assistant 2024.12+

Python 3.12

aiohttp

pytest (para testes)

📈 Próximos Passos (Roadmap)
Dashboard Lovelace automático

Métricas por equipamento

Health check da API

Criptografia da fila local

Migração de versão

📄 Licença
Uso privado / interno.
Distribuição conforme necessidade do projeto.