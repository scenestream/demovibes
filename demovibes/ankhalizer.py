import string, random

common_word_ending_replacements = {}

random_insertions = ["(", "\""]
def random_insert(tokens):
        if random.random() < 0.1:
                i = random.randint(0,len(tokens)-1)
                tokens[i] += random.choice(random_insertions)
        return tokens

def fix_word(word):
        if word[-1] in (",", "!", ";") or (word[-1] == "." and random.random() > 0.4):
                return word[:-1]
        return word

common_word_replacements = {"To": ["Ta'", "2"], "You": ["U", "Ya"], "For": ["4"], "With": ["W/"], "Without": ["W/O", "W/Out"], "Ok": ["K"], "People": ["PPL", "Ppl"], "I've": ["Iv"], "I": [""], "The" : [""], "Offline": ["OFF-line"], "Online": ["ON-line"], "And": ["&", "N'"], "Them": ["'Em"], "A": [""]}
def replace_word(token):
        if token in common_word_replacements.keys():
                reps = common_word_replacements[token]
                for r in reps:
                        if random.random() > 0.3:
                                return r
        return token

def replace_word_endings(token):
        return token

def ZeeZeeFy(token):
        if token[-1] == "?":
                token += ("?" * random.randint(0, 3))
        if token[0] == "S":
                return "ZZ" + token[1:]
        return token

vowels = "aeiouyw"
def messUpVowels(token):
        res = ""
        for char in token:
                if char in vowels:
                        if random.random() < 0.005:
                                res += (char * random.randint(0,2))
                        elif random.random() < 0.005:
                                res += char + random.choice(vowels)
                        else:
                                res += char
                else:
                        res += char
        return res
                        
random_endings = [" :)", " :love:", " :up:", " Bro", ", Bro :love:"]
def random_add(string):
        if string[-1][-1].isalpha() and random.random() > 0.7:
                r = random.randint(0, len(random_endings) - 1)
                return string + random_endings[r]
        return string

def cap(token):
        if token.isupper():
                return token
        return token.capitalize()

def ankhalizer(s):
        tokens = s.split()
        tokens = [cap(fix_word(t)) for t in tokens]
        tokens = [replace_word(t) for t in tokens]
        #tokens = replace_word_endings(tokens)
        tokens = [replace_word_endings(messUpVowels(ZeeZeeFy(t))) for t in tokens if len(t) > 0]
        tokens = random_insert(tokens)
        string = " ".join(tokens)
        string = random_add(string)
        return string

# call ankhalizer() on a string
