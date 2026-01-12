# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.1.0] - 2026-01-11

### ✨ Added
- Configuração de **timeout de porta por equipamento**
- Possibilidade de **ativar/desativar sirene por equipamento**
- Suporte a **alertas de temperatura (min/max) por equipamento**
- Novo status de equipamento: `temperature_alert`
- Detalhamento de alerta de temperatura (`above_max` / `below_min`)
- Estrutura de dados extensível por domínio (porta, temperatura)
- Suporte completo a **TEST_MODE** em todas as camadas
- Novos testes cobrindo:
    - Timeout configurável de porta
    - Sirene desabilitada
    - Temperatura dentro e fora da faixa
    - Estados e atributos refletidos nas entidades

---

### 🔧 Changed
- Coordinator refatorado para:
    - Centralizar regras por equipamento
    - Separar claramente lógica de porta, temperatura e sirene
- Options Flow estendido para edição avançada de equipamentos
- Status do equipamento agora pode refletir múltiplas condições
- Entidades revisadas para refletir novos estados e atributos
- Constantes centralizadas e padronizadas no `const.py`

---

### 🛠 Fixed
- Cancelamento seguro de timers de porta
- Reset correto de status ao fechar porta ou silenciar sirene
- Consistência entre estado interno e entidades expostas
- Comportamento previsível em TEST_MODE (sem chamadas externas)

---

### 🧪 Tests
- Atualização completa do `test_coordinator.py`
- Atualização do `test_entities.py`
- Cobertura explícita de:
    - FEATURE 1 (porta configurável)
    - FEATURE 2 (alertas de temperatura)
- Garantia de compatibilidade com Home Assistant 2024.12+

---

### ⚠️ Backward Compatibility
- Totalmente compatível com a v1.0.0
- Equipamentos antigos continuam funcionando sem migração
- Valores padrão aplicados automaticamente quando campos novos não existem

---

### 🚀 Notes
- Esta versão marca a transição do Easy Smart Monitor para um
  **monitoramento inteligente baseado em regras por equipamento**
- Base preparada para futuras features:
    - Notificações
    - Sensor “Último Evento”
    - Retry exponencial
    - Integração com HACS