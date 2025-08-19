# -*- coding: utf-8 -*-
import os
import re
import time

try:
    import google.generativeai as genai
    GEMINI_API_AVAILABLE = True
except ImportError:
    GEMINI_API_AVAILABLE = False

from ui_utils import exibir_cabecalho, obter_input_usuario, exibir_status

# --- Variáveis Globais de Configuração da IA ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME_GERACAO = None
GEMINI_MODEL_NAME_FINALIZACAO = None
GENERATIVE_MODEL_INSTANCE_GERACAO = None
GENERATIVE_MODEL_INSTANCE_FINALIZACAO = None

MODELOS_GEMINI_SUGERIDOS = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-1.0-pro",
]

def _criar_instancia_modelo(model_name):
    """Cria uma instância de modelo generativo com configurações de segurança."""
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        return genai.GenerativeModel(model_name, safety_settings=safety_settings)
    except Exception as e:
        print(f"❌ Erro ao criar instância do modelo '{model_name}': {e}")
        return None

def configurar_api_gemini():
    """Configura a API Key e os modelos Gemini a serem utilizados."""
    global GEMINI_API_KEY, GEMINI_MODEL_NAME_GERACAO, GEMINI_MODEL_NAME_FINALIZACAO
    global GENERATIVE_MODEL_INSTANCE_GERACAO, GENERATIVE_MODEL_INSTANCE_FINALIZACAO

    if not GEMINI_API_AVAILABLE:
        print("❌ API Gemini não está disponível (biblioteca não instalada). Não é possível configurar.")
        return False

    exibir_cabecalho("Configuração da API Gemini")
    print("Você precisará de uma API Key do Google AI Studio (https://aistudio.google.com/app/apikey).")
    
    if os.getenv("GEMINI_API_KEY"):
        print("ℹ️  API Key encontrada na variável de ambiente GEMINI_API_KEY.")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    else:
        GEMINI_API_KEY = obter_input_usuario("Por favor, insira sua API Key do Gemini:")

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ API Key configurada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao configurar a API Key: {e}")
        print("   Por favor, verifique sua API Key e tente novamente.")
        return False

    print("\n--- Seleção de Modelo para Geração de Conteúdo (Capítulos) ---")
    print("Modelos Gemini sugeridos:")
    for i, modelo in enumerate(MODELOS_GEMINI_SUGERIDOS):
        print(f"  {i+1}. {modelo}")
    print(f"  {len(MODELOS_GEMINI_SUGERIDOS)+1}. Digitar outro nome de modelo")

    while True:
        escolha_modelo_str = obter_input_usuario(f"Escolha o modelo para GERAÇÃO (1-{len(MODELOS_GEMINI_SUGERIDOS)+1}):")
        try:
            escolha_modelo = int(escolha_modelo_str)
            if 1 <= escolha_modelo <= len(MODELOS_GEMINI_SUGERIDOS):
                GEMINI_MODEL_NAME_GERACAO = MODELOS_GEMINI_SUGERIDOS[escolha_modelo-1]
                break
            elif escolha_modelo == len(MODELOS_GEMINI_SUGERIDOS)+1:
                GEMINI_MODEL_NAME_GERACAO = obter_input_usuario("Digite o nome do modelo Gemini para GERAÇÃO (ex: 'gemini-1.5-flash-latest'):")
                break
            else:
                print(f"❌ Escolha inválida.")
        except ValueError:
            print(f"❌ Entrada inválida. Por favor, digite um número.")
            
    GENERATIVE_MODEL_INSTANCE_GERACAO = _criar_instancia_modelo(GEMINI_MODEL_NAME_GERACAO)
    if not GENERATIVE_MODEL_INSTANCE_GERACAO: return False
    print(f"✅ Modelo para GERAÇÃO '{GEMINI_MODEL_NAME_GERACAO}' selecionado.")

    print("\n--- Seleção de Modelo para Finalização e Revisão Geral (Agente Finalizador) ---")
    if obter_input_usuario("Deseja usar um modelo DIFERENTE (potencialmente mais robusto como gemini-1.5-pro-latest) para a finalização? (s/n - para usar '{GEMINI_MODEL_NAME_GERACAO}')", opcoes_validas_lista=['s','n']) == 's':
        print("Modelos Gemini sugeridos (geralmente um modelo 'pro' é bom para revisão):")
        for i, modelo in enumerate(MODELOS_GEMINI_SUGERIDOS):
            print(f"  {i+1}. {modelo}")
        print(f"  {len(MODELOS_GEMINI_SUGERIDOS)+1}. Digitar outro nome de modelo")
        while True:
            escolha_modelo_str = obter_input_usuario(f"Escolha o modelo para FINALIZAÇÃO (1-{len(MODELOS_GEMINI_SUGERIDOS)+1}):")
            try:
                escolha_modelo = int(escolha_modelo_str)
                if 1 <= escolha_modelo <= len(MODELOS_GEMINI_SUGERIDOS):
                    GEMINI_MODEL_NAME_FINALIZACAO = MODELOS_GEMINI_SUGERIDOS[escolha_modelo-1]
                    break
                elif escolha_modelo == len(MODELOS_GEMINI_SUGERIDOS)+1:
                    GEMINI_MODEL_NAME_FINALIZACAO = obter_input_usuario("Digite o nome do modelo Gemini para FINALIZAÇÃO (ex: 'gemini-1.5-pro-latest'):")
                    break
                else:
                    print(f"❌ Escolha inválida.")
            except ValueError:
                print(f"❌ Entrada inválida. Por favor, digite um número.")
    else:
        GEMINI_MODEL_NAME_FINALIZACAO = GEMINI_MODEL_NAME_GERACAO
    
    GENERATIVE_MODEL_INSTANCE_FINALIZACAO = _criar_instancia_modelo(GEMINI_MODEL_NAME_FINALIZACAO)
    if not GENERATIVE_MODEL_INSTANCE_FINALIZACAO: return False
    print(f"✅ Modelo para FINALIZAÇÃO '{GEMINI_MODEL_NAME_FINALIZACAO}' selecionado.")
    
    return True

