# -*- coding: utf-8 -*-
import os
import time
from ui_utils import limpar_tela, exibir_cabecalho, exibir_status, obter_confirmacao, obter_input_usuario
from gemini_api_utils import configurar_api_gemini, GEMINI_API_KEY, GEMINI_MODEL_NAME_GERACAO, GEMINI_MODEL_NAME_FINALIZACAO
from file_utils import carregar_dados_livro_json, salvar_progresso_livro_json, listar_projetos, sanitizar_nome_arquivo
from document_generator import DOCX_AVAILABLE, REPORTLAB_AVAILABLE
from book_logic import (
    coletar_tema_livro, definir_esboco_inicial, gerar_resumo_detalhado,
    definir_titulo_livro, definir_quantidade_capitulos, definir_titulos_capitulos,
    definir_publico_alvo, definir_limites_paragrafos, gerar_secao_adicional, criar_capitulos, agente_finalizador
)

def main():
    # Verificar e configurar API Gemini
    if not GEMINI_API_KEY:
        print("⚠️ API Gemini não configurada. O programa funcionará em modo de simulação.")
        if obter_confirmacao("Deseja configurar a API agora? (s/n)", ('s','n')) == 's':
            configurar_api_gemini()
            limpar_tela()
    else:
        print(f"✅ API Gemini configurada. Modelos:\n   - Geração: {GEMINI_MODEL_NAME_GERACAO}\n   - Finalização: {GEMINI_MODEL_NAME_FINALIZACAO}")
        time.sleep(1.5)

    # Gerenciamento de Projetos
    limpar_tela()
    exibir_cabecalho("Gerenciador de Projetos BookCreator")
    dados_livro_existente = None
    nome_projeto_atual = None

    projetos_existentes = listar_projetos()
    if projetos_existentes:
        print("Projetos existentes:")
        for i, nome_proj in enumerate(projetos_existentes):
            print(f"  {i+1}. {nome_proj}")
        print("  0. Criar Novo Projeto")
        
        while True:
            escolha_proj = obter_input_usuario("Digite o número do projeto para carregar ou '0' para criar um novo: ")
            try:
                escolha_num = int(escolha_proj)
                if 0 <= escolha_num <= len(projetos_existentes):
                    if escolha_num == 0:
                        nome_projeto_atual = obter_input_usuario("Digite o nome para o novo projeto: ")
                        break
                    else:
                        nome_projeto_atual = projetos_existentes[escolha_num - 1]
                        dados_livro_existente = carregar_dados_livro_json(nome_projeto_atual)
                        if dados_livro_existente:
                            print(f"\n✅ Projeto '{nome_projeto_atual}' carregado.")
                            time.sleep(1.5)
                        else:
                            # Caso o arquivo .json esteja vazio ou corrompido, mas o nome exista na lista
                            print(f"⚠️  Projeto '{nome_projeto_atual}' encontrado, mas não pôde ser carregado. Iniciando como novo.")
                            dados_livro_existente = None # Garante que começará como novo
                            time.sleep(1.5)
                        break
                else:
                    print("Opção inválida. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")
    else:
        print("Nenhum projeto existente encontrado.")
        nome_projeto_atual = obter_input_usuario("Digite o nome para o novo projeto: ")

    if dados_livro_existente and dados_livro_existente.get("capitulos"):
        print(f"\nℹ️  Continuando o projeto: '{nome_projeto_atual}' (Título do livro: '{dados_livro_existente.get('titulo_livro', 'Sem título')}')")
        if obter_confirmacao("Deseja continuar este livro? (s/n)", ('s','n')) == 's':
            # Carregar dados para continuar
            planejamento_completo = dados_livro_existente.get("planejamento_completo", {})
            livro_data_completa = dados_livro_existente
            # Pular para a fase de criação de capítulos ou finalização se já houver capítulos
            if not livro_data_completa.get("capitulos"):
                print("O projeto carregado não tem capítulos. Iniciando criação de capítulos...")
            # A lógica de pular para a próxima fase relevante será tratada mais abaixo
        else:
            if not obter_confirmacao("Deseja iniciar um novo livro (sobrescrever o projeto atual se tiver o mesmo nome)? (s/n)", ('s','n')) == 's':
                print("👋 Até a próxima!"); return
            print(f"Ok, iniciando um novo livro no projeto '{nome_projeto_atual}'...")
            dados_livro_existente = None # Resetar para novo livro
            time.sleep(1)
    else:
        print(f"\n✨ Iniciando novo livro no projeto: '{nome_projeto_atual}'")
        time.sleep(1)
        dados_livro_existente = None # Garante que é um novo livro

    # Inicializar livro_data_completa para garantir que exista
    livro_data_completa = dados_livro_existente if dados_livro_existente else {"planejamento_completo": {}, "capitulos": [], "secoes_adicionais": {}}
    planejamento_completo = livro_data_completa.get("planejamento_completo", {})

    # Se não carregou um livro existente com planejamento, ou decidiu não continuar, ou quer refazer o planejamento
    refazer_planejamento = False
    if not dados_livro_existente or not planejamento_completo or not dados_livro_existente.get("capitulos"):
        refazer_planejamento = True
    elif obter_confirmacao("Deseja refazer o planejamento inicial deste projeto? (s/n)", ('s','n')) == 's':
        refazer_planejamento = True

    if refazer_planejamento:
        # Fase 1: Planejamento Inicial
        limpar_tela()
        exibir_cabecalho("Planejamento Inicial do Livro")
        tema_livro = coletar_tema_livro()
        esboco_livro = definir_esboco_inicial(tema_livro)
        contexto_geral_livro = gerar_resumo_detalhado(esboco_livro, tema_livro)
        titulo_livro = definir_titulo_livro(contexto_geral_livro, tema_livro)
        qtd_capitulos = definir_quantidade_capitulos()
        titulos_capitulos = definir_titulos_capitulos(contexto_geral_livro, qtd_capitulos, titulo_livro)
        publico_alvo = definir_publico_alvo(contexto_geral_livro, titulo_livro)
        min_paragrafos, max_paragrafos = definir_limites_paragrafos()

        # Consolidar planejamento
        planejamento_completo = {
            "tema_livro": tema_livro, "titulo_livro": titulo_livro,
            "contexto_geral_livro": contexto_geral_livro,
            "titulos_capitulos": titulos_capitulos,
            "publico_alvo": publico_alvo,
            "min_paragrafos": min_paragrafos,
            "max_paragrafos": max_paragrafos
        }
        # Atualizar livro_data_completa com o novo planejamento
        livro_data_completa["planejamento_completo"] = planejamento_completo
        livro_data_completa["capitulos"] = [] # Resetar capítulos se o planejamento for refeito
        livro_data_completa["secoes_adicionais"] = {} # Resetar seções adicionais também
        salvar_progresso_livro_json(livro_data_completa, nome_projeto_atual)
        exibir_status("Planejamento inicial salvo.")
    else:
        # Se carregou e decidiu continuar, usa os dados existentes
        print("\n✅ Usando planejamento existente do projeto.")
        time.sleep(1)

    # Perguntar sobre seções adicionais APÓS o planejamento (novo ou carregado)
    limpar_tela()
    exibir_cabecalho("Seções Adicionais do Livro")
    secoes_adicionais_disponiveis = ["Introdução", "Prefácio", "Apêndice", "Índice Remissivo"]
    secoes_a_criar = livro_data_completa.get("secoes_adicionais", {}) # Carregar existentes

    for secao_nome in secoes_adicionais_disponiveis:
        chave_secao = sanitizar_nome_arquivo(secao_nome)
        acao = 'criar'
        if chave_secao in secoes_a_criar and secoes_a_criar[chave_secao].get("conteudo"):
            if obter_confirmacao(f"Já existe uma seção '{secao_nome}'. Deseja recriá-la? (s/n)", ('s','n')) == 'n':
                print(f"Mantendo seção '{secao_nome}' existente.")
                continue
            acao = 'recriar'
        
        if obter_confirmacao(f"Deseja {acao} a seção de '{secao_nome}'? (s/n)", ('s','n')) == 's':
            # Certificar que planejamento_completo tem dados antes de passar para gerar_secao_adicional
            if not planejamento_completo or not planejamento_completo.get("tema_livro"):
                print(f"⚠️  Planejamento incompleto. Não é possível gerar a seção '{secao_nome}'.")
                continue
            conteudo = gerar_secao_adicional(secao_nome, planejamento_completo, nome_projeto_atual)
            secoes_a_criar[chave_secao] = {"titulo": secao_nome, "conteudo": conteudo}
    
    if secoes_a_criar:
        livro_data_completa["secoes_adicionais"] = secoes_a_criar
        salvar_progresso_livro_json(livro_data_completa, nome_projeto_atual)
        exibir_status("Seções adicionais salvas.")

    # Fase 2: Criação dos Capítulos
    limpar_tela()
    exibir_cabecalho("Modo de Criação dos Capítulos")
    print("\nEscolha o modo de criação dos capítulos:")
    print("1. Modo Interativo (você revisa e aprova cada etapa)")
    print("2. Modo Autônomo (IA toma decisões automaticamente)")
    modo_autonomo = obter_confirmacao("Usar modo autônomo? (s/n)", ('s','n')) == 's'
    
    livro_data_completa = criar_capitulos(planejamento_completo, modo_autonomo, nome_projeto_atual, livro_data_completa.get("capitulos", []))
    # Certificar que secoes_adicionais está no livro_data_completa para o agente finalizador e geração de docs
    if "secoes_adicionais" not in livro_data_completa:
        livro_data_completa["secoes_adicionais"] = {}

    # Fase 3: Finalização e Geração de Documentos
    if livro_data_completa and livro_data_completa.get("capitulos"):
        if not any("ERRO" in cap.get("texto_final", "") for cap in livro_data_completa["capitulos"]):
            modelo_formatacao = "padrao"
            if DOCX_AVAILABLE or REPORTLAB_AVAILABLE:
                limpar_tela()
                exibir_cabecalho("Seleção de Modelo de Formatação")
                print("Escolha um modelo de formatação para os documentos:")
                print("1. Padrão")
                print("2. ABNT")
                print("3. Romance Moderno")
                # Adicionar mais modelos aqui conforme implementado em document_generator.py
                while True:
                    escolha_modelo = obter_input_usuario("Digite o número do modelo (ex: 1): ")
                    if escolha_modelo == '1':
                        modelo_formatacao = "padrao"
                        break
                    elif escolha_modelo == '2':
                        modelo_formatacao = "abnt"
                        break
                    elif escolha_modelo == '3':
                        modelo_formatacao = "romance_moderno"
                        break
                    else:
                        print("Opção inválida. Tente novamente.")

            if GEMINI_API_KEY and obter_confirmacao("\nDeseja executar o Agente Finalizador para revisão geral e geração dos documentos? (s/n)", ('s','n')) == 's':
                agente_finalizador(livro_data_completa, planejamento_completo, nome_projeto_atual) # O agente finalizador agora salva, não gera docs
            else:
                print("\nℹ️  Agente Finalizador pulado. Gerando arquivos com o conteúdo atual...")
            
            # Geração de documentos movida para depois do agente finalizador ou da decisão de pulá-lo
            # nome_base = sanitizar_nome_arquivo(livro_data_completa.get('titulo_livro', nome_projeto_atual))
            nome_base_sanitizado = sanitizar_nome_arquivo(nome_projeto_atual) # Usar nome do projeto para o arquivo
            if DOCX_AVAILABLE:
                from document_generator import gerar_arquivo_docx
                gerar_arquivo_docx(livro_data_completa, nome_base_sanitizado, modelo_formatacao)
            if REPORTLAB_AVAILABLE:
                from document_generator import gerar_arquivo_pdf
                gerar_arquivo_pdf(livro_data_completa, nome_base_sanitizado, modelo_formatacao)
        else:
            print("\n❌ Alguns capítulos contêm erros. Revise-os antes de finalizar ou gerar documentos.")
    else:
        print("\n⚠️ Nenhum capítulo foi criado ou o processo foi cancelado.")

    print("\n👋 Processo finalizado. Até a próxima!")

if __name__ == "__main__":
    # Verificar bibliotecas essenciais
    missing_libs = []
    try: import google.generativeai
    except ImportError: missing_libs.append("google-generativeai")
    try: import docx
    except ImportError: missing_libs.append("python-docx")
    try: import reportlab
    except ImportError: missing_libs.append("reportlab")

    if missing_libs:
        print("⚠️ Algumas bibliotecas essenciais não estão instaladas:")
        print("   " + ", ".join(missing_libs))
        print("\nPara instalar, execute:\npip install " + " ".join(missing_libs))
        print("\nO programa funcionará com funcionalidades limitadas.")
        if not obter_confirmacao("\nDeseja continuar mesmo assim? (s/n)", ('s','n')) == 's':
            print("👋 Até a próxima!"); exit()

    main()