import socket
import random
import struct
import select

#Tamanho do payload
PAYLOAD = 65536

#Tempo para timeout
TIMEOUT = 0.5

#Indica que o pacote é de dados
TYPE_DATA = 0

#Indica que o pacote é de acks
TYPE_ACK = 1

#Indica que o Cabeçalho vai ter o formato string
MSG_FORMAT = 'B?HH'

#Tamanho do Cabeçalho em bytes
HEADER_SIZE = 6

#Formato do abeçalho:
#Type (Dados ou Ack)    (1 byte)
#Número de Sequência    (1 byte)
#Checksum               (2 bytes)
#Tamanho do Payload     (2 bytes)

#Número de sequência dos pacotes
num_seq_sended = 0
num_seq_received = 0

#Número de sequência do último ack
num_last_ack = None

#Recebe mensagem UDP com tamanho de buffer passado
def udt_receive(sockd, length):
    (msg, peer) = sockd.recvfrom(length)
    return msg

#Calcula o checksum da mensagem em bytes
def chksum(byte_msg):
    total = 0
    length = len(byte_msg)
    i = 0
    while length > 1:
        total += ((byte_msg[i + 1] << 8) & 0xFF00) + ((byte_msg[i]) & 0xFF)
        i += 2
        length -= 2

    if length > 0:
        total += (byte_msg[i] & 0xFF)

    while (total >> 16) > 0:
        total = (total & 0xFFFF) + (total >> 16)

    total = ~total

    return total & 0xFFFF

#Cria o pacote que será enviado para o outro cliente 
#com o seu devido número de sequência
def make_packet(number_seq, data):
    global TYPE_DATA, MSG_FORMAT

    #Cria o pacote inicial -> Para podermos realizar o checksum
    #sobre ele e assim criar o pacote final
    msg_format = struct.Struct(MSG_FORMAT)

    #Coloca o checksum = 0 provisoriamente#
    #enquanto ainda não calculamos o checksum real
    checksum = 0
    initial_msg = msg_format.pack(TYPE_DATA, number_seq, checksum, socket.htons(len(data))) + data

    #Calcula o checksum
    checksum = chksum(bytearray(initial_msg))

    #Cria o pacote final com o checksum correto
    complete_msg = msg_format.pack(TYPE_DATA, number_seq, checksum, socket.htons(len(data))) + data

    return complete_msg

#Cria o ACK que será enviado para o outro cliente
#com o seu devido número de sequência
def make_ack(seq_num):
    global TYPE_ACK, MSG_FORMAT

    #Cria o ACK inicial -> Para podermos realizar o checksum
    #sobre ele e assim criar o ACK final
    msg_format = struct.Struct(MSG_FORMAT)

    #Coloca o checksum = 0 provisoriamente#
    #enquanto ainda não calculamos o checksum real
    checksum = 0
    init_msg = msg_format.pack(TYPE_ACK, seq_num, checksum, socket.htons(0)) + b''

    #Calcula o checksum
    checksum = chksum(bytearray(init_msg))
    # print("checksum = ", checksum)

    #Cria o ACK final com o checksum correto
    return msg_format.pack(TYPE_ACK, seq_num, checksum, socket.htons(0)) + b''

#Desempacota o pacote recebido
def unpacker(msg):
    global MSG_FORMAT
    size = struct.calcsize(MSG_FORMAT)
    (msg_type, number_seq, checksum_received, payload_lenght), payload = struct.unpack(MSG_FORMAT, msg[:size]), msg[size:]
    return (msg_type, number_seq, checksum_received, socket.ntohs(payload_lenght)), payload


#Verifica se o pacote recebido está corrompido
def is_corrupted(pckt_received):
    global MSG_FORMAT

    #Desempacota o pacote recebido
    (msg_type, number_seq, checksum_received, payload_lenght), payload = unpacker(pckt_received)

    #Reconstrí a mensagem inicial para calcular o checksum real
    init_msg = struct.Struct(MSG_FORMAT).pack(msg_type, number_seq, 0, socket.htons(payload_lenght)) + payload

    #Calcula o checksum
    checksum_calculated = chksum(bytearray(init_msg))

    #Verifica se o checksum real bateu com o checksum recebido
    result = checksum_received != checksum_calculated

    return result

#Verifica se a mensagem recebida é o ack esperado
def is_ack(pckt_received, number_seq):
    global TYPE_ACK

    #Desempacota a mensagem e verifica se o pacote é um ack
    #e se o número de sequência é o esperado
    (msg_type, number_seq_received, _, _), _ = unpacker(pckt_received)
    return msg_type == TYPE_ACK and number_seq_received == number_seq

