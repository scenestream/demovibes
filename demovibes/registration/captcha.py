from hashlib import md5
import random

#Example data
KEY = "long_secret_random_key"
TYPES = {
        "category": ["key", "words", "for", "category"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
        "Not configured!": ["Not Configured!"],
}

from captcha_data import KEY, TYPES, S_NUMBERS, S_START, S_PLUS 

class CaptchaChecker(object):
    """
    Generates and verifies captcha codes
    """
    def __init__(self, key):
        self.KEY = key

    def _hash(self, text, r):
        return md5(r + text.strip() + self.KEY).hexdigest()

    def get_code_for(self, text):
        r = str(random.randint(10000, 99999))
        return r + "!" + self._hash(text, r)

    def verify_code(self, text, code):
        r, c = code.split("!")
        return self._hash(text, r) == c


class QaGen(object):
    """
    Generate Questions and Answers for captcha use
    """
    def get_qa(self):
        random.seed()
        q = random.choice(self.TYPES)
        return q(self)
   
    def _types(self):

        T = TYPES.keys()
        random.shuffle(T)
        
        answer = random.choice(TYPES[T[0]])

        L = []
        L.append(answer)
        for x in range(5):
            L.append(random.choice(TYPES[T[x+1]]))
        random.shuffle(L)

        return ("Which of these is %s? %s" % (T[0], ", ".join(L)), answer)

    def _get_number_qa(self):

        n1 = random.randint(0,12)
        n2 = random.randint(0,12)
        
        start = random.choice(S_START)
        plus = random.choice(S_PLUS)
        
        an1 = random.randint(0,1) and n1 or S_NUMBERS[n1]
        an2 = random.randint(0,1) and n2 or S_NUMBERS[n2]

        return ("%s %s %s %s" % (start, an1, plus, an2), str(n1+n2))

    TYPES = [_types]

CC = CaptchaChecker(KEY)
Q = QaGen()

def get_form(forms, data=None):
    """
    Create and return a Django captcha form
    """
    class CaptchaForm(forms.Form):
        answer = forms.CharField(max_length=100)
        code = forms.CharField(max_length=40, widget=forms.HiddenInput())
        
        def auto_set_captcha(self):
            q, a = Q.get_qa()
            self.set_captcha(q, a)

        def set_captcha(self, question, answer):
            self.fields['answer'].label = question
            self.fields['code'].initial = CC.get_code_for(answer)

            if hasattr(self, "data") and self.data:
                if "code" in self.data:
                    self.data["code"] = CC.get_code_for(answer)
                #if "answer" in self.data:
                #    self.data["answer"] = ""

        def clean(self):
            answer = self.cleaned_data.get("answer")
            code = self.cleaned_data.get("code")
            
            if not answer or not code or not CC.verify_code(answer, code):
                raise forms.ValidationError(u'Wrong Answer')
            return self.cleaned_data

    if data:
        return CaptchaForm(data.copy())
    return CaptchaForm()



if __name__ == "__main__":
    s = "test"
    code = CC.get_code_for(s)
    print "code for", s, "is", code
    print "Is correct?", CC.verify_code(s, code)
    print "Is other data correct?", CC.verify_code(s+"a", code)
    for x in range(10): print Q.get_qa()
