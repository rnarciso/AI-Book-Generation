# -*- coding: utf-8 -*-
import re
from ui_utils import exibir_cabecalho, exibir_status, obter_input_usuario, obter_confirmacao, limpar_tela
from gemini_api_utils import chamar_api_gemini, GENERATIVE_MODEL_INSTANCE_FINALIZACAO, GEMINI_MODEL_NAME_FINALIZACAO
from file_utils import salvar_progresso_livro_json, sanitizar_nome_arquivo
from document_generator import gerar_arquivo_docx, gerar_arquivo_pdf, DOCX_AVAILABLE, REPORTLAB_AVAILABLE

# --- Fase 1: Coleta de Informações e Planejamento ---

def coletar_tema_livro():
    exibir_cabecalho("Definição do Tema do Livro")
    return obter_input_usuario("Sobre qual tema você gostaria de criar um livro?")

def definir_esboco_inicial(tema_livro):
    exibir_cabecalho("Esboço Inicial do Livro")
    esboco_atual = ""
    while True:
        prompt_esboco = f"Estou planejando um livro sobre '{tema_livro}'. Pesquise e liste os principais tópicos, subtemas e áreas importantes que poderiam ser abordados em um livro sobre este tema. Apresente como um relatório conciso em formato de lista numerada ou com marcadores."
        sugestao_esboco = chamar_api_gemini(prompt_esboco, tipo_agente="pesquisa_esboco")

        print("\nSugestão de esboço gerada pela IA:")
        print("-" * 30); print(sugestao_esboco); print("-" * 30)

        if "ERRO_API" in sugestao_esboco:
            print("⚠️ Não foi possível gerar o esboço via IA. Por favor, insira manualmente.")
            linhas_esboco = []
            print("Digite o esboço do seu livro (tópicos principais, um por linha). Digite 'FIM_ESBOCO' em uma nova linha para terminar.")
            while True:
                linha = input()
                if linha.strip().upper() == 'FIM_ESBOCO': break
                linhas_esboco.append(linha)
            esboco_atual = "\n".join(linhas_esboco)
            if not esboco_atual.strip():
                print("❌ Esboço manual não pode ser vazio. Tente novamente."); continue
            return esboco_atual

        if not esboco_atual: esboco_atual = sugestao_esboco
        confirmacao = obter_confirmacao("Você aprova este esboço? (s/n - para nova sugestão / m - para modificar / a - para adicionar)", ('s','n','m','a'))
        if confirmacao == 's': print("✅ Esboço aprovado!"); return esboco_atual
        elif confirmacao == 'n': esboco_atual = ""; exibir_status("Ok, vamos gerar uma nova sugestão.")
        elif confirmacao == 'm':
            print("\nEdite o esboço. Digite 'FIM_EDICAO' em uma nova linha para terminar.")
            print("-" * 30); print(esboco_atual); print("-" * 30)
            linhas_editadas = []
            while True:
                linha = input()
                if linha.strip().upper() == 'FIM_EDICAO': break
                linhas_editadas.append(linha)
            esboco_atual = "\n".join(linhas_editadas)
            print("✅ Esboço modificado.")
            reconfirm = obter_confirmacao(f"Este é o esboço final?\n---\n{esboco_atual}\n---\n(s/n - para editar mais)", ('s','n'))
            if reconfirm == 's': print("✅ Esboço final aprovado!"); return esboco_atual
        elif confirmacao == 'a':
            adicao = obter_input_usuario("O que você gostaria de adicionar ao esboço atual?")
            esboco_atual += f"\n- {adicao} (Adicionado pelo usuário)"
            print("✅ Item adicionado. Esboço atualizado:"); print("-" * 30); print(esboco_atual); print("-" * 30)

