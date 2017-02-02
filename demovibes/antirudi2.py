import random
import logging

log = logging.getLogger("dv.antirudi2")

def rudiger_as_himself():
        words = ["ape", "aping", "ork", "orkuses", "eberers", "dragons", "unlike real NORSK!!", "to kyrandia", "at THE CENTRAL", "bastardadminfromhell", "apewashing", "meesdorf", "i give you all a HOUSEFORBID!", "meesdorf.rangers", "you banned me", "VIKING H41L", "laming apes", "from melle", "i don't listen to", "don't count on", "nonnoonono", "bastards", "these nuts like to be rangers?", "they are not even \"center of wizdom\"", "what about releasing,", "they are sometimes this - sometimes that", "i was there for agent reasons!", "likes to ban my account", "ordr", "hndrsn is their leadr", "THE DOGS BELONG TO", "THEIR FALSENED INNERMINISTER", "likes to lock me away", "they have no choice then giving up!", "even if THEY give all", "M923YYK or LRSY22", "and TWY36", "or VKARW or 6S5NVQ", "and QMY6R, 7NV18", "SW4WYC gets me out!", "ART6Z2R & 41912", "WMX82JY brought me 2", "XSX3U87", "the situation NOW", "4Z697", "I SHOT THIS GALLERY", "AND THE DOUBLEHOUSE IS OF THE LEFT SIDE", "ETC - FOR MORE INFORMATION", "PERHAPS SOON @", "with this photos you have the key knowledge", "i made it EXCLUSIVELY to a \"life-experiment\"", "and also the police appeared", "officer houses included", "MAKE YOUR OWN THOUGHT ABOUT THIS", "wannabe-europeans", "NO ILLEGAL ALIEN-SMUGGLING-GANG AROUND OUR ARMY", "thats not a \"fishys\" life", "that like to ape", "1 goal for", "to get the curse out for a longer while!", "stupidest camel", "but we ARENOT", "primal fear got the rangers", "DESTRUCTION ALLY-GATOR!", "NO, I give you NOTHING!", "do we DANCE after a little ALLIGATOR", "thats the hex!", "king for a day?", "slays, not dance with alligators", "let it crack", "BEGIN TO KNOW WHAT REAL", "ASGAARD WAS ALWAYS MY HOME.", "TODAY WILL OVERTAKE \"PRIMAL FEAR\"", "AGAIN ON \"FALSING POSITION\" !", "OUT NOW!", "looking like ....", "this music makes you .... !", "that like to falsen into the haters hand", "going to", "think that", "this is", "now i have the firmware update", "is ruling? haha really no...", "inside the gates", "in norge behind that", "deceiving with false talk... !", "then all the orkus scum they brought.", "but", "ya...", "as a \"nextstep\"", "*whythiskspalwaysonmylawn*?", "the documentation shows", "in reality beeing", " we have to think with MYTH", "more into categories!", "that they brithorns", "have no judge", "is something uncommon - even for", "//><\\\\", "the traincontroller told me", "a skinheqdqorkeralike Kind", "to not to endanger the whole mission", "i made a flawless mission", "was hammered down from friedrich,", "innerminister of germany,", "they dont accept my UPSsending, but", "they know their enemies", "NUMBER OF A CORRESPONDATION 8MULXW", "i photograped the falsedriver in a peniscar...", "marches in enemy territory", "next chapter opened!", "todaysworld, failure?", "JAILBRAIK AND ROOTING IS ILLEGAL?", "IS THAT YOU?", "ILLEGAL - dont Trust HIM", "fight in the subtrain"]
        res = random.sample(words,8)
        if random.randint(0,10) < 5:
                pic = random.choice(["> http://imgur.com/2li66ce", "> http://imgur.com/x5EnGXe", "http://imgur.com/OdRgp2q"])
                res.append(pic)
        if random.randint(0,10) < 4:
                if random.randint(0,10) < 1:
                        res.append(")))))))))))")
                sig = random.choice(["rogermiller1911/meesdorf.rangers", "rm1911/meesdorfrangers"])
                res.append(sig)
        return " ".join(res)
 
def rudiger_as_derp():
        words = ["ehrp", "hurr", "durr", "derp", "eberers", "herp", "ork","herseferbehrd", "ferm merlle", "vehrkerngs", "hurr derp", "hurr durr", "herp derp", "ermegheerd", "meersderp", "eh geehrf teh HEHRSVERBEHRT", "ehrkers", "buhrstehrds", "drehgehrns", "NUHRRSK!!", "mehrrsdehrp", "rehrngehrs", "hue hue", "shuashuashua", "huehuehuehuehue", "EHRSGHERDS WERS MEH HERM!!", "KERNG FER DHEY", "ehrlygehrtehh", "thert leik teh ahrp", "ehr gerf u nerhffeng"]
        res = random.sample(words,5)
        if random.randint(0,10) < 4:
                res.append(random.choice(["> http://imgur.com/WyztP2Z", "http://imgur.com/OdRgp2q"]))
                if random.randint(0,10) < 7:
                        res.append("rehrm1352/mehrsdehrffrehrngehrs")
        return " ".join(res)
 
def rudiger(line, data):
        seed = data.added.microsecond + data.added.second + (data.added.minute * 60) + (data.added.hour * 3600)
        log.debug("Seed : %s, line: %s", seed, line)
        random.seed(seed)
        return random.choice([rudiger_as_derp(), rudiger_as_himself()])
