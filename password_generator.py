import random

numbers = ['1','2','3','4','5','6','7','8','9','0']
alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'] 


def random_generator(n:int, universe:list) -> str:
	'''
	generates a string of length n where each
	character is an element of the universe
	'''
	if len(universe) == 0:
		return ""

	retval = ""
	for i in range(n):
		retval += random.choice(universe)
	return retval	

def password_generate(n:int = 5) -> str:
	'''
	used to generate a password.
	returns a string of size n 
	'''
	return random_generator(n,numbers)

def short_id_generator(n:int = 5) -> str:
	return random_generator(n,alpha) 