def gerar_resumo_detalhado(esboco_livro, tema_livro):
    exibir_cabecalho("Resumo Detalhado do Livro")
    prompt_resumo = f"Com base no seguinte esboço aprovado para um livro sobre '{tema_livro}': \n{esboco_livro}\nCrie um resumo detalhado e coeso do que será abordado no livro. Este resumo servirá como contexto principal para a criação dos capítulos."
    resumo = chamar_api_gemini(prompt_resumo, tipo_agente="escritor")
    print("\nResumo Detalhado Gerado:"); print("-" * 30); print(resumo); print("-" * 30)

    if "ERRO_API" in resumo:
        print("⚠️ Não foi possível gerar o resumo via IA.")
        if obter_confirmacao("Deseja inserir um resumo manualmente? (s/n)", ('s','n')) == 's':
            linhas_resumo = []
            print("Digite o resumo. Digite 'FIM_RESUMO' em uma nova linha para terminar.")
            while True:
                linha = input()
                if linha.strip().upper() == 'FIM_RESUMO': break
                linhas_resumo.append(linha)
            resumo = "\n".join(linhas_resumo)
            if not resumo.strip(): return "Resumo manual não fornecido."
        else: return "Resumo não gerado devido a erro da API."

    if obter_confirmacao("Você aprova este resumo detalhado?", ('s','n')) == 's':
        print("✅ Resumo detalhado aprovado!"); return resumo
    else:
        print("ℹ️  Resumo não aprovado. Usaremos este como base."); return resumo

def definir_titulo_livro(contexto_geral_livro, tema_livro):
    exibir_cabecalho("Título do Livro")
    if obter_confirmacao("Gostaria que a IA gerasse sugestões de título?", ('s','n')) == 's':
        prompt_titulos = f"Sugira 5 títulos criativos para um livro com o tema '{tema_livro}' e resumo: \n'{contexto_geral_livro}'. Liste apenas os títulos, um por linha."
        sugestoes_raw = chamar_api_gemini(prompt_titulos, tipo_agente="geral")
        
        if "ERRO_API" in sugestoes_raw: print("⚠️ Não foi possível gerar sugestões de título via IA.")
        else:
            print("\nSugestões de Título:"); print("-" * 30); print(sugestoes_raw); print("-" * 30)
            titulos_lista = [re.sub(r"^\d+\.\s*", "", t.strip()) for t in sugestoes_raw.split('\n') if t.strip()]

            while True:
                if not titulos_lista: print("ℹ️ Nenhuma sugestão válida da IA."); break
                escolha_str = obter_input_usuario(f"Digite o número do título (1-{len(titulos_lista)} ou '0' para inserir o seu):")
                try:
                    escolha = int(escolha_str)
                    if 0 <= escolha <= len(titulos_lista):
                        if escolha == 0: titulo_final = obter_input_usuario("Digite o título do seu livro:")
                        else: titulo_final = titulos_lista[escolha - 1]
                        print(f"✅ Título definido: '{titulo_final}'"); return titulo_final
                    else: print(f"❌ Escolha inválida.")
                except ValueError: print("❌ Por favor, digite um número.")
    
    titulo_final = obter_input_usuario("Digite o título do seu livro:")
    print(f"✅ Título definido: '{titulo_final}'"); return titulo_final

def definir_quantidade_capitulos():
    exibir_cabecalho("Quantidade de Capítulos")
    return obter_input_usuario("Quantos capítulos o livro terá?", tipo_esperado=int, validacao_func=lambda x: x > 0, erro_msg="Deve ser maior que zero.")

