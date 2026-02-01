import json
import os
import re


def input_nonempty(prompt):
	while True:
		v = input(prompt).strip()
		if v:
			return v
		print('Entrada vazia. Tente novamente.')


def input_int(prompt):
	while True:
		try:
			return int(input(prompt))
		except Exception:
			print('Digite um número válido.')


def input_email(prompt):
	pat = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
	while True:
		e = input(prompt).strip()
		if pat.match(e):
			return e
		print('Email inválido. Tente novamente.')


def input_cpf(prompt):
	while True:
		s = re.sub(r'\D', '', input(prompt))
		if len(s) == 11 and s.isdigit():
			return s
		print('CPF inválido. Deve conter 11 dígitos (somente números).')


def input_telefone(prompt):
	while True:
		s = re.sub(r'\D', '', input(prompt))
		if 8 <= len(s) <= 13 and s.isdigit():
			return s
		print('Telefone inválido. Digite somente dígitos (com DDD).')


def main():
	nome = input_nonempty('Qual seu nome? ')
	idade = input_int('Qual sua idade? ')
	ano = input_int('Qual seu ano? ')
	email = input_email('Qual seu email? ')
	cpf = input_cpf('Qual seu CPF? ')
	telefone = input_telefone('Qual seu telefone? ')

	usuario = {
		'nome': nome,
		'idade': idade,
		'ano': ano,
		'email': email,
		'cpf': cpf,
		'telefone': telefone,
	}

	db_path = 'cadastro_usuarios.json'
	try:
		if os.path.exists(db_path):
			with open(db_path, 'r', encoding='utf-8') as f:
				data = json.load(f)
				if not isinstance(data, list):
					data = []
		else:
			data = []
	except Exception:
		data = []

	data.append(usuario)
	with open(db_path, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

	print('\nCadastro salvo em', db_path)
	print('Resumo:', usuario)


if __name__ == '__main__':
	main()
