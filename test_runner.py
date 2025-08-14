import os
import time
from book_logic import (
    generate_outline, generate_detailed_summary, suggest_titles,
    suggest_chapter_titles, suggest_target_audience, generate_additional_section,
    create_chapter, finalize_book_with_agent
)
from gemini_api_utils import configurar_api_gemini
from file_utils import salvar_progresso_livro_json, sanitizar_nome_arquivo
from document_generator import gerar_arquivo_docx, gerar_arquivo_pdf, DOCX_AVAILABLE, REPORTLAB_AVAILABLE

def run_test():
    """
    Executes a non-interactive, end-to-end test of the book creation logic.
    """
    print("--- INICIANDO TESTE E2E DO BOOK CREATOR ---")

    # Etapa 0: Configuração
    # A API Key já deve estar configurada via variável de ambiente.
    # A função configurar_api_gemini() agora é chamada para selecionar os modelos.
    # Para o teste, vamos pular a seleção interativa e assumir modelos padrão.
    # Esta parte será tratada de forma diferente na UI web.
    print("\n[ETAPA 0] Configurando a API e Modelos (simulado)...")
    try:
        configurar_api_gemini()
        print("Configuração da API bem-sucedida (usando variáveis de ambiente e/ou padrões).")
    except Exception as e:
        print(f"Falha na configuração da API: {e}")
        # Em um teste real, poderíamos mockar isso, mas aqui vamos tentar usar a API real.
        pass

    # Etapa 1: Planejamento
    print("\n[ETAPA 1] Iniciando a fase de planejamento...")

    project_name = "Teste_Automatizado_Ciencia_de_Dados"
    tema_livro = "Introdução à Ciência de Dados para iniciantes"
    print(f"  - Tema: {tema_livro}")

    esboco = generate_outline(tema_livro)
    print(f"  - Esboço gerado.")
    time.sleep(1)

    resumo = generate_detailed_summary(esboco, tema_livro)
    print(f"  - Resumo detalhado gerado.")
    time.sleep(1)

    titulos_sugeridos = suggest_titles(resumo, tema_livro)
    titulo_livro = titulos_sugeridos[0] if titulos_sugeridos else "Título Provisório Gerado Automaticamente"
    print(f"  - Título escolhido: {titulo_livro}")
    time.sleep(1)

    qtd_capitulos = 1 # Reduzido para 1 para um teste mais rápido
    titulos_capitulos = suggest_chapter_titles(resumo, qtd_capitulos, titulo_livro)
    print(f"  - Títulos de {qtd_capitulos} capítulos gerados.")
    time.sleep(1)

    publico_alvo = suggest_target_audience(resumo, titulo_livro)
    print(f"  - Público-alvo sugerido.")
    time.sleep(1)

    planejamento_completo = {
        "tema_livro": tema_livro,
        "titulo_livro": titulo_livro,
        "contexto_geral_livro": resumo,
        "titulos_capitulos": titulos_capitulos,
        "publico_alvo": publico_alvo,
        "min_paragrafos": 2, # Reduzido para teste
        "max_paragrafos": 3, # Reduzido para teste
    }
    print("  - Fase de planejamento concluída.")

    # Etapa 2: Seções Adicionais
    print("\n[ETAPA 2] Gerando seções adicionais...")
    livro_data_completa = {
        "planejamento_completo": planejamento_completo,
        "capitulos": [],
        "secoes_adicionais": {}
    }

    intro_content = generate_additional_section("Introdução", planejamento_completo)
    livro_data_completa["secoes_adicionais"]["introducao"] = {"titulo": "Introdução", "conteudo": intro_content}
    print("  - Introdução gerada.")
    time.sleep(1)

    # Etapa 3: Criação dos Capítulos
    print("\n[ETAPA 3] Iniciando a criação de capítulos...")
    previous_chapters_context = "Este é o primeiro capítulo."

    for i, titulo_cap in enumerate(planejamento_completo['titulos_capitulos']):
        print(f"  - Criando Capítulo {i+1}: {titulo_cap}...")
        chapter_plan = {"numero": i + 1, "titulo": titulo_cap}

        novo_capitulo = create_chapter(chapter_plan, planejamento_completo, previous_chapters_context)
        livro_data_completa["capitulos"].append(novo_capitulo)

        # Atualizar o contexto para o próximo capítulo
        previous_chapters_context += "\n" + novo_capitulo['resumo_para_contexto']

        # Salvar progresso a cada capítulo
        salvar_progresso_livro_json(livro_data_completa, project_name)
        print(f"  - Capítulo {i+1} concluído e salvo.")
        time.sleep(1)

    print("  - Todos os capítulos foram criados.")

    # Etapa 4: Finalização
    print("\n[ETAPA 4] Executando o Agente Finalizador...")
    livro_data_final = finalize_book_with_agent(livro_data_completa, planejamento_completo)
    salvar_progresso_livro_json(livro_data_final, f"{project_name}_Finalizado")
    print("  - Livro finalizado e salvo.")

    # Etapa 5: Geração de Documentos
    print("\n[ETAPA 5] Gerando os arquivos finais...")
    nome_base_sanitizado = sanitizar_nome_arquivo(project_name)

    if DOCX_AVAILABLE:
        gerar_arquivo_docx(livro_data_final, nome_base_sanitizado, modelo="padrao")
    else:
        print("  - Geração de DOCX pulada (biblioteca não instalada).")

    if REPORTLAB_AVAILABLE:
        gerar_arquivo_pdf(livro_data_final, nome_base_sanitizado, modelo="padrao")
    else:
        print("  - Geração de PDF pulada (biblioteca não instalada).")

    print("\n--- TESTE E2E CONCLUÍDO COM SUCESSO! ---")

if __name__ == "__main__":
    # Garante que a API Gemini seja configurada antes de qualquer chamada
    # A função em gemini_api_utils foi modificada para não ser interativa se a key já existir
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERRO: A variável de ambiente GEMINI_API_KEY não está definida.")
        print("   Por favor, defina a chave para executar o teste.")
    else:
        run_test()