def definir_titulos_capitulos(contexto_geral_livro, qtd_capitulos, titulo_livro):
    exibir_cabecalho("Títulos dos Capítulos")
    while True:
        prompt_tit_caps = (f"Para o livro '{titulo_livro}' ({qtd_capitulos} capítulos, resumo: '{contexto_geral_livro}'), "
                           f"sugira um título conciso para cada um dos {qtd_capitulos} capítulos. Liste um por linha, sem numeração.")
        sugestoes_raw = chamar_api_gemini(prompt_tit_caps, tipo_agente="geral")
        
        if "ERRO_API" in sugestoes_raw:
            print("⚠️ Não foi possível gerar títulos de capítulo via IA. Insira manualmente.")
            sugestoes_lista = [obter_input_usuario(f"Título para Capítulo {i+1}:") for i in range(qtd_capitulos)]
            return sugestoes_lista

        sugestoes_lista = [s.strip() for s in sugestoes_raw.split('\n') if s.strip() and not s.lower().startswith("aqui estão")]
        
        if len(sugestoes_lista) != qtd_capitulos:
            print(f"⚠️ IA sugeriu {len(sugestoes_lista)} títulos, pedimos {qtd_capitulos}. Ajustando/Completando...")
            if len(sugestoes_lista) > qtd_capitulos: sugestoes_lista = sugestoes_lista[:qtd_capitulos]
            else:
                for i in range(len(sugestoes_lista), qtd_capitulos):
                    sugestoes_lista.append(obter_input_usuario(f"Título para Capítulo {i+1} (faltante):"))
        
        print("\nSugestões de Títulos:"); print("-" * 30)
        for i, titulo_cap in enumerate(sugestoes_lista): print(f"{i+1}. {titulo_cap}"); print("-" * 30)

        confirmacao = obter_confirmacao("Aprova esta lista de títulos? (s/n - nova sugestão / m - modificar)", ('s','n','m'))
        if confirmacao == 's': print("✅ Títulos aprovados!"); return sugestoes_lista
        elif confirmacao == 'n': exibir_status("Ok, gerando nova lista...")
        elif confirmacao == 'm':
            titulos_finais_mod = list(sugestoes_lista)
            for i in range(len(titulos_finais_mod)):
                novo_titulo_cap = obter_input_usuario(f"Capítulo {i+1} (Enter para manter '{titulos_finais_mod[i]}'):")
                if novo_titulo_cap: titulos_finais_mod[i] = novo_titulo_cap
            print("✅ Títulos modificados."); return titulos_finais_mod

def definir_publico_alvo(contexto_geral_livro, titulo_livro):
    exibir_cabecalho("Público-Alvo do Livro")
    prompt_publico = (f"Para o livro '{titulo_livro}' (contexto: '{contexto_geral_livro}'), "
                      "liste exemplos de público-alvo em marcadores.")
    sugestoes = chamar_api_gemini(prompt_publico, tipo_agente="geral")
    
    if "ERRO_API" not in sugestoes: print("\nExemplos de Público-Alvo da IA:"); print("-" * 30); print(sugestoes); print("-" * 30)
    else: print("⚠️ Não foi possível obter sugestões de público-alvo da IA.")
    return obter_input_usuario("Qual o público-alvo principal do seu livro? (Descreva brevemente)")

def definir_limites_paragrafos():
    exibir_cabecalho("Limites de Parágrafos por Capítulo")
    min_p = obter_input_usuario("MÍNIMO de parágrafos por capítulo?", tipo_esperado=int, validacao_func=lambda x: x > 0, erro_msg="Mínimo > 0.")
    while True:
        max_p = obter_input_usuario("MÁXIMO de parágrafos por capítulo?", tipo_esperado=int, validacao_func=lambda x: x >= min_p, erro_msg=f"Máximo >= {min_p}.")
        if max_p >= min_p: return min_p, max_p
        else: print(f"❌ Máximo ({max_p}) não pode ser menor que mínimo ({min_p}).")

