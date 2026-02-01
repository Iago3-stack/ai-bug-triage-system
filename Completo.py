import json
from typing import Optional, Any, Dict, List

# --- EXCEÇÕES PERSONALIZADAS DE NÍVEL PROFISSIONAL ---
# Criar exceções específicas facilita o tratamento de erros na camada de interface (Controller/View)
class DataInvalidaError(Exception):
    """Exceção base para erros de validação de dados."""
    pass

class NomeVazioError(DataInvalidaError): pass
class IdadeInvalidaError(DataInvalidaError): pass
class AnoInvalidoError(DataInvalidaError): pass
class ValorInvalidoError(DataInvalidaError): pass
class HorasInvalidaError(DataInvalidaError): pass
class EmpresaVaziaError(DataInvalidaError): pass
class CargoVazioError(DataInvalidaError): pass

class ColetorDeDados:
    """
    CLASSE MODEL PAI: Lida APENAS com armazenamento e validação dos dados (Encapsulamento).
    Não há NENHUMA interação com o usuário (input/print).
    """
    def __init__(self):
        """Inicializa os atributos internos (privados por convenção _)."""
        self._nome: Optional[str] = None
        self._idade: Optional[int] = None
        self._ano: Optional[int] = None
        self._trabalho: Optional[str] = None 
        self._valor: Optional[float] = None
        self._horas: Optional[int] = None
    
    # ----------------------------------------------------
    # ENCAPSULAMENTO: PROPRIEDADES (Getters e Setters com Type Hinting)
    # ----------------------------------------------------

    @property
    def nome(self) -> Optional[str]: return self._nome
    @nome.setter
    def nome(self, novo_nome: str):
        # Type Hinting: o valor de entrada é esperado ser str, mas deve ser verificado
        if not isinstance(novo_nome, str):
            raise NomeVazioError('O nome deve ser uma string de texto.')

        nome_processado = novo_nome.strip()
        if not nome_processado:
            raise NomeVazioError('O campo Nome não pode ficar vazio.')
            
        self._nome = nome_processado.title() 

    @property
    def idade(self) -> Optional[int]: return self._idade
    @idade.setter
    def idade(self, nova_idade: Any):
        # Lógica de Type Casting e Limpeza Profissional (permitindo str ou número)
        valor_a_converter = nova_idade.strip() if isinstance(nova_idade, str) else nova_idade
        
        try: 
            idade_int = int(valor_a_converter) 
        except (ValueError, TypeError): 
            raise IdadeInvalidaError('Idade deve ser um número inteiro válido.')
            
        if idade_int < 18:
            raise IdadeInvalidaError('Idade deve ser maior ou igual a 18 anos.')
        self._idade = idade_int

    @property
    def ano(self) -> Optional[int]: return self._ano
    @ano.setter
    def ano(self, novo_ano: Any):
        # Lógica de Type Casting e Limpeza
        valor_a_converter = novo_ano.strip() if isinstance(novo_ano, str) else novo_ano
        
        try: 
            ano_int = int(valor_a_converter)
        except (ValueError, TypeError): 
            raise AnoInvalidoError('Ano deve ser um número inteiro válido.')
            
        if ano_int < 1900 or ano_int > 2025:
            raise AnoInvalidoError('O ano deve estar entre 1900 e 2025.')
        self._ano = ano_int
        
    @property
    def trabalho(self) -> Optional[str]: return self._trabalho
    @trabalho.setter
    def trabalho(self, nova_empresa: str):
        if not isinstance(nova_empresa, str):
            raise EmpresaVaziaError('O nome da empresa deve ser uma string de texto.')
            
        empresa_processada = nova_empresa.strip()
        if not empresa_processada:
            raise EmpresaVaziaError('O campo Empresa não pode ser vazio.')
            
        self._trabalho = empresa_processada.title()
        
    @property
    def valor(self) -> Optional[float]: return self._valor
    @valor.setter
    def valor(self, novo_valor: Any):
        # Lógica de Type Casting e Limpeza (Tratamento de float, int e string)
        valor_processado = novo_valor
        if isinstance(novo_valor, str):
            valor_processado = novo_valor.strip().replace(',', '.')
        
        try: 
            valor_float = float(valor_processado)
        except (ValueError, TypeError): 
            raise ValorInvalidoError('Valor por hora deve ser um número válido (ex: 7.14).')
            
        if valor_float <= 0:
            raise ValorInvalidoError('O valor por hora deve ser positivo.')
            
        self._valor = valor_float

    @property
    def horas(self) -> Optional[int]: return self._horas
    @horas.setter
    def horas(self, novas_horas: Any):
        # Lógica de Type Casting e Limpeza
        valor_a_converter = novas_horas.strip() if isinstance(novas_horas, str) else novas_horas
        
        try: 
            horas_int = int(valor_a_converter)
        except (ValueError, TypeError): 
            raise HorasInvalidaError('Horas por mês deve ser um número inteiro válido.')

        if horas_int <= 0:
            raise HorasInvalidaError('O número de horas deve ser um valor inteiro positivo.')
            
        self._horas = horas_int
        
    @property
    def total(self) -> float:
        """Propriedade APENAS LEITURA, que calcula o salário."""
        if self._valor is not None and self._horas is not None:
            return self._valor * self._horas
        return 0.0
    
    # ----------------------------------------------------
    # ESTRUTURA DE DADOS (Método de Exportação)
    # ----------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Método de exportação dos dados para formato Dict."""
        # Se algum campo crítico estiver faltando, levante um erro claro
        if None in [self.nome, self.trabalho, self.valor, self.horas]:
            raise DataInvalidaError("Dados essenciais para o relatório estão incompletos.")
            
        return {
            "nome": self.nome,
            "idade": self.idade,
            "ano_nascimento": self.ano,
            "empresa": self.trabalho,
            "ganho_por_hora": self.valor,
            "horas_por_mes": self.horas,
            "salario_total": self.total
        }
    
    # ----------------------------------------------------
    # Método Estático de Relatório (Compartilhado)
    # ----------------------------------------------------

    @staticmethod
    def formatar_e_exibir_relatorio(dados_coletados: Dict[str, Any]):
        """Método estático para exibir qualquer dicionário de forma formatada (reutilizável)."""
        print("\n----------------------------------------------------")
        print("--- RELATÓRIO COMPLETO (DICIONÁRIO / ESTRUTURA DE DADOS) ---")
        print("----------------------------------------------------")
        
        # 1. JSON Formatado
        print("\n[Formato JSON/Dict]:")
        # Usa ensure_ascii=False para exibir caracteres especiais corretamente
        print(json.dumps(dados_coletados, indent=4, ensure_ascii=False))

        # 2. Tabela Formatada
        print("\n[Formato Tabela]:")
        print("-" * 55)
        print(f"{'CAMPO':<35} | {'VALOR':>18}") 
        print("-" * 55)
        
        for chave, valor in dados_coletados.items():
            if isinstance(valor, float):
                 # Formatação de moeda: ex: 1.234,56
                 valor_formatado = f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            elif valor is None:
                 valor_formatado = "Não Informado"
            else:
                 valor_formatado = str(valor)

            campo_formatado = chave.replace('_', ' ').title() 
            print(f"{campo_formatado:<35} | {valor_formatado:>18}")
        print("-" * 55)


