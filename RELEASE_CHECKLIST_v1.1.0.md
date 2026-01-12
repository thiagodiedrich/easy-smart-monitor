# Release Checklist — Easy Smart Monitor v1.1.0

## 📦 Código
- [x] coordinator.py atualizado (porta + temperatura)
- [x] config_flow.py atualizado
- [x] const.py atualizado
- [x] sensor.py revisado
- [x] binary_sensor.py revisado
- [x] siren.py revisado
- [x] button.py revisado
- [x] Nenhum hardcode fora de const.py

## 🧠 Funcionalidades
- [x] Timeout de porta configurável por equipamento
- [x] Sirene habilitável/desabilitável por equipamento
- [x] Alertas de temperatura (min/max)
- [x] Novo status `temperature_alert`
- [x] TEST_MODE funcional em todas as camadas

## 🧪 Qualidade
- [x] test_client.py
- [x] test_config_flow.py
- [x] test_coordinator.py (FEATURE 1 + FEATURE 2)
- [x] test_entities.py atualizado
- [x] Todos os testes passam localmente

## 🤖 CI / Automação
- [x] GitHub Actions configurado
- [x] TEST_MODE ativo no CI
- [x] pytest rodando automaticamente

## 📄 Documentação
- [x] README.md atualizado
- [x] CHANGELOG.md atualizado (v1.1.0)

## 🏷️ Release
- [ ] Criar tag `v1.1.0`
- [ ] Publicar Release no GitHub
- [ ] (Opcional) Atualizar badge de CI no README
- [ ] (Opcional) Preparar estrutura HACS

## 🚀 Pós-release
- [ ] Planejar v1.2.0