# --- Seções Adicionais (Opcional) ---
def gerar_secao_adicional(tipo_secao, planejamento_completo, nome_projeto):
    exibir_cabecalho(f"Geração da Seção: {tipo_secao}")
    prompt = f"Para o livro '{planejamento_completo['titulo_livro']}' com o tema '{planejamento_completo['tema_livro']}' e público-alvo '{planejamento_completo['publico_alvo']}', escreva uma {tipo_secao} concisa e apropriada. Contexto geral do livro: {planejamento_completo['contexto_geral_livro']}"
    conteudo_secao = chamar_api_gemini(prompt, tipo_agente="escritor_secao")

    if "ERRO_API" in conteudo_secao:
        print(f"⚠️ Não foi possível gerar a {tipo_secao} via IA.")
        if obter_confirmacao(f"Deseja inserir o conteúdo da {tipo_secao} manualmente? (s/n)", ('s','n')) == 's':
            linhas_secao = []
            print(f"Digite o conteúdo da {tipo_secao}. Digite 'FIM_SECAO' em uma nova linha para terminar.")
            while True:
                linha = input()
                if linha.strip().upper() == 'FIM_SECAO': break
                linhas_secao.append(linha)
            conteudo_secao = "\n".join(linhas_secao)
            if not conteudo_secao.strip(): conteudo_secao = f"{tipo_secao} não fornecida."
        else:
            conteudo_secao = f"{tipo_secao} não gerada devido a erro da API."
    else:
        print(f"\n{tipo_secao} Gerada:"); print("-" * 30); print(conteudo_secao); print("-" * 30)
        if obter_confirmacao(f"Você aprova esta {tipo_secao}? (s/n)", ('s','n')) != 's':
            # Permitir edição simples
            print(f"\nEdite a {tipo_secao}. Digite 'FIM_EDICAO' em uma nova linha para terminar.")
            print("-" * 30); print(conteudo_secao); print("-" * 30)
            linhas_editadas = []
            while True:
                linha = input()
                if linha.strip().upper() == 'FIM_EDICAO': break
                linhas_editadas.append(linha)
            conteudo_secao = "\n".join(linhas_editadas)
            print(f"✅ {tipo_secao} modificada.")

    print(f"✅ {tipo_secao} definida.")
    return conteudo_secao