def chamar_api_gemini(prompt_para_ia, tipo_agente="geral", usar_modelo_finalizacao=False):
    """
    Chama a API Gemini real para gerar conteúdo.
    Permite escolher entre o modelo de geração e o de finalização.
    """
    global GENERATIVE_MODEL_INSTANCE_GERACAO, GENERATIVE_MODEL_INSTANCE_FINALIZACAO
    global GEMINI_MODEL_NAME_GERACAO, GEMINI_MODEL_NAME_FINALIZACAO

    modelo_a_usar = None
    nome_modelo_em_uso = ""

    if usar_modelo_finalizacao and GENERATIVE_MODEL_INSTANCE_FINALIZACAO:
        modelo_a_usar = GENERATIVE_MODEL_INSTANCE_FINALIZACAO
        nome_modelo_em_uso = GEMINI_MODEL_NAME_FINALIZACAO
    elif GENERATIVE_MODEL_INSTANCE_GERACAO:
        modelo_a_usar = GENERATIVE_MODEL_INSTANCE_GERACAO
        nome_modelo_em_uso = GEMINI_MODEL_NAME_GERACAO
    
    if not GEMINI_API_AVAILABLE or modelo_a_usar is None:
        exibir_status(f"[SIMULAÇÃO - API INDISPONÍVEL/MODELO NÃO CONFIGURADO] [AGENTE {tipo_agente.upper()}] Processando solicitação...")
        return simular_resposta_fallback(prompt_para_ia, tipo_agente)

    exibir_status(f"[AGENTE {tipo_agente.upper()}] Enviando solicitação para o modelo '{nome_modelo_em_uso}'...", delay=1)
    
    try:
        response = modelo_a_usar.generate_content(prompt_para_ia)
        
        if hasattr(response, 'text'):
            return response.text
        elif response.parts:
            return "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason
            print(f"❌ A solicitação foi bloqueada pela API. Razão: {block_reason}")
            if response.prompt_feedback.safety_ratings:
                 for rating in response.prompt_feedback.safety_ratings:
                    print(f"   - Categoria: {rating.category}, Probabilidade: {rating.probability.name if hasattr(rating.probability, 'name') else rating.probability}")
            return f"ERRO_API: Solicitação bloqueada ({block_reason})."
        else:
            try:
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            except (AttributeError, IndexError): pass
            print(f"❌ A API Gemini retornou uma resposta inesperada. Resposta: {response}")
            return "ERRO_API: Resposta vazia ou inesperada."
    except Exception as e:
        print(f"❌ Erro durante a chamada à API Gemini: {e}")
        return f"ERRO_API: {e}."

def simular_resposta_fallback(prompt_para_ia, tipo_agente):
    """Fornece respostas simuladas se a API real não puder ser usada."""
    time.sleep(1)
    if "pesquisar os principais tópicos" in prompt_para_ia.lower() or tipo_agente == "pesquisa_esboco":
        return ("Relatório de Tópicos Sugeridos (Simulado):\n1. Introdução\n2. Desenvolvimento\n3. Conclusão")
    elif "pesquisar conteúdo para o capítulo" in prompt_para_ia.lower() or tipo_agente == "pesquisa_capitulo":
        return ("Conteúdo pesquisado simulado para o capítulo:\n- Ponto chave A\n- Ponto chave B")
    elif "escrever o conteúdo do capítulo" in prompt_para_ia.lower() or tipo_agente == "escritor":
        return ("Este é um parágrafo simulado gerado como fallback. A API Gemini não está configurada.")
    elif "revise o seguinte texto do capítulo" in prompt_para_ia.lower() or tipo_agente == "finalizador" or "TEXTO COMPLETO PARA REVISÃO FINAL" in prompt_para_ia:
        texto_original_match = re.search(r"TEXTO COMPLETO PARA REVISÃO FINAL:\n(.*?)$", prompt_para_ia, re.DOTALL)
        if texto_original_match:
            texto_original = texto_original_match.group(1).strip()
            return f"{texto_original}\n\n(Nota: Esta é uma revisão simulada. O texto foi retornado como estava.)"
        return "Texto (simuladamente) revisado e finalizado. (Nota: Revisão simulada sem extração de original)."
    else:
        return "Resposta simulada genérica (API não disponível)."