# -*- coding: utf-8 -*-
import os
import time

def limpar_tela():
    """Limpa o terminal para melhor visualização."""
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_cabecalho(titulo):
    """Exibe um cabeçalho formatado."""
    print("\n" + "=" * 60)
    print(f"📚 {titulo.center(56)} 📚")
    print("=" * 60 + "\n")

def exibir_status(mensagem, delay=0.5):
    """Exibe uma mensagem de status."""
    print(f"⚙️  {mensagem}")
    time.sleep(delay)

def obter_input_usuario(pergunta, tipo_esperado=str, validacao_func=None, erro_msg="Entrada inválida. Tente novamente.", opcoes_validas_lista=None):
    """Obtém input do usuário com validação opcional e lista de opções."""
    while True:
        try:
            if opcoes_validas_lista:
                print(f"   Opções disponíveis: {', '.join(opcoes_validas_lista)}")
            
            resposta = input(f"➡️  {pergunta} ").strip()

            if tipo_esperado == int:
                resposta_convertida = int(resposta)
            elif tipo_esperado == float:
                resposta_convertida = float(resposta)
            else:
                resposta_convertida = resposta

            if opcoes_validas_lista and resposta_convertida not in opcoes_validas_lista:
                print(f"❌ Opção inválida. Escolha entre: {', '.join(opcoes_validas_lista)}")
                continue

            if validacao_func:
                if validacao_func(resposta_convertida):
                    return resposta_convertida
                else:
                    print(f"❌ {erro_msg}")
            else:
                if tipo_esperado == str and not resposta_convertida: # Não permitir string vazia se não especificado
                    print("❌ A entrada não pode ser vazia.")
                else:
                    return resposta_convertida
        except ValueError:
            print(f"❌ Erro: Esperava um valor do tipo '{tipo_esperado.__name__}'.")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado: {e}")

def obter_confirmacao(pergunta, opcoes_validas=('s', 'n', 'r', 'm', 'a')):
    """Obtém confirmação do usuário (sim/não/refazer/melhorar/adicionar)."""
    opcoes_str = "/".join(opcoes_validas)
    while True:
        resposta = input(f"➡️  {pergunta} ({opcoes_str}): ").strip().lower()
        if resposta in opcoes_validas:
            return resposta
        else:
            print(f"❌ Opção inválida. Por favor, digite uma das seguintes opções: {opcoes_str}.")