class Horario:
    """Representa um horário composto por hora, minuto e segundo.

    Métodos
    -------
    incrementar(segundos)
        Adiciona um número de segundos ao horário, ajustando horas,
        minutos e segundos (com "carry" para cima e wrap em 24h).

    diferenca(outro)
        Retorna a diferença em segundos entre este horário e outro.
    """

    def __init__(self, hora: int = 0, minuto: int = 0, segundo: int = 0) -> None:
        if not (0 <= hora < 24):
            raise ValueError(f"Hora inválida: {hora}")
        if not (0 <= minuto < 60):
            raise ValueError(f"Minuto inválido: {minuto}")
        if not (0 <= segundo < 60):
            raise ValueError(f"Segundo inválido: {segundo}")

        self.hora = hora
        self.minuto = minuto
        self.segundo = segundo

    def __str__(self) -> str:
        # formato HH:MM:SS com zeros à esquerda
        return f"{self.hora:02d}:{self.minuto:02d}:{self.segundo:02d}"

    def to_seconds(self) -> int:
        """Retorna o horário convertido em segundos desde meia-noite."""
        return self.hora * 3600 + self.minuto * 60 + self.segundo

    @classmethod
    def from_seconds(cls, total: int) -> "Horario":
        """Cria um Horario a partir de um total de segundos (0-86399)."""
        total %= 24 * 3600
        h = total // 3600
        total %= 3600
        m = total // 60
        s = total % 60
        return cls(h, m, s)

    def incrementar(self, segundos: int) -> None:
        """Incrementa o horário adicionando o número de segundos fornecido.

        O valor é somado e o resultado "dobra" a cada 24 horas.
        """
        if not isinstance(segundos, int):
            raise TypeError("Segundos deve ser inteiro")

        total = self.to_seconds() + segundos
        novo = self.from_seconds(total)
        self.hora, self.minuto, self.segundo = novo.hora, novo.minuto, novo.segundo

    def diferenca(self, outro: "Horario") -> int:
        """Retorna a diferença absoluta em segundos entre dois horários."""
        if not isinstance(outro, Horario):
            raise TypeError("A diferença só pode ser calculada entre dois Horario")
        return abs(self.to_seconds() - outro.to_seconds())


# Exemplo de uso
if __name__ == "__main__":
    h1 = Horario(2, 30, 15)
    h2 = Horario(1, 15, 50)

    print("h1 =", h1)
    print("h2 =", h2)
    print("Diferença em segundos:", h1.diferenca(h2))

    h1.incrementar(3600 + 30)
    print("h1 após incremento:", h1)
