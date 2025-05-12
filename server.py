import threading, json, requests, html, random, string, socket

# --- Configurações Fixas do Servidor ---
MEU_ENDERECO = '0.0.0.0'  # Endereço onde o servidor vai escutar (0.0.0.0 = todos os disponíveis)
MINHA_PORTA = 12345  # Número da porta onde o servidor vai atender
NUM_PERGUNTAS = 5  # Quantas perguntas cada quiz vai ter
MAX_CLIENTES_FILA = 5  # Quantos clientes podem esperar na fila se o servidor estiver ocupado

# Categorias que nosso servidor conhece e oferece
CATEGORIAS_SRV = {
    "cg": {"id_api": 9, "nome": "Conhecimentos Gerais"},
    "vg": {"id_api": 15, "nome": "Video Games"},
    "cn": {"id_api": 17, "nome": "Ciência e Natureza"},
    "pc": {"id_api": 18, "nome": "Computadores"},
    "es": {"id_api": 21, "nome": "Esportes"}
}

# --- Função para buscar as perguntas na internet (API OpenTDB) ---
# dif_escolhida: dificuldade ("easy", "medium", "hard")
# id_cat_api: número da ID da categoria para a API
# nome_cat_bonito: nome da categoria para mostrar nos prints do servidor
def buscar_perguntas_api(dif_escolhida, id_cat_api, nome_cat_bonito):
    # Avisa no console do servidor que está buscando
    print(f"SRV: Buscando {NUM_PERGUNTAS} perguntas de '{nome_cat_bonito}' (dificuldade: '{dif_escolhida}')...")
    
    # Monta o link para pedir as perguntas para a API
    url_api = f"https://opentdb.com/api.php?amount={NUM_PERGUNTAS}&category={id_cat_api}&difficulty={dif_escolhida}&type=multiple"
    
    lista_p_formatadas = []  # Lista vazia para guardar as perguntas já arrumadas

    try:
        # Tenta fazer o pedido para a API
        resposta_da_api = requests.get(url_api, timeout=7)
        
        # Verifica se a API respondeu com sucesso (código 200 significa OK)
        if resposta_da_api.status_code != 200:
            print(f"SRV: API não respondeu OK. Código: {resposta_da_api.status_code}")
            return None  # Retorna Nada se deu erro
        
        # Pega os dados da resposta da API (que vêm em formato JSON)
        dados_recebidos_api = resposta_da_api.json()
        
        # A API tem um campo 'response_code'. Se for diferente de 0, algo deu errado lá na API.
        if dados_recebidos_api['response_code'] != 0:
            print(f"SRV: API retornou erro interno (Código API: {dados_recebidos_api['response_code']}) para '{nome_cat_bonito}' na dificuldade '{dif_escolhida}'.")
            return None # Retorna Nada

        # Arrumar cada pergunta:
        for pergunta_da_api in dados_recebidos_api['results']:
            # Pega o texto da pergunta e conserta os caracteres especiais
            texto_pergunta = html.unescape(pergunta_da_api['question'])
            # Pega a resposta correta e arruma também
            resp_correta_txt = html.unescape(pergunta_da_api['correct_answer'])
            # Pega as respostas incorretas e arruma cada uma
            resps_incorretas_lista = [html.unescape(r_inc) for r_inc in pergunta_da_api['incorrect_answers']]
            
            # Junta todas as opções numa lista só
            todas_opcoes = resps_incorretas_lista + [resp_correta_txt]
            random.shuffle(todas_opcoes)  # Embaralha a ordem das opções

            opcoes_com_letras = {}
            letra_resp_correta = ''
            
            # Loop para dar uma letra para cada opção
            for i, texto_opcao_atual in enumerate(todas_opcoes):
                letra_da_opcao = string.ascii_lowercase[i] 
                opcoes_com_letras[letra_da_opcao] = texto_opcao_atual
                
                # Se o texto da opção for igual ao da resposta correta
                if texto_opcao_atual == resp_correta_txt:
                    letra_resp_correta = letra_da_opcao
            
            # Guarda a pergunta formatada na lista
            lista_p_formatadas.append({
                "p_txt": texto_pergunta,      # 'p_txt' = texto da pergunta
                "p_ops": opcoes_com_letras,   # 'p_ops' = opções com letras
                "p_rc_k": letra_resp_correta  # 'p_rc_k' = letra (key) da resposta correta
            })
        
        # Se, depois de tudo, tiver pelo menos uma pergunta formatada, retorna a lista
        if len(lista_p_formatadas) >= 1:
            return lista_p_formatadas
        else:
            print(f"SRV: Nenhuma pergunta foi formatada para '{nome_cat_bonito}' - '{dif_escolhida}', mesmo com API OK.")
            return None

    except Exception as erro_na_busca: # Se qualquer outro erro acontecer
        print(f"SRV: Falha ao buscar/processar perguntas de '{nome_cat_bonito}' - '{dif_escolhida}'. Erro: {erro_na_busca}")
        return None

