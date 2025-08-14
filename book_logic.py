# -*- coding: utf-8 -*-
import re
from gemini_api_utils import chamar_api_gemini
from file_utils import salvar_progresso_livro_json

# --- Funções de Geração de Conteúdo (Não Interativas) ---

def generate_outline(theme):
    """Gera um esboço de livro para um dado tema."""
    prompt = f"Estou planejando um livro sobre '{theme}'. Pesquise e liste os principais tópicos, subtemas e áreas importantes que poderiam ser abordados em um livro sobre este tema. Apresente como um relatório conciso em formato de lista numerada ou com marcadores."
    return chamar_api_gemini(prompt, tipo_agente="pesquisa_esboco")

def generate_detailed_summary(outline, theme):
    """Gera um resumo detalhado com base no esboço e no tema."""
    prompt = f"Com base no seguinte esboço aprovado para um livro sobre '{theme}': \n{outline}\nCrie um resumo detalhado e coeso do que será abordado no livro. Este resumo servirá como contexto principal para a criação dos capítulos."
    return chamar_api_gemini(prompt, tipo_agente="escritor")

def suggest_titles(summary, theme):
    """Sugere títulos de livros com base no resumo e tema."""
    prompt = f"Sugira 5 títulos criativos para um livro com o tema '{theme}' e resumo: \n'{summary}'. Liste apenas os títulos, um por linha."
    suggestions_raw = chamar_api_gemini(prompt, tipo_agente="geral")
    if "ERRO_API" in suggestions_raw:
        return []
    return [re.sub(r"^\d+\.\s*", "", t.strip()) for t in suggestions_raw.split('\n') if t.strip()]

def suggest_chapter_titles(summary, chapter_count, book_title):
    """Sugere títulos de capítulos."""
    prompt = (f"Para o livro '{book_title}' ({chapter_count} capítulos, resumo: '{summary}'), "
              f"sugira um título conciso para cada um dos {chapter_count} capítulos. Liste um por linha, sem numeração.")
    suggestions_raw = chamar_api_gemini(prompt, tipo_agente="geral")
    if "ERRO_API" in suggestions_raw:
        return [f"Capítulo {i+1}" for i in range(chapter_count)]
    
    suggestions_list = [s.strip() for s in suggestions_raw.split('\n') if s.strip() and not s.lower().startswith("aqui estão")]

    # Garantir a quantidade correta de títulos
    if len(suggestions_list) > chapter_count:
        return suggestions_list[:chapter_count]
    while len(suggestions_list) < chapter_count:
        suggestions_list.append(f"Capítulo {len(suggestions_list) + 1} (Título a definir)")
        
    return suggestions_list

def suggest_target_audience(summary, book_title):
    """Sugere o público-alvo para o livro."""
    prompt = (f"Para o livro '{book_title}' (contexto: '{summary}'), "
              "descreva em uma ou duas frases o público-alvo ideal.")
    return chamar_api_gemini(prompt, tipo_agente="geral")

def generate_additional_section(section_type, plan):
    """Gera o conteúdo para uma seção adicional (ex: Introdução)."""
    prompt = (f"Para o livro '{plan['titulo_livro']}' com o tema '{plan['tema_livro']}' e público-alvo '{plan['publico_alvo']}', "
              f"escreva uma {section_type} concisa e apropriada. "
              f"Contexto geral do livro: {plan['contexto_geral_livro']}")
    return chamar_api_gemini(prompt, tipo_agente="escritor_secao")

def create_chapter(chapter_plan, book_plan, previous_chapters_context):
    """
    Cria o conteúdo de um único capítulo de forma autônoma.
    Retorna o dicionário de dados do capítulo.
    """
    numero_capitulo = chapter_plan['numero']
    titulo_cap_atual = chapter_plan['titulo']

    # 1. Pesquisa de Conteúdo
    prompt_pesquisa_cap = (
        f"Para o capítulo '{titulo_cap_atual}' (Cap. {numero_capitulo}) do livro '{book_plan['titulo_livro']}' "
        f"(público-alvo: {book_plan['publico_alvo']}), cujo tema geral é '{book_plan['contexto_geral_livro']}', "
        f"e considerando o seguinte contexto de capítulos anteriores: {previous_chapters_context}. "
        "Pesquise e forneça os principais pontos, informações relevantes, dados e conceitos a serem abordados neste capítulo específico. Seja detalhado e forneça material substancial."
    )
    conteudo_pesquisado = chamar_api_gemini(prompt_pesquisa_cap, tipo_agente="pesquisa_capitulo")
    if "ERRO_API" in conteudo_pesquisado:
        conteudo_pesquisado = "Erro ao pesquisar conteúdo para este capítulo."

    # 2. Escrita do Capítulo
    prompt_escrita = (
        f"Aja como um escritor especialista no tema do livro '{book_plan['titulo_livro']}'. "
        f"Escreva o conteúdo completo do capítulo '{titulo_cap_atual}'. "
        f"O público-alvo é: {book_plan['publico_alvo']}. "
        f"Baseie-se no seguinte material/tópicos: \n'{conteudo_pesquisado}'.\n"
        f"O capítulo deve ter entre {book_plan['min_paragrafos']} e {book_plan['max_paragrafos']} parágrafos. "
        f"Mantenha um tom adequado. Considere o contexto dos capítulos anteriores ({previous_chapters_context}) para fluidez.\n"
        "Foque em clareza e coesão. Não adicione 'Neste capítulo...' a menos que seja natural."
    )
    texto_capitulo_gerado = chamar_api_gemini(prompt_escrita, tipo_agente="escritor")
    if "ERRO_API" in texto_capitulo_gerado:
        texto_capitulo_gerado = "Erro ao gerar o texto para este capítulo."

    # 3. Revisão do Capítulo
    prompt_revisao = (
        f"Revise o texto do capítulo '{titulo_cap_atual}' (livro: '{book_plan['titulo_livro']}') "
        f"quanto à gramática (Português), coesão e clareza. Texto para revisão: \n'{texto_capitulo_gerado}'\n"
        "Forneça apenas a versão revisada do texto."
    )
    texto_revisado = chamar_api_gemini(prompt_revisao, tipo_agente="revisor")
    if "ERRO_API" in texto_revisado or len(texto_revisado) < 20: # Heurística simples para detectar falha na revisão
        texto_final = texto_capitulo_gerado
    else:
        texto_final = texto_revisado

    # 4. Resumo do Capítulo para Contexto Futuro
    prompt_resumo_cap = (
        f"Resuma os pontos principais do capítulo '{titulo_cap_atual}' em 2-3 frases. "
        f"Contexto do capítulo:\n{texto_final}"
    )
    resumo_cap_atual = chamar_api_gemini(prompt_resumo_cap, tipo_agente="geral")
    if "ERRO_API" in resumo_cap_atual:
        resumo_cap_atual = f"Resumo do capítulo {numero_capitulo} não pôde ser gerado."

    return {
        "numero": numero_capitulo,
        "titulo": titulo_cap_atual,
        "conteudo_pesquisado_aprovado": conteudo_pesquisado,
        "texto_final": texto_final,
        "resumo_para_contexto": resumo_cap_atual
    }