class ColetorProfissional(ColetorDeDados):
    """
    CLASSE MODEL FILHA: Herda de ColetorDeDados e adiciona um campo específico.
    (Demonstra HERANÇA).
    """
    def __init__(self):
        # Chama o construtor da CLASSE PAI
        super().__init__()
        self._cargo: Optional[str] = None
        
    # ----------------------------------------------------
    # ENCAPSULAMENTO ADICIONAL (Específico da Classe Filha)
    # ----------------------------------------------------

    @property
    def cargo(self) -> Optional[str]: return self._cargo

    @cargo.setter
    def cargo(self, novo_cargo: str):
        if not isinstance(novo_cargo, str):
            raise CargoVazioError('O cargo deve ser uma string de texto.')
            
        cargo_processado = novo_cargo.strip()
        if not cargo_processado:
            raise CargoVazioError('O campo Cargo não pode ficar vazio.')
            
        self._cargo = cargo_processado.title()

    # ----------------------------------------------------
    # SOBRESCRITA DE MÉTODO (Polimorfismo para Exportação)
    # ----------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Sobrescreve o método do pai para adicionar o campo 'cargo' ao dicionário.
        """
        # 1. Pega o dicionário base da CLASSE PAI
        dados = super().to_dict()
        
        # 2. Adiciona o campo específico da CLASSE FILHA
        dados["cargo_especifico"] = self.cargo
        
        return dados

# aqui vem a segunda parte para estudar em nivel de mercado de trabalho 
from model_data import (
    ColetorProfissional,
    NomeVazioError,
    IdadeInvalidaError,
    AnoInvalidoError,
    ValorInvalidoError,
    HorasInvalidaError,
    EmpresaVaziaError,
    CargoVazioError,
    DataInvalidaError
)
from typing import Callable, Any

# --------------------------------------------------------------------------
# LÓGICA DO CONTROLADOR/INTERFACE (Camada de Interação)
# Esta camada usa input() e print() e chama o Model para realizar a validação
# --------------------------------------------------------------------------

def _perguntar_loop(prompt: str, setter_func: Callable[[Any], None]):
    """
    Função auxiliar genérica que lida com o loop de entrada e tratamento de erro.
    Aceita o 'prompt' para o input e a 'setter_func' (o setter do Model).
    """
    while True:
        try:
            # Pede o input ao usuário
            resposta = input(f'{prompt} ')
            
            # Chama o setter do Model para validar e armazenar
            setter_func(resposta)
            
            # Se não levantou exceção, sai do loop
            break
        except (
            NomeVazioError, 
            IdadeInvalidaError, 
            AnoInvalidoError, 
            ValorInvalidoError, 
            HorasInvalidaError, 
            EmpresaVaziaError, 
            CargoVazioError
        ) as e:
            # Captura a exceção específica do Model e exibe a mensagem amigável
            print(f'\nATENÇÃO: {e}')
        except Exception as e:
            # Captura qualquer outra exceção inesperada
            print(f'\nERRO INESPERADO: {e}')
            
def iniciar_coleta_profissional():
    """
    Controlador principal que orquestra a coleta de dados, separada da lógica do Model.
    """
    print("--- INICIANDO COLETA DE DADOS PROFISSIONAIS (Nível Profissional) ---")
    
    # 1. Cria uma INSTÂNCIA do Model (ColetorProfissional)
    meu_formulario = ColetorProfissional()
    
    # --- FASE 1: DADOS PESSOAIS ---
    print("\n--- FASE 1 (DADOS PESSOAIS) ---")
    _perguntar_loop('Qual o seu nome?', lambda x: meu_formulario.nome(x))
    _perguntar_loop('Qual sua idade?', lambda x: meu_formulario.idade(x))
    _perguntar_loop('Qual seu ano de nascimento?', lambda x: meu_formulario.ano(x))
    
    # --- FASE 2: DADOS PROFISSIONAIS BASE ---
    print("\n--- FASE 2 (DADOS PROFISSIONAIS) ---")
    _perguntar_loop('Qual empresa você trabalha?', lambda x: meu_formulario.trabalho(x))
    _perguntar_loop('Quanto você ganha por hora? (Ex: 7.50)', lambda x: meu_formulario.valor(x))
    _perguntar_loop('Quantas horas você trabalha por mês?', lambda x: meu_formulario.horas(x))
    
    # --- FASE 3: DADOS ESPECÍFICOS DO FILHO (Cargo) ---
    print("\n--- FASE 3 (CARGO ESPECÍFICO) ---")
    _perguntar_loop('Qual é o seu cargo?', lambda x: meu_formulario.cargo(x))

    print("\n--- COLETA CONCLUÍDA ---\n")
    
    # 4. GERAÇÃO E EXIBIÇÃO DO RELATÓRIO
    try:
        # Pede ao Model para exportar os dados (to_dict)
        dados_finais = meu_formulario.to_dict()
        
        # Usa o método estático de formatação do Model para exibir
        ColetorProfissional.formatar_e_exibir_relatorio(dados_finais)

    except DataInvalidaError as e:
        print(f"\n[ERRO FATAL DE DADOS] Não foi possível gerar o relatório. {e}")
        
    # 5. TESTES UNITÁRIOS SIMULADOS (Para mostrar a robustez do Model)
    print("\n----------------------------------------------------")
    print("--- TESTES DE ROBUSTEZ (Model independente do CLI) ---")
    
    # Teste 1: Tenta setar idade inválida diretamente no Model.
    try:
        print("\n[TESTE 1] Tentando setar idade inválida (10)...")
        meu_formulario.idade = 10 
    except IdadeInvalidaError as e:
        print(f"SUCESSO NA VALIDAÇÃO DO MODEL: {e}") 

    # Teste 2: Tenta setar valor por hora válido (50.5 - float).
    try:
        print("\n[TESTE 2] Tentando setar valor por hora (float 50.5)...")
        meu_formulario.valor = 50.5 
        print(f"SUCESSO. Novo valor/hora: R$ {meu_formulario.valor:.2f}") 
        print(f"Novo Salário Total Calculado: R$ {meu_formulario.total:.2f}")
    except Exception as e:
        print(f"ERRO: {e}") 
    
    # Teste 3: Tenta setar valor por hora válido (string com vírgula).
    try:
        print("\n[TESTE 3] Tentando setar valor por hora (string '12,99')...")
        meu_formulario.valor = "12,99"
        print(f"SUCESSO. Novo valor/hora: R$ {meu_formulario.valor:.2f}") 
    except Exception as e:
        print(f"ERRO: {e}") 

# Bloco principal de execução
if __name__ == "__main__":
    iniciar_coleta_profissional()
