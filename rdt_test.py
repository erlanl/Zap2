import socket

#macros
PAYLOAD_LIMIT = 10000
TIMEOUT = 0.05
WAIT = 10*TIMEOUT
ACK = 0
DATA = 1

#variáveis globais
__buffer = []
__send_seq = 0 #no. de sequência do emissor
__recv_seq = 0 #no. de sequência do receptor
__last_ACK_seq = None #no. de sequência do último ACK

#segmento
class Packet:
    def __get_checksum(self, data):
        total = 0
        length = len(data)
        i = 0

        while length > 1:
            total += ((data[i+1] << 8) & 0xFF00) + ((data[i]) & 0xFF)
            i += 2
            length -= 2

        if length > 0:
            total += (data[i] & 0xFF)

        while (total >> 16) > 0:
            total = (total & 0xFFFF) + (total >> 16)

        return total & 0xFFFF

    def __init__(self, seq, cat, data):
        self.seq_num = seq
        self.category = cat
        self.payload = data
        self.length = len(data)
        self.checksum = ~(self.__get_checksum(data))

    def extract(self):
        return (self.seq_num, self.category, self.payload, self.length, self.checksum)

#funções para avaliação de segmento
def is_ACK(pkt):
    return pkt.category == ACK

def is_in_sequence(pkt, seq):
    return pkt.seq == seq

def is_corrupted(pkt):
    local_checksum = pkt.__get_checksum(pkt.data)
    return ~(local_checksum + pkt.checksum == 0xFFFF)

#funções rdt
def rdt_send(sock, data):
    global PAYLOAD_LIMIT, DATA, ACK, __send_seq, __buffer, __last_ACK_seq

    assert len(data) <= PAYLOAD_LIMIT

    try: #envia segmento
        udp_send(sock, Packet(__send_seq, DATA, data)) #(proto)
    except socket.error as err:
        print(f"Erro de envio no remetente: {err}")
        return -1

    ACKed = False
    while not ACKed: #espera pelo ACK
        recv = sock.recv() #(proto)
        if recv: #recebeu algo
            try:
                incoming_pkt = udp_recv(sock) #(proto)
            except socket.error as err:
                print(f"Erro de recepção no remetente: {err}")
                return 1
            
            if is_corrupted(incoming_pkt) or (is_ACK(incoming_pkt) and ~is_in_sequence(incoming_pkt, __send_seq)):
                print("Segmento inválido recebido pelo remetente")
            elif is_ACK(incoming_pkt) and is_in_sequence(incoming_pkt, __send_seq): #recebeu ACK esperado
                __send_seq ^= 1
                ACKed = True
            else: #recebeu dados
                if incoming_pkt not in __buffer:
                    __buffer.append(incoming_pkt)

                data_seq = incoming_pkt.seq
                try: #reenvia ACK
                    udp_send(sock, Packet(data_seq, ACK, None)) #(proto)
                except socket.error as err:
                    print(f"Falha do remetente ao reenviar ACK: {err}")
                    return 1
                __last_ACK_seq = data_seq
        else: #timeout
            rdt_send(sock, data)

    return 0

def rdt_recv(sock):
    global ACK, __buffer, __recv_seq, __last_ACK_seq

    while len(__buffer) > 0:
        pkt = __buffer.pop(0)
        if is_in_sequence(pkt, __recv_seq):
            __rcv_seq ^= 1

    received_expected = False
    while not received_expected: #espera pelos dados
        try:
            incoming_pkt = udp_recv(sock) #(proto)
        except socket.error as err:
            print(f"Erro de recepção no destinatário: {err}")
            return 1

        if is_corrupted(incoming_pkt) or ~is_in_sequence(incoming_pkt, __recv_seq):
            print("Segmento inválido recebido pelo destinatário")

            try: #reenvia ACK
                udp_send(sock, Packet(~__send_seq, ACK, None)) #(proto)
            except socket.error as err:
                print(f"Falha do destinatário ao reenviar ACK: {err}")
        elif is_in_sequence(incoming_pkt, __recv_seq): #recebeu dados esperados
            try: #envia ACK
                udp_send(sock, Packet(__recv_seq, ACK, None)) #(proto)
            except socket.error as err:
                print(f"Falha do destinatário ao enviar ACK: {err}")
                return 1

            __last_ACK_seq = __recv_seq
            __recv_seq ^= 1
            return 0