def finalize_book_with_agent(livro_data_completa, planejamento_completo):
    """
    Executa o agente finalizador para uma revisão holística do livro.
    Retorna o dicionário de dados do livro completo e revisado.
    """
    texto_completo_livro = ""
    for cap_info in livro_data_completa.get('capitulos', []):
        texto_original_cap = cap_info.get('texto_final', '')
        texto_completo_livro += f"--- CAPÍTULO {cap_info['numero']}: {cap_info['titulo']} ---\n"
        texto_completo_livro += f"{texto_original_cap}\n\n"

    if not texto_completo_livro.strip():
        return livro_data_completa # Retorna os dados originais se não houver nada a revisar

    contexto_prompt_final = (
        f"Contexto Geral do Livro (Tema: {planejamento_completo['tema_livro']}, "
        f"Título do Livro: {planejamento_completo['titulo_livro']}, "
        f"Público-Alvo: {planejamento_completo['publico_alvo']}):\n{planejamento_completo['contexto_geral_livro']}"
    )

    prompt_finalizacao_livro_inteiro = (
        f"Você é um editor de livros sênior. Realize uma revisão final e polimento no MANUSCRITO COMPLETO a seguir. "
        f"{contexto_prompt_final}\n\n"
        f"Instruções:\n"
        f"1. Corrija gramática e ortografia (Português).\n"
        f"2. Garanta coesão e coerência global entre os capítulos.\n"
        f"3. Mantenha um tom consistente e apropriado para o público-alvo.\n"
        f"4. Melhore a clareza e elimine redundâncias.\n"
        f"5. **IMPORTANTE**: Retorne o TEXTO COMPLETO E REVISADO, mantendo EXATAMENTE a mesma estrutura de separadores de capítulo (--- CAPÍTULO X: [TÍTULO] ---). Sua resposta deve começar diretamente com '--- CAPÍTULO 1: ...' e terminar após o último capítulo, sem adicionar comentários.\n\n"
        f"TEXTO COMPLETO PARA REVISÃO FINAL:\n{texto_completo_livro}"
    )

    livro_inteiro_revisado = chamar_api_gemini(prompt_finalizacao_livro_inteiro, tipo_agente="finalizador", usar_modelo_finalizacao=True)

    if "ERRO_API" in livro_inteiro_revisado or not livro_inteiro_revisado.strip():
        print("⚠️ Erro ao finalizar o livro com o Agente Finalizador. O conteúdo original será mantido.")
        return livro_data_completa

    # Processar a resposta e atualizar os capítulos
    capitulos_revisados_texto = re.split(r'(?=--- CAPÍTULO \d+:)', livro_inteiro_revisado)
    capitulos_revisados_texto = [cap.strip() for cap in capitulos_revisados_texto if cap.strip()]

    if len(capitulos_revisados_texto) == len(livro_data_completa['capitulos']):
        for i, cap_revisado_completo in enumerate(capitulos_revisados_texto):
            # Extrai apenas o texto, removendo o cabeçalho do capítulo
            texto_apenas = re.sub(r'--- CAPÍTULO \d+:.*?---\n', '', cap_revisado_completo, count=1).strip()
            livro_data_completa['capitulos'][i]['texto_final'] = texto_apenas
        print("✅ Livro revisado e finalizado pelo Agente.")
        return livro_data_completa
    else:
        print(f"⚠️ Erro ao analisar a resposta do Agente Finalizador. O número de capítulos retornado ({len(capitulos_revisados_texto)}) é diferente do esperado ({len(livro_data_completa['capitulos'])}). Conteúdo original mantido.")
        return livro_data_completa