# --- Fase 2: Criação Iterativa dos Capítulos ---
def criar_capitulos(planejamento, modo_autonomo_capitulos=False, nome_projeto=None, capitulos_existentes=None):
    exibir_cabecalho("Criação dos Capítulos")
    if modo_autonomo_capitulos:
        print("🤖 MODO AUTÔNOMO ATIVADO PARA CRIAÇÃO DE CAPÍTULOS 🤖")
        exibir_status("A IA tomará decisões de aprovação e revisão automaticamente.", delay=1.5)

    livro_final_data = {
        "titulo_livro": planejamento['titulo_livro'], "tema_livro": planejamento['tema_livro'],
        "contexto_geral_livro": planejamento['contexto_geral_livro'],
        "publico_alvo": planejamento['publico_alvo'], 
        "capitulos": capitulos_existentes if capitulos_existentes is not None else []
    }
    # Determinar a partir de qual capítulo começar
    capitulo_inicial_num = len(livro_final_data["capitulos"]) + 1
    if capitulo_inicial_num > 1:
        print(f"\nℹ️  Continuando a partir do Capítulo {capitulo_inicial_num} do projeto '{nome_projeto}'...")
    resumos_caps_anteriores_para_contexto = []

    for i_real, titulo_cap_atual in enumerate(planejamento['titulos_capitulos']): # i_real é 0-indexed
        numero_capitulo_atual = i_real + 1 # numero_capitulo_atual é 1-indexed
        if numero_capitulo_atual < capitulo_inicial_num:
            continue # Pula capítulos já existentes
        if not modo_autonomo_capitulos: limpar_tela()
        exibir_cabecalho(f"Capítulo {numero_capitulo_atual}/{len(planejamento['titulos_capitulos'])}: {titulo_cap_atual}")

        contexto_caps_anteriores_str = "\n".join(resumos_caps_anteriores_para_contexto)
        if not contexto_caps_anteriores_str: contexto_caps_anteriores_str = "Este é o primeiro capítulo."
        else: contexto_caps_anteriores_str = f"Contexto dos capítulos anteriores (resumos):\n{contexto_caps_anteriores_str}"

        conteudo_pesquisado_aprovado = ""
        while True: # Loop para pesquisa de conteúdo do capítulo
            prompt_pesquisa_cap = (
                f"Para o capítulo '{titulo_cap_atual}' do livro '{planejamento['titulo_livro']}' "
                f"(público-alvo: {planejamento['publico_alvo']}), cujo tema geral é '{planejamento['contexto_geral_livro']}', "
                f"e considerando o {contexto_caps_anteriores_str}. "
                "Pesquise e forneça os principais pontos, informações relevantes, dados e conceitos a serem abordados neste capítulo específico. Seja detalhado e forneça material substancial."
            )
            conteudo_pesquisado = chamar_api_gemini(prompt_pesquisa_cap, tipo_agente="pesquisa_capitulo")
            print("\nConteúdo/Tópicos para o capítulo (sugerido pela IA):"); print("-" * 30); print(conteudo_pesquisado); print("-" * 30)

            if "ERRO_API" in conteudo_pesquisado:
                print("⚠️ Não foi possível pesquisar conteúdo via IA.")
                if modo_autonomo_capitulos:
                    print("🤖 Modo Autônomo: Pulando pesquisa devido a erro."); conteudo_pesquisado_aprovado = "ERRO PESQUISA (AUTONOMO)"; break
                else:
                    print("Você precisará fornecer os pontos principais manualmente.")
                    linhas_conteudo = []; print("Digite os pontos/conteúdo. Digite 'FIM_CONTEUDO' para terminar.")
                    while True:
                        linha = input();
                        if linha.strip().upper() == 'FIM_CONTEUDO': break
                        linhas_conteudo.append(linha)
                    conteudo_pesquisado_aprovado = "\n".join(linhas_conteudo)
                    if not conteudo_pesquisado_aprovado.strip(): print("❌ Conteúdo manual não pode ser vazio."); continue
                    break
            
            if modo_autonomo_capitulos:
                print("🤖 Modo Autônomo: Aprovando conteúdo pesquisado."); conteudo_pesquisado_aprovado = conteudo_pesquisado; break
            else:
                confirmacao_pesquisa = obter_confirmacao("Aprova este conteúdo/tópicos? (s/n - nova pesquisa / r - refazer com sugestão)", ('s','n','r'))
                if confirmacao_pesquisa == 's': conteudo_pesquisado_aprovado = conteudo_pesquisado; print("✅ Conteúdo aprovado."); break
                elif confirmacao_pesquisa == 'n': exibir_status("Ok, nova pesquisa...")
                elif confirmacao_pesquisa == 'r':
                    sugestao_usuario = obter_input_usuario("Qual sua sugestão para refazer a pesquisa?")
                    exibir_status(f"Refazendo pesquisa com sugestão: '{sugestao_usuario}'...")
        
        texto_capitulo_final = ""
        while True: # Loop para geração e aprovação do texto do capítulo
            prompt_escrita = (
                f"Aja como um escritor especialista e professor experiente no tema do livro '{planejamento['titulo_livro']}'. "
                f"Escreva o conteúdo completo do capítulo '{titulo_cap_atual}'. "
                f"O público-alvo é: {planejamento['publico_alvo']}. "
                f"Baseie-se no seguinte material/tópicos: \n'{conteudo_pesquisado_aprovado}'.\n"
                f"O capítulo deve ter entre {planejamento['min_paragrafos']} e {planejamento['max_paragrafos']} parágrafos. "
                f"Mantenha um tom adequado. Considere o {contexto_caps_anteriores_str} para fluidez.\n"
                "Foque em clareza e coesão. Não adicione 'Neste capítulo...' a menos que natural."
            )
            texto_capitulo_gerado = chamar_api_gemini(prompt_escrita, tipo_agente="escritor")
            print("\nTexto do capítulo gerado pela IA:"); print("-" * 30); print(texto_capitulo_gerado); print("-" * 30)

            if "ERRO_API" in texto_capitulo_gerado:
                print("⚠️ Não foi possível gerar o texto do capítulo via IA.")
                if modo_autonomo_capitulos:
                    print("🤖 Modo Autônomo: Erro ao gerar texto."); texto_capitulo_final = "ERRO GERAÇÃO TEXTO (AUTONOMO)"; break
                elif obter_confirmacao("Tentar gerar novamente? (s/n)", ('s','n')) == 'n':
                    texto_capitulo_final = "ERRO GERAÇÃO CAPÍTULO."; break 
                else: continue

            revisar_pela_ia = modo_autonomo_capitulos or (obter_confirmacao("IA deve revisar este texto? (s/n)", ('s','n')) == 's')
            if modo_autonomo_capitulos and revisar_pela_ia: print("🤖 Modo Autônomo: Solicitando revisão automática.")

            if revisar_pela_ia:
                prompt_revisao = (
                    f"Revise o texto do capítulo '{titulo_cap_atual}' (livro: '{planejamento['titulo_livro']}', público: {planejamento['publico_alvo']}, "
                    f"contexto geral e caps anteriores: {planejamento['contexto_geral_livro']} {contexto_caps_anteriores_str}) "
                    f"quanto à gramática (Português), coesão, clareza. Texto para revisão: \n'{texto_capitulo_gerado}'\n"
                    "Forneça a versão revisada. Se poucas alterações, confirme."
                )
                texto_revisado_sugerido = chamar_api_gemini(prompt_revisao, tipo_agente="revisor")
                print("\nTexto revisado pela IA:"); print("-" * 30); print(texto_revisado_sugerido); print("-" * 30)
                
                if "ERRO_API" not in texto_revisado_sugerido:
                    if modo_autonomo_capitulos:
                        print("🤖 Modo Autônomo: Aplicando texto revisado."); texto_capitulo_gerado = texto_revisado_sugerido 
                    elif obter_confirmacao("Usar texto revisado pela IA? (s/n)", ('s','n')) == 's':
                        texto_capitulo_gerado = texto_revisado_sugerido; print("✅ Texto revisado aplicado.")
                    else: print("ℹ️  Texto original gerado mantido.")
                else: print("⚠️ Erro na revisão da IA. Texto original mantido.")

            if modo_autonomo_capitulos:
                print("🤖 Modo Autônomo: Aprovando texto do capítulo."); texto_capitulo_final = texto_capitulo_gerado; break
            else:
                confirmacao_escrita = obter_confirmacao("Aprova o texto do capítulo? (s/n - reescrever / m - pedir melhorias)", ('s','n','m'))
                if confirmacao_escrita == 's': texto_capitulo_final = texto_capitulo_gerado; print("✅ Texto aprovado!"); break
                elif confirmacao_escrita == 'n': exibir_status("Ok, gerando texto novamente...")
                elif confirmacao_escrita == 'm':
                    sugestao_melhora = obter_input_usuario("O que melhorar/alterar?")
                    exibir_status(f"Regerando com sugestão: '{sugestao_melhora}'...")
        
        resumo_para_contexto_agente_finalizador = "Resumo não disponível." # Default
        prompt_resumo_cap = (
            f"Resuma os pontos principais do capítulo '{titulo_cap_atual}' em 2-3 frases. "
            f"Contexto do capítulo:\n{texto_capitulo_final}"
        )
        resumo_cap_atual = chamar_api_gemini(prompt_resumo_cap, tipo_agente="geral")
        if "ERRO_API" not in resumo_cap_atual and resumo_cap_atual:
            resumo_extraido = resumo_cap_atual.split("Resumo do capítulo", 1)[-1].split(":", 1)[-1].strip() if ":" in resumo_cap_atual else resumo_cap_atual.strip()
            if not resumo_extraido: resumo_extraido = "Resumo não pôde ser extraído."
            resumos_caps_anteriores_para_contexto.append(f"Cap. {i+1} ({titulo_cap_atual}): {resumo_extraido}")
            resumo_para_contexto_agente_finalizador = resumo_extraido # Salvar para o agente finalizador
            print(f"💬 Resumo para contexto: {resumo_extraido}")
        else:
            print("⚠️ Não foi possível gerar resumo do capítulo."); resumos_caps_anteriores_para_contexto.append(f"Cap. {i+1} ({titulo_cap_atual}): Resumo não disponível.")

        capitulo_data = {
            "numero": numero_capitulo_atual, "titulo": titulo_cap_atual,
            "conteudo_pesquisado_aprovado": conteudo_pesquisado_aprovado,
            "texto_final": texto_capitulo_final,
            "resumo_para_contexto": resumo_para_contexto_agente_finalizador
        }
        # Atualiza o capítulo se ele já existir (caso de recriação), ou adiciona novo
        capitulo_encontrado_para_atualizar = False
        for idx, cap_existente in enumerate(livro_final_data["capitulos"]):
            if cap_existente["numero"] == numero_capitulo_atual:
                livro_final_data["capitulos"][idx] = capitulo_data
                capitulo_encontrado_para_atualizar = True
                break
        if not capitulo_encontrado_para_atualizar:
            livro_final_data["capitulos"].append(capitulo_data)
        
        if nome_projeto:
            salvar_progresso_livro_json(livro_final_data, nome_projeto)
            # exibir_status(f"Capítulo '{titulo_cap_atual}' salvo no projeto '{nome_projeto}'.") # Removido pois salvar_progresso já imprime
        else: # Fallback para o nome antigo, caso nome_projeto não seja passado (improvável com as novas mudanças)
            salvar_progresso_livro_json(livro_final_data, "livro_em_progresso_temp.json")
            exibir_status(f"Capítulo '{titulo_cap_atual}' salvo em 'livro_em_progresso_temp.json' (fallback).")


        if numero_capitulo_atual < len(planejamento['titulos_capitulos']):
            if not modo_autonomo_capitulos:
                if obter_confirmacao("Prosseguir para o próximo capítulo?", ('s','n')) != 's':
                    print("⚠️ Criação interrompida."); break
            else: exibir_status(f"🤖 Modo Autônomo: Próximo capítulo ({numero_capitulo_atual + 1})...", delay=1.5)
        else: exibir_status("🎉 Todos os capítulos foram criados!")
    return livro_final_data

