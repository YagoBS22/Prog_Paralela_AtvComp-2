# 🎮 Bem-vindo ao ULTRA QUIZ de Sistemas Distribuidos! 😎

## Funcionalidades

* **Jogo Cliente-Servidor:** O servidor gerencia o quiz e os clientes se conectam para jogar.
* **Múltiplos Clientes:** O servidor consegue atender vários jogadores ao mesmo tempo.
* **Escolha de Categoria:** O jogador pode escolher entre 5 categorias diferentes para o quiz:
    * (cg) Conhecimentos Gerais
    * (vg) Video Games
    * (cn) Ciência e Natureza
    * (pc) Computadores
    * (es) Esportes
* **Escolha de Dificuldade:** O jogador pode escolher a dificuldade do quiz digitando a primeira letra:
    * (E)asy
    * (M)edium
    * (H)ard
* **Número de Perguntas:** Cada quiz tem 5 perguntas.
* **Fonte das Perguntas:** As perguntas são buscadas da API pública Open Trivia Database.
* **Comunicação:** Cliente e servidor se comunicam usando Sockets TCP/IP, trocando mensagens no formato JSON.

## Estrutura do Projeto
├── server.py \
├── client.py \
├── requirements.txt \
└── README.md \


## Requisitos

* Python 3.x
* Biblioteca `requests` (para o servidor buscar perguntas na internet).

## Como Executar

Siga os passos abaixo para rodar o jogo:

1.  **Clone o Repositório ou Baixe os Arquivos:**

2.  **Instale as Dependências:**
    Abra um terminal ou prompt de comando na pasta onde você salvou os arquivos e execute o seguinte comando para instalar a biblioteca `requests`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Inicie o Servidor:**
    * No mesmo terminal (ou em um novo, na mesma pasta), execute o script do servidor:
        ```bash
        python server.py
        ```
    * O servidor começará a "escutar" por conexões na porta `12345` e no endereço `0.0.0.0`. Você verá mensagens no console do servidor indicando que ele está no ar.

4.  **Inicie o Cliente (ou Clientes):**
    * Abra um **novo** terminal para cada jogador que quiser participar. Navegue até a pasta do projeto.
    * Execute o script do cliente:
        ```bash
        python client.py
        ```
    * O cliente perguntará primeiro pelo "Host do Servidor".
        * Se o servidor estiver rodando no **mesmo computador** que o cliente, você pode apenas apertar `ENTER` (o padrão é `localhost`).
        * Se o servidor estiver rodando em **outro computador na mesma rede**, digite o endereço IP daquele computador (ex: `192.168.1.10`).
    * Siga as instruções no cliente para escolher a categoria e a dificuldade do quiz.

## Protocolo de Comunicação (Simplificado)

A comunicação entre o cliente e o servidor é feita através de mensagens no formato JSON.

**Mensagens do Cliente para o Servidor:**

* **Iniciar Quiz:**
    * `{"act": "START_QUIZ", "dif": "dificuldade_completa", "cat_k": "chave_da_categoria"}`
    * Ex: `{"act": "START_QUIZ", "dif": "easy", "cat_k": "vg"}`
* **Enviar Resposta:**
    * `{"act": "SUBMIT_RESPOSTA", "id_p": id_da_pergunta, "ans_k": "letra_da_resposta_do_usuario"}`
    * Ex: `{"act": "SUBMIT_RESPOSTA", "id_p": 0, "ans_k": "a"}`
* **Sair do Jogo:**
    * `{"act": "QUIT"}`

**Mensagens do Servidor para o Cliente:**

* **Detalhes do Quiz:**
    * `{"tipo": "DETALHES_Q", "cat_n": "Nome Completo da Categoria", "dif_n": "dificuldade_completa", "num_p": numero_de_perguntas}`
    * Ex: `{"tipo": "DETALHES_Q", "cat_n": "Video Games", "dif_n": "easy", "num_p": 5}`
* **Enviar Pergunta:**
    * `{"tipo": "PERGUNTA", "id_p": id_da_pergunta, "txt_p": "Texto da pergunta...", "ops_p": {"a":"Opção A", "b":"Opção B", ...}, "num_p_atual": numero_da_pergunta_atual, "total_p_quiz": total_de_perguntas}`
* **Feedback da Resposta:**
    * `{"tipo": "FEEDBACK", "acertou": true_ou_false, "resp_c_k": "letra_da_resposta_correta", "pts_atuais": pontuacao_atual_do_jogador}`
* **Fim de Jogo:**
    * `{"tipo": "FIM_JOGO", "pts_finais": pontuacao_final, "total_p_q": total_de_perguntas_no_quiz}`
* **Erro:**
    * `{"tipo": "ERRO", "txt": "Mensagem descritindo o erro"}`
* **Informação (ex: confirmação de QUIT):**
    * `{"tipo": "INFO", "txt": "Mensagem informativa"}`

Divirta-se!
