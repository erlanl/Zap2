from tkinter import *

class GUI:

    def __init__(self, largura, altura):
        self.window = Tk()
        self.window.title("Zap 2")

        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.grid(columnspan = 3)
        self.createWidgets()

    def createWidgets(self):

        self.txt_chat = Text(self.canva, border = 1)
        self.txt_field = Entry(self.canva, width = 85, border = 1, bg = 'white')
        self.send_button = Button(self.canva, text = "Enviar", padx = 40, command = self.send)
        
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

if __name__ == '__main__':
    interface = GUI(1024, 768).start()

