# Easy Smart Monitor

Easy Smart Monitor é uma **integração customizada para Home Assistant** focada em
**monitoramento inteligente de equipamentos**, com ênfase em:

- Porta aberta com alarme automático
- Monitoramento de temperatura, umidade e energia
- Envio de eventos para API externa
- Operação resiliente com fila local
- Configuração 100% via interface gráfica
- Modo de teste sem API externa (TEST_MODE)

---

## 🚀 Recursos Principais

- ✅ Configuração via UI (Config Flow)
- ✅ Suporte a múltiplos equipamentos
- ✅ Sensores dinâmicos por equipamento
- ✅ Sirene automática após porta aberta por tempo configurável
- ✅ Botão para silenciar alarme
- ✅ Persistência local de eventos
- ✅ Envio assíncrono para API REST
- ✅ TEST_MODE para desenvolvimento offline
- ✅ Testes unitários com pytest
- ✅ Pronto para CI/CD (GitHub Actions)

---

## 📦 Entidades Criadas

Por equipamento:

- `sensor.<equipamento>_status`
- `sensor.<equipamento>_temperatura`
- `sensor.<equipamento>_umidade`
- `binary_sensor.<equipamento>_energia`
- `binary_sensor.<equipamento>_porta`
- `siren.<equipamento>_alarme`
- `button.<equipamento>_silenciar_alarme`

Globais:

- `sensor.easy_smart_monitor_status`
- `sensor.easy_smart_monitor_queue`

---

## 🧭 Instalação

### Manual

1. Copie a pasta:
custom_components/easy_smart_monitor

makefile
Copiar código
para:
config/custom_components/

markdown
Copiar código

2. Reinicie o Home Assistant

3. Vá em:
Configurações → Dispositivos e Serviços → Adicionar Integração

yaml
Copiar código

4. Procure por **Easy Smart Monitor**

---

## ⚙️ Configuração

Toda a configuração é feita via interface gráfica:

- Login na API
- Criação de equipamentos
- Vinculação de sensores existentes
- Ajuste de intervalos
- Ativação/desativação de equipamentos e sensores

---

## 🧪 TEST_MODE (Modo de Teste)

O **TEST_MODE** permite usar a integração **sem a API oficial online**.

### Quando usar
- Desenvolvimento local
- Testes automatizados
- Validação de UI e entidades
- Ambientes sem acesso à internet

### Como ativar

#### Linux / macOS
```bash
export EASY_SMART_MONITOR_TEST_MODE=true
Docker / Home Assistant OS
Adicionar variável de ambiente:

ini
Copiar código
EASY_SMART_MONITOR_TEST_MODE=true
O que muda em TEST_MODE
✔️ Login é simulado

✔️ Nenhuma chamada HTTP real

✔️ Envio de eventos é ignorado

✔️ Status da integração = test_mode

Para produção, não defina essa variável.

🧪 Testes
Instalar dependências
bash
Copiar código
pip install pytest pytest-asyncio homeassistant
Rodar testes
bash
Copiar código
pytest
Cobertura atual:

client.py

config_flow.py

coordinator.py

entidades (sensor, binary_sensor, siren, button)

🤖 CI / GitHub Actions
O projeto está preparado para CI com GitHub Actions:

Executa testes automaticamente

Usa TEST_MODE

Evita regressões

🧱 Arquitetura (Resumo)
Coordinator: cérebro do sistema

Entidades: apenas refletem estado

API Client: comunicação externa

Config Flow: UX completa via UI

Fila local: Store persistente