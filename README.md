<h1 align="center">
  <h1 align="center">IA Clínica de Psicoanálise</h1>
  <br>
</h1>

## 📌 **Sobre o Projeto**
Este projeto implementa um pipeline de análise clínica textual voltado ao contexto de psicologia/psicanálise, utilizando modelos de linguagem (LLMs) para gerar hipóteses, temas, significantes e avaliações de risco a partir de textos livres. O foco principal não é apenas gerar texto, mas garantir consistência estrutural e validação semântica mínima, utilizando Pydantic como camada de verificação clínica.

# ⚙️ Como rodar o projeto

### 1️⃣ Pré-requisitos

- Python **3.10+**
- Conta OpenAI com **billing ativo**
- Dependências:
  - `pydantic`
  - `langgraph`
  - `openai`

Instale as dependências:

```bash
pip install pydantic langgraph openai
```

### 2️⃣ Configurar variável de ambiente

Defina sua chave da OpenAI

```bash
export OPENAI_API_KEY="sua_chave_aqui"
```

Ou no Windows (PowerShell)

```bash
setx OPENAI_API_KEY "sua_chave_aqui"
```

### 3️⃣ Escolher versão do prompt e colocar texto clínico

O prompt ativo é definido no main():

```bash
def main(prompt_version: str = "v2"):
```

Para trocar o prompt, basta alterar o valor de v2 para v1, ou vice-versa.

O programa suporta 2 textos clínicos para análise por vez, coloque eles dentro dos arquivos:

```text
data/input
├── text_1.txt
└── text_2.txt
```

Caso possua apenas 1 texto, deixe o outro arquivo em branco.

### 4️⃣ Executar o pipeline

Rode o comando:

```bash
python pipeline.py
```

Ao final da execução, será gerado o arquivo:

```text
results.json
```

### 🔄 Como funciona o pipeline

O fluxo é implementado com LangGraph, em um grafo linear de dois nós:
```text
[Generation Node] → [Validation Node] → END
```
🔹 1. Generation Node

- Lê o texto de entrada
- Carrega o prompt selecionado
- Chama a OpenAI Responses API
- Retorna uma resposta em formato JSON (string)

🔹 2. Validation Node

- Valida a saída do modelo com Pydantic
- Garante: Tipos corretos, campos obrigatórios, regras mínimas (ex: listas não vazias)
- Se a validação falhar, o erro é registrado de forma explícita

Esse desenho evita falhas silenciosas e impede inferências clínicas a partir de dados insuficientes ou malformados.

### 🧩 Como escolher o prompt
Os prompts ficam no diretório:

```text
prompts/
├── prompt_v1.txt
└── prompt_v2.txt
```

Cada prompt pode definir:
- nível de detalhamento clínico
- estilo da análise
- grau de cautela na avaliação de risco

Isso permite experimentação controlada sem alterar o código. 

As versões dos prompts são melhor explicadas em NOTES.md
## 📊 Como interpretar os resultados
O arquivo results.json possui a seguinte estrutura geral:

```json
{
  "prompt_version": "v2",
  "total": 2,
  "ok": 1,
  "failed": 1,
  "results": [...]
}
```

🔹 Campos principais
- ok: indica se o texto passou todas as validações
- errors: lista de erros estruturais ou clínicos
- output: resultado validado (quando ok = true)

⚠️ Falhas esperadas (importante)
Alguns textos podem falhar na validação, por exemplo:

```text
Validation Error: List should have at least 1 item
at ('risk_assessment', 'signals')
```

Isso significa que o modelo não encontrou sinais clínicos suficientes, o pipeline optou por não inferir risco indevidamente. Esse comportamento é intencional e desejável. O sistema prioriza rigor clínico em vez de forçar inferências a partir de dados pobres.

📌 Este projeto foi desenvolvido como um case técnico, com foco em clareza,
robustez e responsabilidade no uso de modelos de linguagem.