#Verifica se o pacote recebido tem o número de sequência esperado
def seq_verifier(pckt_received, number_seq):
    #Desempacota a mensagem e verifica se o número de sequência é o esperado
    (msg_type, number_seq_received, _, _), _ = unpacker(pckt_received)
    return number_seq_received == number_seq

#Garante que os dados não terão tamanho maior 
#que o limite máximo do payload
def resize_msg(byte_msg):
    global PAYLOAD
    if len(byte_msg) > PAYLOAD:
        msg = byte_msg[0:PAYLOAD]
    else:
        msg = byte_msg
    return msg

#Envia a mensagem RDT
def rdt_send(sockd, peer_addr, byte_msg):
    global PAYLOAD, HEADER_SIZE, num_seq_sended, num_last_ack

    #Garante que a mensagem não será maior que o payload
    msg = resize_msg(byte_msg)

    #Cria o pacote RDT
    pckt_send = make_packet(num_seq_sended, msg)

    #Tenta enviar a mensagem para o outro cliente
    try:
        sent_lenght = sockd.sendto(pckt_send, peer_addr)
    except socket.error as error_msg:
        print("Erro ao enviar o pacote: ", error_msg)
        return -1
    print(f"Pacote com Seq [{num_seq_sended}] e tamanho [{sent_lenght}] enviado!")

    #Espera um ack ou um timeout
    sockd_list = [sockd]
    ack_received = False
    
    #Loop para espera da chegada do ack
    while not ack_received:
        is_time, _, _ = select.select(sockd_list, [], [], TIMEOUT)

        #Verifica se deu timeout
        if is_time:
            try:
                msg_received = udt_receive(sockd, PAYLOAD + HEADER_SIZE)
            except socket.error as error_msg:
                print("Erro ao receber ACK: ", error_msg)
                return -1

            #Se o ACK estiver corrompido ou com sequência errada espera até timeout
            if is_corrupted(msg_received) or is_ack(msg_received, 1 - num_seq_sended):
                print("Erro: ACK corrompido ou com número de sequência errado")

            #Recebeu o ack esperado
            elif is_ack(msg_received, num_seq_sended):
                print(f"ACK com Seq [{num_seq_sended}] recebido!")
                
                #Atualiza o número de sequência
                num_seq_sended ^= 1
                return sent_lenght - HEADER_SIZE

        #Deu timeout
        else:
            print("Timeout!")
            
            #Tenta retransmitir o pacote
            try:
                sent_lenght = sockd.sendto(pckt_send, peer_addr)
            except socket.error as error_msg:
                print("Erro ao retransmitir pacote: ", error_msg)
                return -1
            (_), payload = unpacker(pckt_send)
            print(f"Pacote com Seq [{num_seq_sended}] e tamanho [{sent_lenght}] reenviado!")

#Fica esperando a mensagem do outro lado
def rdt_recv(sockd, peer_addr, length):
    global num_seq_received, HEADER_SIZE, num_last_ack

    expected_data_received = False
    #Loop enquanto não receber pacote
    while not expected_data_received:

        #Tenta receber um pacote
        try:
            pckt_received = udt_receive(sockd, length + HEADER_SIZE)
        except socket.error as error_msg:
            print("Erro ao receber pacote: " + error_msg)
            return b''

        #Se o pacote tiver corrompido ou com número de sequência errado reenvia o ACK
        if is_corrupted(pckt_received) or seq_verifier(pckt_received, 1 - num_seq_received):
            print(f"Pacote com Seq [{num_seq_sended}] e tamanho [{sent_lenght}] corrompido ou com número de sequência errado!")

            #Envia ACK com número de sequência anterior
            ack_send = make_ack(1 - num_seq_received)
            try:
                sockd.sendto(ack_send, peer_addr)
            except socket.error as error_msg:
                print("Erro ao enviar ACK anterior: " + error_msg)
                return b''

            #Atualiza o número de sequência do último ACK
            num_last_ack = 1 - num_seq_received
            print(f"ACK com Seq [{1 - num_seq_sended}] enviado!")
            
        #Se o pacote recebido tiver o número de sequência correto envia o ACK
        elif seq_verifier(pckt_received, num_seq_received):
            (_), payload = unpacker(pckt_received)
            print(f"Pacote com Seq [{num_seq_received}] e tamanho [{len(pckt_received)}] recebido!")

            #Tenta enviar o ACK
            try:
                sockd.sendto(make_ack(num_seq_received), peer_addr)
            except socket.error as error_msg:
                print("Erro ao enviar o ACK: " + str(error_msg))
                return b''
            print(f"ACK com Seq [{num_seq_received}] enviado!")

            #Atualiza o número de sequência do último ACK
            num_last_ack = num_seq_received

            #Atualiza o número de sequência
            num_seq_received ^= 1  # Flip seq num
            return payload