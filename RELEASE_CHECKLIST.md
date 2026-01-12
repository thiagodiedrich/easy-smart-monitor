# Release Checklist – Easy Smart Monitor v1.0.1

## 📦 Código
- [ ] Código revisado
- [ ] Nenhum TODO / placeholder
- [ ] Logs adequados
- [ ] Tipagem consistente
- [ ] Sem erros no startup
- [x] config_flow.py completo
- [x] coordinator.py consistente
- [x] client.py com TEST_MODE
- [x] sensor.py
- [x] binary_sensor.py
- [x] siren.py
- [x] button.py
- [x] const.py
- [x] __init__.py
- [x] manifest.json

## 🌐 UX
- [x] Configuração 100% via UI
- [x] Fluxo de equipamentos
- [x] Fluxo de sensores
- [x] Feedback claro de status
- [x] Botão de silenciar alarme

## 🧪 Qualidade
- [x] TEST_MODE funcional
- [x] Nenhuma chamada externa em testes
- [x] Testes unitários cobrindo core
- [x] Projeto testável offline

## 📄 Documentação
- [x] README.md
- [x] CHANGELOG.md
- [x] Checklist de release

## 🤖 CI / Automação
- [ ] GitHub Actions configurado
- [ ] Badge de status no README

## 🧪 Testes
- [ ] pytest executado
- [ ] Testes passando
- [ ] Mock de API validado
- [ ] Timer de sirene testado

## ⚙️ Home Assistant
- [ ] Integração instala sem erro
- [ ] Config Flow funcional
- [ ] Entidades criadas corretamente
- [ ] Reload da integração funcionando

## 📤 API
- [ ] Login funcionando
- [ ] Token renovado corretamente
- [ ] Retry em falha validado
- [ ] Fila limpa após sucesso

## 📚 Documentação
- [ ] README.md atualizado
- [ ] CHANGELOG.md atualizado
- [ ] Versão definida (v1.0.1)

## 🚀 Release
- [ ] Commit versionado
- [ ] Tag criada (`v1.0.1`)
- [ ] Backup realizado