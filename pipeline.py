from __future__ import annotations 
from openai import OpenAI
import os
import json 
from pathlib import Path 
from typing import Any, Dict, List, Tuple, Optional, Literal, TypedDict 
 
# Imports obrigatórios para o novo escopo 
try: 
    from pydantic import BaseModel, Field, ValidationError 
    from langgraph.graph import StateGraph, END 
except ImportError: 
    raise ImportError("Dependências ausentes. Instale: pip install pydantic langgraph") 
 
BASE_DIR = Path(__file__).parent 
INPUT_DIR = BASE_DIR / "data" / "input" 
PROMPTS_DIR = BASE_DIR / "prompts" 
OUT_PATH = BASE_DIR / "results.json" 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========================= 
# 1. Pydantic Schemas (Structured Output) 
# ========================= 
 
class RiskAssessment(BaseModel):
    level: Literal["baixo", "médio", "alto"] = Field(
        description="Nível de risco clínico identificado"
    )
    signals: List[str] = Field(
        min_length=1,
        description="Sinais clínicos que justificam o nível de risco"
    )

class ClinicalReport(BaseModel):
    required: bool = Field(
        description="Indica se é necessário um laudo clínico formal"
    )
    summary: str = Field(
        description="Resumo do laudo clínico quando aplicável"
    )

class ClinicalOutput(BaseModel):
    """
    Schema principal que representa a análise clínica completa.
    """

    analysis: str = Field(
        min_length=50,
        description="Análise clínica estruturada do discurso"
    )

    themes: List[str] = Field(
        min_length=3,
        max_length=6,
        description="Temas clínicos identificados no discurso"
    )

    signifiers: List[str] = Field(
        min_length=3,
        max_length=8,
        description="Significantes ou palavras marcantes"
    )

    hypotheses: List[str] = Field(
        min_length=2,
        max_length=4,
        description="Hipóteses clínicas interpretativas"
    )

    questions: List[str] = Field(
        min_length=3,
        max_length=6,
        description="Perguntas clínicas abertas para aprofundamento"
    )

    risk_assessment: RiskAssessment
    clinical_report: ClinicalReport
 
 
# ========================= 
# 2. State Definition 
# ========================= 
 
class ClinicalState(TypedDict): 
    filename: str 
    input_text: str 
    prompt_version: str 
     
    # Resposta crua do modelo (string JSON) 
    raw_response: Optional[str] 
     
    # Objeto validado pelo Pydantic 
    parsed_output: Optional[ClinicalOutput] 
     
    # Lista de erros (parsing ou validação) 
    errors: List[str] 
 
 
# ========================= 
# 3. IO / Prompt Helpers 
# ========================= 
 
def load_prompt(prompt_version: str) -> str: 
    path = PROMPTS_DIR / f"prompt_{prompt_version}.txt" 
    if not path.exists(): 
        # Fallback para teste se arquivo não existir 
        return "Analise o texto: {INPUT}" 
    return path.read_text(encoding="utf-8") 
 
def read_inputs(input_dir: Path) -> List[Tuple[str, str]]:
    """
    Lê arquivos .txt do diretório de entrada.
    Retorna lista de tuplas: (filename, content).
    """
    items: List[Tuple[str, str]] = []

    if not input_dir.exists():
        raise FileNotFoundError(f"Diretório de entrada não encontrado: {input_dir}")

    for path in sorted(input_dir.glob("*.txt")):
        try:
            content = path.read_text(encoding="utf-8").strip()
        except Exception as e:
            # Se falhar leitura, ignora arquivo
            print(f"Erro ao ler {path.name}: {e}")
            continue

        if not content:
            # Ignora arquivos vazios
            continue

        items.append((path.name, content))

    return items
 
 
# ========================= 
# 4. Model Call (Mock or API) 
# ========================= 
 
