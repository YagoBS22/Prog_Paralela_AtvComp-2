import socket,json 

# --- Configurações Fixas do Cliente ---
SRV_HOST_PADRAO = 'localhost'  # Endereço padrão do servidor (Servidor local)
SRV_PORTA_PADRAO = 12345       # Porta padrão do servidor (TEM QUE SER A MESMA DO SERVIDOR)

# Categorias que o cliente conhece
CATEGORIAS_CLI = {
    "cg": "Conhecimentos Gerais",
    "vg": "Video Games",
    "cn": "Ciência e Natureza",
    "pc": "Computadores",
    "es": "Esportes"
}

# --- Função Principal do Cliente ---
def rodar_cliente_quiz():
    print("🎮 Bem-vindo ao ULTRA QUIZ de Sistemas Distribuidos! 😎")
    
    # Pergunta ao usuário qual o endereço do servidor
    # Se ele só apertar ENTER, usa o endereço padrão (localhost)
    host_do_servidor = input(f"Digite o endereço do servidor (ou ENTER para '{SRV_HOST_PADRAO}'): ").strip()
    if not host_do_servidor:  # Se não digitou nada
        host_do_servidor = SRV_HOST_PADRAO
    
    # Cria o socket do cliente
    sock_para_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Tenta se conectar ao servidor usando o endereço e porta
        print(f"CLI: Tentando conectar ao servidor em {host_do_servidor}:{SRV_PORTA_PADRAO}...")
        sock_para_servidor.connect((host_do_servidor, SRV_PORTA_PADRAO))
        print("CLI: Conectado com sucesso ao servidor!")
    except ConnectionRefusedError: # Se o servidor não estiver lá ou recusar
        print(f"CLI: ERRO - Conexão recusada. O servidor está rodando em {host_do_servidor}:{SRV_PORTA_PADRAO}?")
        return # Termina o programa cliente
    except Exception as erro_conexao: # Outro erro de conexão
        print(f"CLI: ERRO - Falha ao tentar conectar: {erro_conexao}")
        return # Termina o programa cliente

    # --- Etapa 1: Escolher a Categoria ---
    chave_cat_escolhida = ""  # Variável para guardar a categoria
    print("\nEscolha uma categoria para o seu Quiz:")
    # Mostra todas as categorias disponíveis para o usuário
    for chave_c, nome_c in CATEGORIAS_CLI.items():
        print(f"  ({chave_c}) {nome_c}")
    
    # Loop para garantir que o usuário escolha uma categoria válida
    while chave_cat_escolhida not in CATEGORIAS_CLI:
        chave_cat_escolhida = input("Digite a sigla da categoria desejada: ").strip().lower()
        if chave_cat_escolhida not in CATEGORIAS_CLI:
            print("CLI: Sigla de categoria inválida. Por favor, escolha uma da lista.")

    # --- Etapa 2: Escolher a Dificuldade ---
    # Mapa para converter a primeira letra na palavra completa da dificuldade
    mapa_dificuldade = {"e": "easy", "m": "medium", "h": "hard"}
    input_dificuldade_usr = ""  # O que o usuário digitar (E, M, ou H)
    dificuldade_final_envio = ""  # A palavra completa (easy, medium, hard)
    
    print("\nEscolha o nível de dificuldade do Quiz:")
    print("  (E)asy e")
    print("  (M)edium")
    print("  (H)ard")
    
    # Loop para garantir que o usuário escolha uma dificuldade válida
    while not dificuldade_final_envio:
        input_dificuldade_usr = input("Digite a primeira letra da dificuldade (E, M, ou H): ").strip().lower()
        if input_dificuldade_usr in mapa_dificuldade:
            dificuldade_final_envio = mapa_dificuldade[input_dificuldade_usr] # Converte 'e' para 'easy'
        else:
            print("CLI: Letra de dificuldade inválida. Por favor, use E, M ou H.")
    
    try:
        # --- Etapa 3: Envia o pedido para iniciar o Quiz pro servidor ---
        # Monta a mensagem  com a ação, dificuldade e categoria
        msg_para_iniciar_quiz = {
            "act": "START_QUIZ",            # 'act': ação que queremos (iniciar quiz)
            "dif": dificuldade_final_envio, # 'dif': dificuldade escolhida
            "cat_k": chave_cat_escolhida    # 'cat_k': chave da categoria escolhida
        }
        # Converte a mensagem para texto JSON, depois para bytes, e envia
        sock_para_servidor.sendall(json.dumps(msg_para_iniciar_quiz).encode('utf-8'))
        
        # --- Etapa 4: Loop principal do jogo ---
        quiz_esta_acontecendo = True
        while quiz_esta_acontecendo:
            # Espera receber alguma mensagem do servidor (até 2048 bytes)
            dados_do_servidor_bytes = sock_para_servidor.recv(2048)
            # Se não receber nada, o servidor provavelmente desconectou
            if not dados_do_servidor_bytes: 
                print("CLI: O servidor parece ter desconectado o jogo.")
                break # Sai do loop do quiz
            
            # Converte os bytes recebidos para texto JSON, depois para um dicionário
            msg_do_servidor = json.loads(dados_do_servidor_bytes.decode('utf-8'))
            tipo_da_msg_servidor = msg_do_servidor.get("tipo") # Pega o "tipo" da mensagem

            # Verifica o tipo da mensagem enviada do servidor
            if tipo_da_msg_servidor == "DETALHES_Q": # Servidor mandou os detalhes do quiz
                print(f"\n--- Começando o Quiz! ---")
                print(f" Categoria: {msg_do_servidor.get('cat_n')}") # Nome da categoria
                print(f" Dificuldade: {msg_do_servidor.get('dif_n').title()}") # Dificuldade (Easy, Medium, Hard)
                print(f" Total de Perguntas: {msg_do_servidor.get('num_p')}")
                print(f"---------------------------")
                if msg_do_servidor.get('num_p', 0) == 0: # Avisa se não tiver perguntas
                    print("CLI: Atenção! O servidor informou 0 perguntas. O quiz pode não funcionar.")
            
            elif tipo_da_msg_servidor == "PERGUNTA": # Servidor mandou uma pergunta
                num_p_srv = msg_do_servidor.get('num_p_atual') # Número da pergunta atual
                total_p_srv = msg_do_servidor.get('total_p_quiz') # Total de perguntas
                texto_p_srv = msg_do_servidor.get('txt_p')      # Texto da pergunta
                print(f"\nPergunta {num_p_srv} de {total_p_srv}:")
                print(f" {texto_p_srv}")
                
                opcoes_da_pergunta = msg_do_servidor.get("ops_p", {}) # Pega as opções
                for letra_op, texto_op in opcoes_da_pergunta.items(): # Mostra cada opção
                    print(f"  {letra_op}) {texto_op}")
                
                resposta_usuario = "" # Variável para guardar a resposta do usuário
                # Loop até o usuário digitar uma letra de opção válida ou "quit"
                while resposta_usuario not in opcoes_da_pergunta.keys() and resposta_usuario != "quit":
                    resposta_usuario = input("Digite a letra da sua resposta (ou 'quit' para sair): ").strip().lower()

                if resposta_usuario == "quit": # Se o usuário quer sair
                    msg_sair = {"act": "QUIT"}
                    sock_para_servidor.sendall(json.dumps(msg_sair).encode('utf-8'))
                    print("CLI: Você escolheu sair do quiz.")
                    quiz_esta_acontecendo = False # Para o loop do quiz
                else: # Se respondeu uma opção, envia a resposta para o servidor
                    msg_resposta = {
                        "act": "SUBMIT_RESPOSTA",             # Ação: enviar resposta
                        "id_p": msg_do_servidor.get("id_p"),  # ID da pergunta que está respondendo
                        "ans_k": resposta_usuario             # Letra da resposta que escolheu
                    }
                    sock_para_servidor.sendall(json.dumps(msg_resposta).encode('utf-8'))
            
            elif tipo_da_msg_servidor == "FEEDBACK": # Servidor mandou o resultado da resposta
                print("\n--- Resultado da sua resposta ---")
                if msg_do_servidor.get("acertou"): # Se acertou for True
                    print(" Você ACERTOU! :)")
                else: # Se acertou for False
                    letra_certa = msg_do_servidor.get('resp_c_k')
                    print(f" Você ERROU. :( A resposta correta era a letra: {letra_certa.upper()}")
                # Mostra a pontuação atual
                print(f" Sua pontuação atual: {msg_do_servidor.get('pts_atuais')}")
                print("---------------------------------")
            
            elif tipo_da_msg_servidor == "FIM_JOGO": # Servidor avisou que o jogo acabou
                print(f"\n--- O Jogo Acabou! ---")
                pontos_finais_srv = msg_do_servidor.get('pts_finais')
                total_perguntas_srv = msg_do_servidor.get('total_p_q')
                print(f"Sua pontuação final foi: {pontos_finais_srv} de {total_perguntas_srv} perguntas.")
                print(f"------------------------")
                quiz_esta_acontecendo = False # Para o loop do quiz
            
            elif tipo_da_msg_servidor == "ERRO": # Servidor enviou uma mensagem de ERRO
                print(f"\nOPS! ERRO VINDO DO SERVIDOR: {msg_do_servidor.get('txt')}")
                print("CLI: O quiz não pode continuar devido a este erro.")
                quiz_esta_acontecendo = False # Para o loop do quiz
            
            elif tipo_da_msg_servidor == "INFO": # Servidor enviou uma mensagem informativa
                # Se for uma confirmação de que saiu (QUIT), para o loop
                if "quit" in msg_do_servidor.get("txt", "").lower() or \
                   "saiu" in msg_do_servidor.get("txt", "").lower():
                    print(f"CLI INFO: {msg_do_servidor.get('txt')}") # Mostra a info
                    quiz_esta_acontecendo = False # Para o loop
                else:
                    print(f"CLI INFO: {msg_do_servidor.get('txt')}") # Mostra outras infos

            else: # Se receber um tipo de mensagem que não conhece
                print(f"CLI: Recebi uma mensagem estranha do servidor (tipo: {tipo_da_msg_servidor})")

    except ConnectionAbortedError: # Se a conexão cair do nada
        print("CLI: A conexão com o servidor foi cortada.")
    except json.JSONDecodeError: # Se receber algo que não é JSON do servidor
        print("CLI: Erro ao tentar ler mensagem do servidor (não era JSON válido).")
    except KeyboardInterrupt: # Se o usuário apertar Ctrl+C para sair
        print("\nCLI: Você apertou Ctrl+C. Saindo do quiz...")
        # Tenta avisar o servidor que está saindo
        if sock_para_servidor:
            try:
                msg_sair_urgente = {"act": "QUIT"}
                sock_para_servidor.sendall(json.dumps(msg_sair_urgente).encode('utf-8'))
            except:
                pass # Ignora erros ao tentar enviar na saída urgente
    except Exception as erro_geral_cliente: # Pega qualquer outro erro que possa acontecer
        print(f"CLI: Ocorreu um erro inesperado durante o quiz: {erro_geral_cliente}")
    finally: # Este bloco SEMPRE executa, não importa o que aconteça
        print("CLI: Encerrando a conexão com o servidor.")
        if sock_para_servidor: # Se o socket ainda existir
            sock_para_servidor.close() # Fecha a conexão do cliente
        print("CLI: Cliente finalizado.")


if __name__ == "__main__": 
    rodar_cliente_quiz() # Roda o client