# --- Agente Finalizador ---
def agente_finalizador(livro_data_completa, planejamento_completo, nome_projeto=None):
    """
    Agente responsável pela revisão final de todos os capítulos e geração dos documentos.
    Utiliza o modelo de FINALIZAÇÃO configurado em uma ÚNICA chamada otimizada.
    """
    exibir_cabecalho("Agente Finalizador - Revisão Geral Otimizada")
    if not GENERATIVE_MODEL_INSTANCE_FINALIZACAO:
        print("⚠️ Modelo de finalização não configurado. Não é possível executar o Agente Finalizador.")
        print("   Gerando arquivos com o conteúdo atual...")
        if livro_data_completa and livro_data_completa.get("capitulos"):
            nome_base = sanitizar_nome_arquivo(livro_data_completa['titulo_livro'])
            if DOCX_AVAILABLE: gerar_arquivo_docx(livro_data_completa, nome_base)
            if REPORTLAB_AVAILABLE: gerar_arquivo_pdf(livro_data_completa, nome_base)
        return

    print(f"ℹ️  O Agente Finalizador usará o modelo '{GEMINI_MODEL_NAME_FINALIZACAO}' para a revisão holística do livro.")
    
    texto_completo_livro = ""
    for cap_info in livro_data_completa.get('capitulos', []):
        texto_original_cap = cap_info.get('texto_final', '')
        texto_completo_livro += f"--- CAPÍTULO {cap_info['numero']}: {cap_info['titulo']} ---\n"
        texto_completo_livro += f"{texto_original_cap}\n\n"

    if not texto_completo_livro.strip():
        print("❌ Não há conteúdo para ser revisado pelo Agente Finalizador.")
        return

    contexto_prompt_final = (
        f"Contexto Geral do Livro (Tema: {planejamento_completo['tema_livro']}, "
        f"Título do Livro: {planejamento_completo['titulo_livro']}, "
        f"Público-Alvo: {planejamento_completo['publico_alvo']}):\n{planejamento_completo['contexto_geral_livro']}"
    )

    prompt_finalizacao_livro_inteiro = (
        f"Você é um editor de livros sênior e especialista em '{planejamento_completo['tema_livro']}'. "
        f"Realize uma revisão final e polimento no MANUSCRITO COMPLETO a seguir. "
        f"{contexto_prompt_final}\n\n"
        f"Instruções para Revisão Final Holística:\n"
        f"1. Gramática e Ortografia: Corrija todos os erros em Português.\n"
        f"2. Coesão e Coerência Global: Garanta que o livro inteiro flua bem, que as ideias estejam conectadas logicamente entre os capítulos e que não haja contradições.\n"
        f"3. Estilo e Tom Consistentes: Ajuste o texto para manter um tom consistente com o público-alvo ('{planejamento_completo['publico_alvo']}') em todo o livro.\n"
        f"4. Clareza, Precisão e Redundância: Melhore a clareza, corrija imprecisões e elimine repetições desnecessárias ao longo de todo o manuscrito.\n"
        f"5. Não altere fundamentalmente o significado ou os principais pontos dos capítulos, apenas refine-os para a mais alta qualidade editorial.\n"
        f"6. **IMPORTANTE**: Retorne o TEXTO COMPLETO E REVISADO do livro, mantendo EXATAMENTE a mesma estrutura de separadores de capítulo que você recebeu (--- CAPÍTULO X: [TÍTULO] ---). Sua resposta deve começar diretamente com '--- CAPÍTULO 1: ...' e terminar após o último capítulo, sem adicionar comentários ou introduções.\n\n"
        f"TEXTO COMPLETO PARA REVISÃO FINAL:\n{texto_completo_livro}"
    )

    exibir_status(f"Enviando manuscrito completo para revisão final com o modelo '{GEMINI_MODEL_NAME_FINALIZACAO}'...")
    livro_inteiro_revisado = chamar_api_gemini(prompt_finalizacao_livro_inteiro, tipo_agente="finalizador", usar_modelo_finalizacao=True)

    if "ERRO_API" in livro_inteiro_revisado or not livro_inteiro_revisado.strip():
        print(f"⚠️ Erro ao finalizar o livro com o Agente Finalizador. O conteúdo original será mantido.")
        livro_revisado_data = livro_data_completa
    else:
        print("✅ Livro revisado e finalizado pelo Agente.")
        capitulos_revisados_texto = re.split(r'(?=--- CAPÍTULO \d+:)', livro_inteiro_revisado)
        capitulos_revisados_texto = [cap.strip() for cap in capitulos_revisados_texto if cap.strip()]

        if len(capitulos_revisados_texto) == len(livro_data_completa['capitulos']):
            for i, cap_revisado_completo in enumerate(capitulos_revisados_texto):
                texto_apenas = re.sub(r'--- CAPÍTULO \d+:.*?---\n', '', cap_revisado_completo, count=1).strip()
                livro_data_completa['capitulos'][i]['texto_final'] = texto_apenas
            
            livro_revisado_data = livro_data_completa
            if nome_projeto:
                salvar_progresso_livro_json(livro_revisado_data, nome_projeto)
            else: # Fallback
                salvar_progresso_livro_json(livro_revisado_data, "livro_totalmente_revisado_fallback.json")
            exibir_status("💾 Dados do livro atualizados com a revisão final.")
        else:
            print(f"⚠️ Erro ao analisar a resposta do Agente Finalizador. O número de capítulos retornado ({len(capitulos_revisados_texto)}) é diferente do esperado ({len(livro_data_completa['capitulos'])}).")
            print("   O conteúdo original será mantido para evitar perda de dados.")
            livro_revisado_data = livro_data_completa
    
    # A geração de DOCX/PDF é agora controlada pelo main.py após esta função retornar
    # ou se o agente finalizador for pulado. Apenas confirmamos a revisão aqui.
    if "ERRO_API" not in livro_inteiro_revisado and livro_inteiro_revisado.strip():
        print(f"✅ Revisão final aplicada e salva no projeto '{nome_projeto if nome_projeto else '[sem nome definido]'}'.")
    else:
        print(f"ℹ️  Revisão final não aplicada devido a erro ou ausência de conteúdo. Projeto '{nome_projeto if nome_projeto else '[sem nome definido]'}' mantém conteúdo anterior à tentativa de finalização.")
