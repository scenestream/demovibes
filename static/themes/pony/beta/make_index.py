import os

files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith(".css")]

link = "<li><a href='%s'>%s</a></li>\n"
h = """<html><head><title>CSS</title></head><body>
<h3>CSS experiments:</h3>
<ul>
"""

links = [link % (x, x) for x in files]

f = """
</ul>
<h3>Source</h3>
<p><a href="pony.zip">pony.zip</a></p>
<p>It's in <a href="http://sass-lang.com/">SCSS</a> format, you can f.x use <a href="http://koala-app.com/">Koala</a> to compile</p>
</body></html>"""

o = open("index.html", "w")
o.write(h + "".join(links) + f)
o.close()
