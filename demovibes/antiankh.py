import string, enchant

enchant_dict = enchant.Dict("en_US")

common_word_replacements = {"ta'": "to", "2": "to", "ta": "to", "u": "you", "ya": "you", "4": "for", "w/": "with", "w/o": "without", "w/out": "without", "k": "ok", "ppl": "people", "iv": "i've", "off-line": "offline", "on-line": "online", "&": "and", "n'": "and", "'em": "them", ":up:": "", "bro": "", ":love:": "", ":heart:": "", "tha": "the", "prolly": "probably"}
def replace_word(token):
	# if crazy "MWHWMWHMWHMWHW" word  (credits to sqrmax):
	if len(token) > 4 * len(set(token)):
		return ""
	# if sane word:
	last = ""
	if token[-1] in (".", "!", "?", ","):
		last = token[-1]
		token = token[:-1]
	if token in common_word_replacements.keys():
		token = common_word_replacements[token]
	return token + last

def deZeeZeeFy(token):
	if len(token) > 2 and token[0] == token[1] == "z":
		return "s" + token[2:]
	return token

def cap(token):
	if token.isupper():
		return token
	return token.capitalize()

def suggest(token):
	rep = string.replace(token, "z", "s")
	if token.isalpha() and enchant_dict.check(rep) == True:
		return rep
	return token

def antiankhalizer(s):
	tokens = s.split()
	tokens = [suggest(deZeeZeeFy(replace_word(t.lower()))) for t in tokens]
	string = " ".join(tokens)
	return string
