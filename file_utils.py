# -*- coding: utf-8 -*-
import json
import re
import os

PROJECTS_DIR = "book_projects"

def _ensure_projects_dir():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

def salvar_progresso_livro_json(livro_data, project_name):
    _ensure_projects_dir()
    nome_arquivo = os.path.join(PROJECTS_DIR, f"{sanitizar_nome_arquivo(project_name)}.json")
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(livro_data, f, ensure_ascii=False, indent=4)
        print(f"✅ Progresso salvo em '{nome_arquivo}'")
    except IOError as e: print(f"❌ Erro ao salvar progresso em '{nome_arquivo}': {e}")

def carregar_dados_livro_json(project_name):
    nome_arquivo = os.path.join(PROJECTS_DIR, f"{sanitizar_nome_arquivo(project_name)}.json")
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: #print(f"ℹ️  Arquivo de projeto '{nome_arquivo}' não encontrado."); 
        return None
    except json.JSONDecodeError: print(f"❌ Erro ao decodificar JSON do projeto '{nome_arquivo}'."); return None

def listar_projetos():
    _ensure_projects_dir()
    try:
        arquivos_json = [f for f in os.listdir(PROJECTS_DIR) if f.endswith('.json')]
        # Retorna nomes de projetos sem a extensão .json
        return [os.path.splitext(f)[0] for f in arquivos_json]
    except OSError as e:
        print(f"❌ Erro ao listar projetos em '{PROJECTS_DIR}': {e}")
        return []

def sanitizar_nome_arquivo(nome):
    nome = str(nome) # Garantir que é string
    nome = re.sub(r'[^\w\s-]', '', nome).strip(); nome = re.sub(r'[-\s]+', '_', nome)
    return nome if nome else "projeto_sem_titulo"