#!/usr/bin/env python3
import os
import sys
import socket

# Configurações padrão de rede e caminhos relativos ao diretório pta-server
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 11550

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.txt")
FILES_DIR = os.path.join(BASE_DIR, "files")

STATE_WAITING = "ESPERANDO"
STATE_READY = "PRONTO"


def load_valid_users(filepath):
    """Carrega a lista de usuários válidos do arquivo users.txt."""
    if not os.path.isfile(filepath):
        return set()
    with open(filepath, "r", encoding="ascii", errors="ignore") as f:
        return {line.strip() for line in f if line.strip()}


def get_available_files(directory):
    """Retorna a lista de arquivos disponíveis no diretório files/."""
    if not os.path.isdir(directory):
        return None
    try:
        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and not f.startswith(".")
        ]
        files.sort()
        return files
    except OSError:
        return None


def send_reply(conn, seq_num, reply, args=b""):
    """Formata e envia a mensagem de resposta: SEQ_NUM REPLY [ARGS]."""
    header = f"{seq_num} {reply}".encode("ascii")
    if args:
        conn.sendall(header + b" " + args)
    else:
        conn.sendall(header)


def handle_client(conn):
    """Gerencia a máquina de estados do protocolo PTA para uma conexão TCP."""
    state = STATE_WAITING
    expected_seq = None
    valid_users = load_valid_users(USERS_FILE)

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            # Remove quebras de linha finais preservando a separação por espaços
            raw_msg = data.decode("ascii", errors="replace").rstrip("\r\n")
            parts = raw_msg.split(" ")

            # Validação mínima de formato: precisa ter ao menos SEQ_NUM e COMMAND
            if len(parts) < 2:
                seq_str = parts[0] if parts and parts[0].isdigit() else "0"
                send_reply(conn, seq_str, "NOK")
                if state == STATE_WAITING:
                    break
                continue

            seq_str = parts[0]
            try:
                seq_num = int(seq_str)
            except ValueError:
                send_reply(conn, seq_str, "NOK")
                if state == STATE_WAITING:
                    break
                continue

            # Validação da sequência incremental de mensagens do cliente
            if expected_seq is None:
                expected_seq = seq_num
            if seq_num != expected_seq:
                send_reply(conn, seq_num, "NOK")
                if state == STATE_WAITING:
                    break
                continue
            expected_seq += 1

            command = parts[1]
            args = parts[2:]

            # Estado 1: ESPERANDO (Exige apresentação via CUMP <nome>)
            if state == STATE_WAITING:
                if command == "CUMP" and len(args) == 1:
                    username = args[0]
                    if username in valid_users:
                        send_reply(conn, seq_num, "OK")
                        state = STATE_READY
                    else:
                        send_reply(conn, seq_num, "NOK")
                        break
                else:
                    send_reply(conn, seq_num, "NOK")
                    break

            # Estado 2: PRONTO (Aceita LIST, PEGA <nome> e TERM)
            elif state == STATE_READY:
                if command == "LIST":
                    if len(args) != 0:
                        send_reply(conn, seq_num, "NOK")
                        continue

                    files = get_available_files(FILES_DIR)
                    if not files:
                        send_reply(conn, seq_num, "NOK")
                    else:
                        file_list_str = ",".join(files)
                        reply_args = f"{len(files)} {file_list_str}".encode("ascii")
                        send_reply(conn, seq_num, "ARQS", reply_args)

                elif command == "PEGA":
                    if len(args) != 1:
                        send_reply(conn, seq_num, "NOK")
                        continue

                    filename = args[0]
                    # Evita Path Traversal garantindo que é apenas o nome do arquivo
                    if os.path.basename(filename) != filename:
                        send_reply(conn, seq_num, "NOK")
                        continue

                    filepath = os.path.join(FILES_DIR, filename)
                    if not os.path.isfile(filepath):
                        send_reply(conn, seq_num, "NOK")
                    else:
                        try:
                            with open(filepath, "rb") as f:
                                file_bytes = f.read()
                            size_prefix = f"{len(file_bytes)} ".encode("ascii")
                            send_reply(conn, seq_num, "ARQ", size_prefix + file_bytes)
                        except OSError:
                            send_reply(conn, seq_num, "NOK")

                elif command == "TERM":
                    if len(args) != 0:
                        send_reply(conn, seq_num, "NOK")
                        continue

                    send_reply(conn, seq_num, "OK")
                    break

                else:
                    # Comandos inválidos no estado PRONTO retornam NOK sem fechar a conexão
                    send_reply(conn, seq_num, "NOK")

    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((DEFAULT_HOST, port))
    server_socket.listen(5)

    print(f"Servidor PTA ouvindo em {DEFAULT_HOST}:{port}...")

    try:
        while True:
            conn, _ = server_socket.accept()
            handle_client(conn)
    except KeyboardInterrupt:
        print("\nEncerrando o servidor PTA.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()