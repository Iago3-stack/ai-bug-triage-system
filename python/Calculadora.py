# calculadora python com custontkinter
import re
import customtkinter as ctk

# Define a aparência padrão (dark, light, system)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class Calculator:
    def __init__(self, master):
        self.master = master
        master.title("Calculadora CustomTkinter")
        master.geometry("300x400")

        # Campo de entrada (display)
        self.display = ctk.CTkEntry(master, font=("Arial", 24), justify="right")
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Configuração para que os botões se expandam com a janela
        master.grid_columnconfigure((0, 1, 2, 3), weight=1)
        master.grid_rowconfigure((1, 2, 3, 4, 5), weight=1)

        # Botões
        buttons = [
            '7', '8', '9', '÷',
            '4', '5', '6', '×',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]

        row_val = 1
        col_val = 0
        for button in buttons:
            if button == 'C':
                action = self.button_clear
            elif button == '=':
                action = self.button_equal
            else:
                action = lambda x=button: self.button_click(x)
            
            ctk.CTkButton(master, text=button, command=action, font=("Arial", 18)).grid(row=row_val, column=col_val, padx=5, pady=5, sticky="nsew")
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

    def button_click(self, item):
        self.display.insert("end", item)

    def button_clear(self):
        self.display.delete(0, "end")

    def button_equal(self):
        try:
            # Replace visual operators with Python operators for evaluation
            expression = self.display.get().replace("÷", "/").replace("×", "*")
            result = str(eval(expression))
            self.button_clear()
            self.display.insert(0, result)
        except Exception as e:
            self.button_clear()
            self.display.insert(0, "Erro")

if __name__ == "__main__":
    app = ctk.CTk()
    calc = Calculator(app)
    app.mainloop()
