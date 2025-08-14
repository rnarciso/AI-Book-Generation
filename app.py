import gradio as gr
import os
import time
from book_logic import (
    generate_outline, generate_detailed_summary, suggest_titles,
    suggest_chapter_titles, suggest_target_audience, generate_additional_section,
    create_chapter, finalize_book_with_agent
)
from file_utils import salvar_progresso_livro_json, carregar_dados_livro_json, listar_projetos, sanitizar_nome_arquivo
from document_generator import gerar_arquivo_docx, gerar_arquivo_pdf, DOCX_AVAILABLE, REPORTLAB_AVAILABLE

# --- Configuração da API ---
if os.getenv("GEMINI_API_KEY"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        print("✅ API Gemini configurada com sucesso.")
    except Exception as e:
        print(f"❌ Falha ao configurar a API Gemini: {e}")
else:
    print("⚠️ A variável de ambiente GEMINI_API_KEY não foi encontrada.")

# --- Funções de Lógica da UI ---

def start_planning_phase(theme):
    if not theme:
        gr.Warning("Por favor, insira um tema para o livro.")
        return None, None, None, gr.update(visible=False)

    gr.Info("Iniciando planejamento... Isso pode levar alguns minutos.")

    print(f"[Fase 1] Gerando esboço para o tema: {theme}")
    outline = generate_outline(theme)

    print("[Fase 1] Gerando resumo detalhado...")
    summary = generate_detailed_summary(outline, theme)

    print("[Fase 1] Sugerindo títulos...")
    titles = suggest_titles(summary, theme)

    project_data = {
        "theme": theme,
        "outline": outline,
        "summary": summary,
        "titles": titles
    }

    return project_data, outline, summary, gr.update(visible=True)

def finalize_planning(project_data, selected_title, chapter_count_str, audience_style, paragraphs_str):
    gr.Info("Finalizando o planejamento...")

    try:
        chapter_count = int(chapter_count_str)
        min_p, max_p = map(int, paragraphs_str.split('-'))
        if not (chapter_count > 0 and min_p > 0 and max_p >= min_p):
            raise ValueError()
    except (ValueError, TypeError):
        gr.Warning("Por favor, verifique as configurações (Capítulos, Parágrafos).")
        return None, None, gr.update(visible=False)

    print("[Fase 1] Gerando títulos de capítulos...")
    chapter_titles = suggest_chapter_titles(project_data['summary'], chapter_count, selected_title)

    print("[Fase 1] Gerando público-alvo...")
    target_audience = suggest_target_audience(project_data['summary'], selected_title)

    plan = {
        "tema_livro": project_data['theme'],
        "titulo_livro": selected_title,
        "contexto_geral_livro": project_data['summary'],
        "titulos_capitulos": chapter_titles,
        "publico_alvo": target_audience,
        "min_paragrafos": min_p,
        "max_paragrafos": max_p
    }

    full_book_data = {
        "planejamento_completo": plan,
        "capitulos": [],
        "secoes_adicionais": {}
    }

    # Gerar introdução como exemplo de seção adicional
    print("[Fase 2] Gerando introdução...")
    intro_content = generate_additional_section("Introdução", plan)
    full_book_data["secoes_adicionais"]["introducao"] = {"titulo": "Introdução", "conteudo": intro_content}

    project_name = sanitizar_nome_arquivo(selected_title)
    salvar_progresso_livro_json(full_book_data, project_name)

    status_update = f"Planejamento salvo no projeto '{project_name}'. Pronto para criar capítulos."
    print(status_update)

    return full_book_data, status_update, gr.update(visible=True)


def create_chapters_sequentially(full_book_data):
    if not full_book_data or not full_book_data.get("planejamento_completo"):
        gr.Warning("Planejamento não finalizado. Volte para a Etapa 1.")
        return None, "Planejamento incompleto."

    plan = full_book_data["planejamento_completo"]
    project_name = sanitizar_nome_arquivo(plan['titulo_livro'])
    num_chapters = len(plan['titulos_capitulos'])

    gr.Info(f"Iniciando criação de {num_chapters} capítulos. Isso levará um tempo considerável.")

    previous_chapters_context = "Este é o primeiro capítulo."

    for i, chapter_title in enumerate(plan['titulos_capitulos']):
        status = f"Criando Capítulo {i+1}/{num_chapters}: {chapter_title}..."
        print(status)
        yield full_book_data, status, None, None # Atualiza o status na UI

        chapter_plan = {"numero": i + 1, "titulo": chapter_title}
        new_chapter = create_chapter(chapter_plan, plan, previous_chapters_context)

        full_book_data["capitulos"].append(new_chapter)
        previous_chapters_context += "\n" + new_chapter.get('resumo_para_contexto', '')

        salvar_progresso_livro_json(full_book_data, project_name)
        print(f"Capítulo {i+1} salvo.")

    final_status = f"Todos os {num_chapters} capítulos foram criados com sucesso!"
    print(final_status)
    yield full_book_data, final_status, gr.update(visible=True), None


def finalize_and_generate_files(full_book_data):
    if not full_book_data or not full_book_data.get("capitulos"):
        gr.Warning("Nenhum capítulo foi criado ainda.")
        return None, None, None

    gr.Info("Executando o Agente Finalizador para revisão geral...")
    print("[Fase 4] Executando o Agente Finalizador...")

    final_book_data = finalize_book_with_agent(full_book_data, full_book_data["planejamento_completo"])

    project_name = sanitizar_nome_arquivo(final_book_data["planejamento_completo"]["titulo_livro"])
    final_project_name = f"{project_name}_Finalizado"
    salvar_progresso_livro_json(final_book_data, final_project_name)

    gr.Info("Gerando arquivos DOCX e PDF...")
    print("[Fase 5] Gerando documentos...")

    docx_path = None
    if DOCX_AVAILABLE:
        try:
            gerar_arquivo_docx(final_book_data, final_project_name, "padrao")
            docx_path = f"{final_project_name}.docx"
            print(f"DOCX gerado: {docx_path}")
        except Exception as e:
            print(f"Erro ao gerar DOCX: {e}")

    pdf_path = None
    if REPORTLAB_AVAILABLE:
        try:
            gerar_arquivo_pdf(final_book_data, final_project_name, "padrao")
            pdf_path = f"{final_project_name}.pdf"
            print(f"PDF gerado: {pdf_path}")
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")

    return final_book_data, gr.update(value=docx_path, visible=docx_path is not None), gr.update(value=pdf_path, visible=pdf_path is not None)


# --- Interface Gradio ---
with gr.Blocks(theme=gr.themes.Soft(), title="AI Book Creator") as app:

    # Estrutura de Dados
    project_data_state = gr.State(None) # Armazena o planejamento inicial
    full_book_data_state = gr.State(None) # Armazena a estrutura completa do livro

    gr.Markdown("# 📚 AI Book Creator")
    gr.Markdown("Transforme suas ideias em livros com o poder da IA. Siga as etapas abaixo para criar sua obra.")

    # Etapa 1: Planejamento
    with gr.Accordion("Etapa 1: Planejamento Inicial", open=True):
        theme_input = gr.Textbox(label="Qual é o tema central do seu livro?", placeholder="Ex: A história da computação quântica")
        start_planning_button = gr.Button("Iniciar Planejamento", variant="primary")

        with gr.Column(visible=False) as planning_results_col:
            outline_output = gr.Textbox(label="Esboço Sugerido", lines=10, interactive=True)
            summary_output = gr.Textbox(label="Resumo Detalhado Sugerido", lines=10, interactive=True)

            with gr.Row():
                title_dropdown = gr.Dropdown(label="Escolha um Título (ou digite o seu)", interactive=True, allow_custom_value=True)
                chapter_input = gr.Textbox(label="Nº de Capítulos", value="5", interactive=True)

            with gr.Row():
                audience_dropdown = gr.Dropdown(label="Estilo de Escrita", choices=["Iniciante", "Intermediário", "Especialista"], value="Iniciante", interactive=True)
                paragraphs_input = gr.Textbox(label="Parágrafos por Cap.", value="5-8", interactive=True)

            finalize_planning_button = gr.Button("Finalizar Planejamento e Salvar", variant="primary")

    # Etapa 2: Criação de Capítulos
    with gr.Accordion("Etapa 2: Criação dos Capítulos", open=False) as chapter_creation_accordion:
        start_chapters_button = gr.Button("Gerar Todos os Capítulos", variant="primary", visible=False)
        chapter_status_output = gr.Textbox(label="Progresso", interactive=False)

    # Etapa 3: Finalização e Download
    with gr.Accordion("Etapa 3: Finalização e Download", open=False) as finalization_accordion:
        finalize_button = gr.Button("Revisar Livro e Gerar Arquivos", variant="primary", visible=False)
        with gr.Row():
            download_docx = gr.File(label="Download DOCX", interactive=False, visible=False)
            download_pdf = gr.File(label="Download PDF", interactive=False, visible=False)

    # Conexões da Lógica da UI
    start_planning_button.click(
        fn=start_planning_phase,
        inputs=[theme_input],
        outputs=[project_data_state, outline_output, summary_output, planning_results_col]
    ).then(
        lambda data: gr.update(choices=data.get("titles", []) if data else [], value=data.get("titles", [""])[0] if data and data.get("titles") else ""),
        inputs=[project_data_state],
        outputs=[title_dropdown]
    )

    finalize_planning_button.click(
        fn=finalize_planning,
        inputs=[project_data_state, title_dropdown, chapter_input, audience_dropdown, paragraphs_input],
        outputs=[full_book_data_state, chapter_status_output, start_chapters_button]
    )

    start_chapters_button.click(
        fn=create_chapters_sequentially,
        inputs=[full_book_data_state],
        outputs=[full_book_data_state, chapter_status_output, finalize_button, download_docx]
    )

    finalize_button.click(
        fn=finalize_and_generate_files,
        inputs=[full_book_data_state],
        outputs=[full_book_data_state, download_docx, download_pdf]
    )

if __name__ == "__main__":
    app.launch(share=True)
