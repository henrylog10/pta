Practical Exam: Servidor PTA (Protocolo de Transferência de Arquivos)
Autor: José Henrique Barbosa Pena

Matrícula: 202600470060

Instituição: Universidade Federal do Pará (UFPA)

Este repositório contém a implementação do servidor para o Protocolo de Transferência de Arquivos (PTA) sobre TCP, desenvolvido como requisito de avaliação prática. O servidor é capaz de autenticar utilizadores, listar ficheiros disponíveis e transferi-los de forma atómica de acordo com a máquina de estados especificada.

Requisitos e Ambiente de Execução
Linguagem: Python 3
Bibliotecas: O projeto utiliza exclusivamente bibliotecas nativas integradas (standard library) do Python (socket, os, sys). Não é necessária qualquer instalação externa via gestor de pacotes.

Compatibilidade: Funcional em ambiente Windows (via PowerShell), bem como em sistemas baseados em Unix/Linux.

Estrutura de Diretórios
pta-server/pta-server.py: Código-fonte principal da aplicação do servidor PTA.

pta-server/users.txt: Lista de utilizadores autorizados a estabelecer ligação e aceder ao servidor (sensível a maiúsculas e minúsculas).

pta-server/files/: Diretório que armazena os ficheiros estáticos que podem ser requisitados.

pta-client.py: Script do cliente fornecido para a realização de testes automatizados da implementação.