def call_model(prompt: str) -> str:
    """
    Chamada real à API da OpenAI.

    Retorna uma STRING contendo um JSON que será validado
    posteriormente pelo Pydantic.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.3,
        max_output_tokens=800
    )

    # A Responses API pode retornar múltiplos blocos;
    # usamos a forma segura de extrair texto final
    return response.output_text
 
 
# ========================= 
# 5. LangGraph Nodes 
# ========================= 
 
def generation_node(state: ClinicalState) -> ClinicalState:
    """
    Nó de Geração: Monta prompt e chama o modelo.
    """
    print(f"--- Node: Generation ({state['filename']}) ---")

    try:
        # 1. Carrega o template do prompt
        template = load_prompt(state["prompt_version"])

        # 2. Injeta o texto clínico
        prompt = template.replace("{INPUT}", state["input_text"])

        # 3. Chama o modelo (mock ou API)
        response = call_model(prompt)

        return {
            "raw_response": response
        }

    except Exception as e:
        # Erro na geração não quebra o pipeline
        return {
            "raw_response": None,
            "errors": state.get("errors", []) + [f"Generation Error: {str(e)}"]
        }
 
 
def validation_node(state: ClinicalState) -> ClinicalState: 
    """ 
    Nó de Validação: Usa Pydantic para validar o JSON cru. 
    """ 
    print("--- Node: Validation ---") 
     
    raw = state.get("raw_response", "") 
    errors = [] 
    parsed_obj = None 
 
    try: 
        # A mágica do Pydantic acontece aqui: 
        # Ele faz o parse E valida tipos/regras definidos na classe ClinicalOutput 
        parsed_obj = ClinicalOutput.model_validate_json(raw) 
         
    except ValidationError as e: 
        # Captura erros de validação estrutural (ex: lista muito curta, tipo errado) 
        errors = [f"Validation Error: {err['msg']} at {err['loc']}" for err in 
e.errors()] 
         
    except json.JSONDecodeError as e: 
        errors = [f"JSON Parse Error: {str(e)}"] 
         
    except Exception as e: 
        errors = [f"Unknown Error: {str(e)}"] 
 
    return { 
        "parsed_output": parsed_obj, 
        "errors": errors 
    } 
 
 
# ========================= 
# 6. Graph Construction 
# ========================= 
 
def build_graph() -> StateGraph: 
    workflow = StateGraph(ClinicalState) 
     
    # Adiciona nós 
    workflow.add_node("generator", generation_node) 
    workflow.add_node("validator", validation_node) 
     
    # Define fluxo linear 
    workflow.set_entry_point("generator") 
    workflow.add_edge("generator", "validator") 
    workflow.add_edge("validator", END) 
     
    return workflow.compile() 
 
 
def save_results(payload: Dict[str, Any], path: Path) -> None: 
    # Converte o objeto Pydantic para dict antes de salvar, se existir 
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8") 
 
 
# ========================= 
# 7. Main Execution 
# ========================= 
 
def main(prompt_version: str = "v2"): 
    # 1. Leitura 
    try: 
        items = read_inputs(INPUT_DIR) 
    except NotImplementedError: 
        print("Erro: read_inputs não implementado. Usando inputs mockados.") 
        items = [("test_mock.txt", "Texto de exemplo para teste do fluxo.")] 
 
    # 2. Setup do Grafo 
    app = build_graph() 
    results = [] 
    ok_count = 0 
 
    print(f"Iniciando Pipeline (LangGraph + Pydantic) - Prompt {prompt_version}...\n") 
 
    for fname, text in items: 
         
        # Estado Inicial 
        initial_state: ClinicalState = { 
            "filename": fname, 
            "input_text": text, 
            "prompt_version": prompt_version, 
            "raw_response": None, 
            "parsed_output": None, 
            "errors": [] 
        } 
 
        try: 
            # Invoca o grafo 
            final_state = app.invoke(initial_state) 
             
            output_data = final_state["parsed_output"] 
            errors = final_state["errors"] 
             
            # Sucesso se temos objeto validado e zero erros 
            is_ok = (output_data is not None) and (len(errors) == 0) 
             
            if is_ok: 
                ok_count += 1 
                # Converter modelo Pydantic para dict para salvar no JSON final 
                output_dict = output_data.model_dump() 
            else: 
                output_dict = None 
 
            results.append({ 
                "file": fname, 
                "ok": is_ok, 
                "errors": errors, 
                "output": output_dict 
            }) 
             
        except Exception as e: 
            results.append({ 
                "file": fname, 
                "ok": False, 
                "errors": [f"Runtime Error: {e}"], 
                "output": None 
            }) 
 
    # 3. Consolidação 
    payload = { 
        "prompt_version": prompt_version, 
        "total": len(results), 
        "ok": ok_count, 
        "failed": len(results) - ok_count, 
        "results": results, 
    } 
 
    save_results(payload, OUT_PATH) 
    print(f"Processamento concluído. Salvo em {OUT_PATH}") 
    print(f"Sucesso: {ok_count} | Falhas: {len(results) - ok_count}") 
 
 
if __name__ == "__main__": 
    main() 