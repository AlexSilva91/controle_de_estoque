from reportlab.platypus import Flowable

class SignatureLine(Flowable):
    """
    Classe para desenhar linha de assinatura com legenda abaixo.
    """
    def __init__(self, width=200, height=40, label=""):
        super().__init__()
        self.width = width
        self.height = height
        self.label = label

    def draw(self):
        # Linha horizontal para assinatura
        self.canv.line(0, self.height - 20, self.width, self.height - 20)
        # Texto legenda abaixo da linha, centralizado
        self.canv.setFont("Helvetica", 10)
        self.canv.drawCentredString(self.width / 2, self.height - 35, self.label)