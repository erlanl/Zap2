import socket
import time

class Server:

    def __init__(self):
        #Porta do server
        self.port_tcp = 50000
        self.port_udp = 50001

        #Criando socket TCP do server
        self.server_tcp = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_tcp.bind(('localhost', self.port_tcp))

        #Criando socket UDP do server
        self.server_udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_udp.bind(('localhost', self.port_udp))

        #Inicia o server
        self.start()

    #Aceita a conexão do cliente e recebe seus dados
    def accept_client(self):
        client, addr = self.server_tcp.accept()
        name = client.recv(1024).decode('utf-8')
        print("Nome: " + name)

        addr_pair_msg = self.server_udp.recvfrom(1024)
        print("Addr envio mensagens: " + str(addr_pair_msg[1]))
        command = addr_pair_msg[0].decode('utf-8')
        address_msg = addr_pair_msg[1]

        addr_pair_acks = self.server_udp.recvfrom(1024)
        print("Addr envio acks: " + str(addr_pair_acks[1]) + "\n")
        command = addr_pair_acks[0].decode('utf-8')
        address_acks = addr_pair_acks[1]

        client_list = [client, addr[0], addr[1], name, address_msg[1], address_acks[1]]

        return client_list

    #Envia os dados de um cliente ao outro
    def send_data(self, client_sender, client_reciever):
        client_reciever[0].sendall(client_sender[3].encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(client_sender[1].encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(str(client_sender[2]).encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(str(client_sender[4]).encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(str(client_sender[5]).encode('utf-8'))
        print("Troca Concluída")

    def start(self):
        self.server_tcp.listen(2)
        self.client1 = self.accept_client()
        self.client2 = self.accept_client()

        #Troca os dados entre os clientes
        self.send_data(self.client1, self.client2)
        self.send_data(self.client2, self.client1)

        #Fecha a conexão do server
        self.server_tcp.close()
        self.server_udp.close()

server = Server()