# --- Função de conexão com um cliente específico ---
def tratar_cliente(sock_cli, end_cli):
    # Avisa no console do servidor que um novo cliente se conectou
    print(f"SRV: Cliente {end_cli} conectou.")
    pontos_jogador = 0  # Cada jogador começa com 0 pontos

    try:
        # 1. Recebea a primeira mensagem do cliente
        dados_recebidos_bytes = sock_cli.recv(1024) # Espera receber até 1024 bytes de dados
        # Se não receber nada, o cliente desconectou antes de começar
        if not dados_recebidos_bytes:
            print(f"SRV: Cliente {end_cli} desconectou antes de iniciar.")
            return 

        # Converte os bytes recebidos para texto (JSON) e depois para um dicionário
        msg_cliente_inicio = json.loads(dados_recebidos_bytes.decode('utf-8'))

        # 2. Pegar a categoria e dificuldade que o cliente escolheu na mensagem
        cat_k_cliente = msg_cliente_inicio.get("cat_k")  # Ex: "vg" (Video Games)
        dif_cliente = msg_cliente_inicio.get("dif")    # Ex: "easy"

        # 3. Verificar se o pedido do cliente é válido
        acao_valida = msg_cliente_inicio.get("act") == "START_QUIZ"
        dif_valida = dif_cliente in ["easy", "medium", "hard"]
        cat_valida = cat_k_cliente in CATEGORIAS_SRV
        
        if not (acao_valida and dif_valida and cat_valida):
            # Se algo estiver inválido, avisa o cliente e encerra a conexão
            print(f"SRV: Pedido inválido do cliente {end_cli}. Ação: {msg_cliente_inicio.get('act')}, Cat: {cat_k_cliente}, Dif: {dif_cliente}")
            msg_erro_inicio = {"tipo": "ERRO", "txt": "Seu pedido para iniciar o quiz é inválido."}
            sock_cli.sendall(json.dumps(msg_erro_inicio).encode('utf-8'))
            return # Termina a função para este cliente

        # 4. Se o tudo foi válido, busca as informações da categoria escolhida
        info_da_cat_escolhida = CATEGORIAS_SRV[cat_k_cliente]
        id_cat_para_api = info_da_cat_escolhida["id_api"]    # Número da ID para a API
        nome_cat_para_mostrar = info_da_cat_escolhida["nome"]  # Nome bonito para mostrar

        # 5. Tenta buscar as perguntas na API usando a categoria e dificuldade
        lista_de_perguntas = buscar_perguntas_api(dif_cliente, id_cat_para_api, nome_cat_para_mostrar)
        
        # Se não conseguiu buscar perguntas (lista_de_perguntas é None ou vazia)
        if not lista_de_perguntas:
            print(f"SRV: Falha ao obter perguntas para {nome_cat_para_mostrar} ({dif_cliente}) para o cliente {end_cli}.")
            msg_erro_perguntas = {"tipo": "ERRO", "txt": f"Desculpe, não consegui perguntas de '{nome_cat_para_mostrar}' ({dif_cliente}) agora."}
            sock_cli.sendall(json.dumps(msg_erro_perguntas).encode('utf-8'))
            return # Termina para este cliente

        # 6. Enviar para o cliente os detalhes do quiz
        num_perguntas_obtidas = len(lista_de_perguntas) # Vê quantas perguntas realmente conseguiu
        msg_detalhes_quiz = {
            "tipo": "DETALHES_Q",       # 'tipo' da mensagem: Detalhes do Quiz
            "cat_n": nome_cat_para_mostrar, # 'cat_n': Nome da categoria
            "dif_n": dif_cliente,           # 'dif_n': Dificuldade escolhida
            "num_p": num_perguntas_obtidas  # 'num_p': Número de perguntas
        }
        sock_cli.sendall(json.dumps(msg_detalhes_quiz).encode('utf-8'))

        # 7. Loop principal do Quiz: para cada pergunta na lista:
        for i_pergunta, dados_pergunta_atual in enumerate(lista_de_perguntas):
            # Monta a mensagem da pergunta
            msg_pergunta = {
                "tipo": "PERGUNTA",           # 'tipo' da mensagem: Pergunta
                "id_p": i_pergunta,           # 'id_p': um ID simples para a pergunta (0, 1, 2...)
                "txt_p": dados_pergunta_atual["p_txt"], # 'txt_p': texto da pergunta
                "ops_p": dados_pergunta_atual["p_ops"], # 'ops_p': opções com letras
                "num_p_atual": i_pergunta + 1,        # 'num_p_atual': qual pergunta é esta (1 de 5, 2 de 5...)
                "total_p_quiz": num_perguntas_obtidas   # 'total_p_quiz': total de perguntas
            }
            sock_cli.sendall(json.dumps(msg_pergunta).encode('utf-8')) # Envia a pergunta
            
            # Espera pela resposta do cliente
            dados_resposta_bytes = sock_cli.recv(1024)
            if not dados_resposta_bytes: # Se cliente desconectou no meio
                print(f"SRV: Cliente {end_cli} desconectou durante a pergunta {i_pergunta + 1}.")
                break # Sai do loop de perguntas
            
            # Converte a resposta do cliente
            msg_resposta_cliente = json.loads(dados_resposta_bytes.decode('utf-8'))

            # Verifica se o cliente quer sair (QUIT)
            if msg_resposta_cliente.get("act") == "QUIT":
                print(f"SRV: Cliente {end_cli} pediu para sair do jogo.")
                # Poderia enviar uma confirmação de QUIT, mas para simplificar, só paramos.
                break # Sai do loop de perguntas

            # Caso a resposta não tenha sido QUIT
            jogador_acertou = False # Começa achando que errou
            if msg_resposta_cliente.get("act") == "SUBMIT_RESPOSTA":
                # Pega a letra que o jogador respondeu
                letra_respondida_pelo_jogador = msg_resposta_cliente.get("ans_k")
                # Pega a letra da resposta correta para a pergunta
                letra_correta_desta_pergunta = dados_pergunta_atual["p_rc_k"]
                
                # Compara se são iguais
                if letra_respondida_pelo_jogador == letra_correta_desta_pergunta:
                    pontos_jogador += 1  # Aumenta os pontos
                    jogador_acertou = True # Marca que acertou
            
            # Monta a mensagem de feedback para o cliente
            msg_feedback = {
                "tipo": "FEEDBACK",             # 'tipo' da mensagem: Feedback
                "acertou": jogador_acertou,       # 'acertou': True ou False
                "resp_c_k": dados_pergunta_atual["p_rc_k"], # 'resp_c_k': Letra da resposta correta
                "pts_atuais": pontos_jogador    # 'pts_atuais': Pontuação atual
            }
            sock_cli.sendall(json.dumps(msg_feedback).encode('utf-8')) # Envia o feedback
        
        # 8. Fim do loop de perguntas, envia mensagem de Fim de Jogo
        msg_fim_jogo = {
            "tipo": "FIM_JOGO",                 # 'tipo' da mensagem: Fim de Jogo
            "pts_finais": pontos_jogador,       # 'pts_finais': Pontos totais feitos
            "total_p_q": num_perguntas_obtidas  # 'total_p_q': Total de perguntas que teve no quiz
        }
        sock_cli.sendall(json.dumps(msg_fim_jogo).encode('utf-8'))
        print(f"SRV: Quiz finalizado para {end_cli}. Pontuação: {pontos_jogador}/{num_perguntas_obtidas}")

    except ConnectionResetError: # Erro comum se o cliente fecha a janela de repente
        print(f"SRV: Cliente {end_cli} fechou a conexão abruptamente.")
    except json.JSONDecodeError: # Se o cliente mandar algo que não é JSON
        print(f"SRV: Cliente {end_cli} enviou dados inválidos (não JSON).")
    except Exception as erro_geral_cliente: # Pega qualquer outro erro que possa acontecer
        print(f"SRV: Erro inesperado com cliente {end_cli}: {erro_geral_cliente}")
    finally: # Este bloco SEMPRE executa, mesmo se der erro ou não
        print(f"SRV: Encerrando conexão com {end_cli}.")
        sock_cli.close() # Fecha a conexão com o cliente

