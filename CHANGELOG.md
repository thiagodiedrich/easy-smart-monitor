# Changelog

## [1.0.0] - 2026-01-11

### ✨ Added
- Integração Easy Smart Monitor
- Configuração 100% via UI (Config Flow)
- Gerenciamento de equipamentos e sensores
- Entidades dinâmicas por equipamento
- Lógica de sirene (porta aberta por 120s)
- Botão de reset da sirene
- Fila local persistente
- Envio assíncrono para API REST
- Autenticação com token e refresh automático
- Testes unitários com pytest

### 🧱 Architecture
- DataUpdateCoordinator como núcleo
- Client HTTP desacoplado
- Persistência via Store
- Código totalmente assíncrono

### 🛡️ Stability
- Sem chamadas bloqueantes
- Retry automático em falha de API
- Compatível com reload da integração