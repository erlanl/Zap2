from tkinter import *

class Chat:

    def __init__(self, largura, altura, nome, porta):
        #Declarando as informações da janela
        self.window = Tk()
        self.window.title(f"Chat Aberto - {nome}")
        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.grid(columnspan = 3)
        self.createWidgets()

        #Informações do Usuário
        self.nome = nome
        self.porta = porta

    def createWidgets(self):
        
        #Declarando os widgets do chat
        self.txt_chat = Text(self.canva, border = 1)
        self.txt_field = Entry(self.canva, width = 85, border = 1, bg = 'white')
        self.send_button = Button(self.canva, text = "Enviar", padx = 40, command = self.send)
        
        #Posicionando os Widgets
        self.txt_chat.config(background = "#363636", foreground='white')
        self.txt_chat.grid(column = 0, row = 0, columnspan = 3)
        self.txt_field.grid(column = 0, row = 1, columnspan = 2)
        self.send_button.grid(column = 2, row = 1)

    def send(self, event = None):
        texto = self.txt_field.get() + '\n'
        self.txt_chat.insert(END, texto)
        self.txt_field.delete(0, END)


    def start(self):
        self.window.mainloop()


class Login:

    def __init__(self, largura, altura):
        #Declarando as informações da janela
        self.window = Tk()
        self.window.title("Zap 2")
        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.grid(columnspan = 3)
        self.createWidgets()

        self.texto_nome = ""
        self.texto_porta = ""

    def createWidgets(self):

        #Labels de nome e porta
        self.label1 = Label(self.canva, text="Nome: ", anchor = W)
        self.label2 = Label(self.canva, text="Porta: ", anchor = W)

        #Declarando as áreas de Texto
        self.txt_name = Entry(self.canva, width = 85, border = 1, bg = 'white')
        self.txt_port = Entry(self.canva, width = 85, border = 1, bg = 'white')   

        #Declarando o Botão
        self.send_button = Button(self.canva, text = "Enviar", padx = 40, command = self.send)
        
        #Posicionando os Widgets
        self.label1.grid(column = 0, row = 1, columnspan = 1)
        self.label2.grid(column = 0, row = 5, columnspan = 1)
        self.txt_name.grid(column = 1 , row = 1, columnspan = 3)
        self.txt_port.grid(column = 1, row = 5, columnspan = 3)
        self.send_button.grid(column = 5, row = 1)

    def send(self, event = None):

        #Pegando as infromações de nome e porta e fechando a janela
        self.texto_nome = self.txt_name.get() + '\n'
        self.texto_porta = self.txt_port.get() + '\n'
        self.window.destroy()

    def start(self):
        self.window.mainloop()
        return self.texto_nome, self.texto_porta