# --- Função Principal que Inicia o Servidor ---
def iniciar_servidor():
    # Cria o socket principal do servidor
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Configuração para poder reiniciar o servidor rápido sem erro de "porta já em uso"
    socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try: 
        # Tenta ligar o servidor no endereço e porta definidos
        socket_servidor.bind((MEU_ENDERECO, MINHA_PORTA))
    except Exception as erro_bind: 
        print(f"SRV: CRÍTICO - Não consegui ligar o servidor em {MEU_ENDERECO}:{MINHA_PORTA}. Erro: {erro_bind}")
        return # Se não conseguir, para tudo
    
    # Coloca o servidor para esperar por pedidos de conexão de clientes
    # MAX_CLIENTES_FILA é quantos podem ficar na fila esperando
    socket_servidor.listen(MAX_CLIENTES_FILA) 
    print(f"SRV: Servidor de Quiz está no ar em {MEU_ENDERECO}:{MINHA_PORTA}")
    print(f"SRV: Oferecendo {len(CATEGORIAS_SRV)} categorias, com {NUM_PERGUNTAS} perguntas por quiz.")
    
    try:
        # Loop infinito para o servidor ficar sempre aceitando novos clientes
        while True:
            # Espera aqui até um novo cliente tentar se conectar...
            print("SRV: Aguardando novas conexões de clientes...")
            novo_sock_cli, novo_end_cli = socket_servidor.accept() 
            
            # Criação de uma nova Thread para o cliente	
            nova_thread_cliente = threading.Thread(target=tratar_cliente, args=(novo_sock_cli, novo_end_cli), daemon=True)
            nova_thread_cliente.start() # Inicia a Thread
            
    except KeyboardInterrupt: # Se alguém apertar Ctrl+C no console do servidor
        print("\nSRV: Recebido Ctrl+C. Desligando o servidor manualmente :(...")
    except Exception as erro_loop_principal: # Outro erro grave no loop principal
        print(f"SRV: CRÍTICO - Erro no loop principal do servidor: {erro_loop_principal}")
    finally:
        print("SRV: Fechando o socket principal do servidor.")
        socket_servidor.close() # Fecha o socket principal do servidor
        print("SRV: Servidor completamente desligado.")

if __name__ == "__main__": 
    iniciar_servidor() # Roda o server