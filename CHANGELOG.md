# Changelog

## [1.0.0] - 2026-01-11

### 🎉 Primeira versão estável

#### ✨ Adicionado
- Integração customizada Easy Smart Monitor
- Config Flow completo via UI
- Gestão de múltiplos equipamentos
- Vinculação dinâmica de sensores
- Monitoramento de porta, temperatura, umidade e energia
- Sirene automática após porta aberta
- Botão para silenciar alarme
- Envio de eventos para API REST
- Fila local persistente
- TEST_MODE para desenvolvimento offline
- Testes unitários com pytest
- Estrutura pronta para CI/CD

#### 🧪 Testes
- test_client.py
- test_config_flow.py
- test_coordinator.py
- test_entities.py

#### 🧱 Arquitetura
- DataUpdateCoordinator central
- Client HTTP assíncrono
- Entidades desacopladas da lógica
- Persistência com Store