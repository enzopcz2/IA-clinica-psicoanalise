# 📝 NOTES — Considerações Técnicas do Projeto

Este documento descreve as decisões técnicas, dificuldades encontradas e aprendizados durante o desenvolvimento do pipeline de análise clínica automatizada.

## 1️⃣ Como eu entendi o problema?

O problema proposto não era apenas gerar uma análise psicológica a partir de um texto, mas construir um pipeline confiável, capaz de:

- processar múltiplos textos automaticamente
- utilizar um modelo de linguagem para gerar análise clínica
- garantir que a saída obedeça a um contrato estrutural mínimo
- falhar de forma explícita quando não houver informação suficiente

Ou seja, o foco não estava na criatividade do modelo, mas na robustez do sistema.


## 2️⃣ Por que estruturei o prompt dessa forma?

Foram definidos dois prompts com objetivos distintos:

- **prompt_v1**: exploratório e qualitativo  
  Permite observar a resposta livre do modelo, sem impor formato ou estrutura rígida.

- **prompt_v2**: orientado a schema  
  Projetado para produzir uma saída compatível com validação automática via Pydantic.

Essa separação permite:
- experimentação controlada
- comparação entre saídas livres e estruturadas
- evolução gradual do sistema sem acoplamento excessivo ao prompt


## 3️⃣ Quais problemas encontrei?

Os principais problemas enfrentados foram:

- Mudanças no formato de resposta da OpenAI Responses API
- Respostas estruturadas (`output_json`) em vez de texto puro
- Falhas silenciosas quando exceções não eram corretamente logadas
- Textos clínicos pouco informativos que não atendiam às regras mínimas do schema

Esses problemas exigiram tratamento explícito de exceções e maior visibilidade do fluxo.

## 4️⃣ O que melhorou do v1 para o v2?

Do prompt_v1 para o prompt_v2, houve melhorias significativas:

- Definição clara de campos esperados
- Saída em formato JSON padronizado
- Compatibilidade direta com validação Pydantic
- Maior previsibilidade da resposta do modelo
- Redução de ambiguidades clínicas

O v2 transformou uma análise textual livre em um artefato estruturado e validável.

## 5️⃣ O que eu faria diferente em produção?

Em um ambiente de produção, algumas melhorias seriam importantes:

- Implementar retries com backoff exponencial para chamadas à API
- Criar um modo offline com mock de modelo para testes
- Adicionar versionamento de schemas clínicos
- Monitorar taxas de falha por tipo de validação
- Implementar logging estruturado (ex: JSON logs)

Essas mudanças aumentariam resiliência e observabilidade.

## 6️⃣ O que pode ser mais difícil?

Os principais desafios em sistemas desse tipo são:

- Garantir inferências clínicas responsáveis a partir de textos ambíguos
- Evitar overfitting do prompt ao schema
- Lidar com textos muito curtos ou neutros
- Manter compatibilidade com mudanças nas APIs de LLMs
- Balancear rigor clínico com taxa de sucesso do pipeline

Esses desafios exigem decisões éticas e técnicas cuidadosas.

📌 Este projeto foi desenvolvido como um case técnico, com foco em clareza, robustez e responsabilidade no uso de modelos de linguagem.
