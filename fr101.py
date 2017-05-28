import requests,random,string,bs4,pickle,argparse

random_str=lambda l,ch :"".join([random.choice(ch) for i in range(l)])
random_mail=lambda :random_str(10,string.ascii_lowercase)+"."+random_str(10,string.ascii_lowercase)+"@gmail.com"
random_user=lambda :random_str(random.randint(3,15),string.ascii_letters+string.digits)
random_pass=lambda :random_str(random.randint(6,15),string.ascii_letters+string.digits)

def get_user_id(ses):
    t=ses.get("http://www.france-ioi.org/index.php").text
    b=t.index("idUser")
    id=""
    while t[b]!=";":
        b+=1
        if t[b] in string.digits:
            id+=t[b]
    return id


parser = argparse.ArgumentParser()
parser.add_argument("-D","--dump", help="Just dump know answers.",action="store_true")
group = parser.add_mutually_exclusive_group()
group.add_argument("-C","--create-account", help="Create an account to fill with the wanted data.",action="store_true")
group.add_argument("-g","--get-newanswers", help="Get unknown answers from the account.",action="store_true")
parser.add_argument("-c","--fill-courses", help="Mark courses as read.",action="store_true")
parser.add_argument("-s","--fill-solutions", help="Completes all of the known answers. (you can't if you never saw the chapter...)",action="store_true")
parser.add_argument("-l","--language", help="Chose the language of the answers.")
parser.add_argument("-x","--specific", help="Specify chap/course. (\"<chap>/<course>\")")
parser.add_argument('user', nargs='?', default=random_user())
parser.add_argument('password', nargs='?', default=random_pass())
parser.add_argument('email', nargs='?', default=random_mail())
args = parser.parse_args()

# PARAMS
ACC_CREATION=args.create_account
FILL_COURSES=args.fill_courses
FILL_SOLUTIONS=args.fill_solutions
CHOSEN_LANG=args.language
GET_NEW_SOLS=args.get_newanswers
USER = args.user
PASSWORD = args.password
EMAIL = args.email

if args.dump:
    file = open("knownsolutions.dump", "rb")
    solutions = pickle.load(file)
    print("[+++]", len(solutions), "solutions are known.")
    file.close()
    for sol in solutions:
        if CHOSEN_LANG:
            if sol[2]!=CHOSEN_LANG:
                continue
        if args.specific:
            if args.specific!=sol[0]+"/"+sol[1]:
                continue
        print("[+++] Chp:"+sol[0]+"/Crs:"+sol[1]+"-"+sol[2]+"\n"+sol[3])
    exit()

# init
print("[+++] Init...")
ses=requests.session()


print("[+++] Setting...")
# connection
if ACC_CREATION:
    file=open("accounts_created.lst","a")
    file.write("Username : "+USER+"\nPassword : "+PASSWORD+"\nEmail : "+EMAIL+"\n\n")
    file.close()
    ses.post("http://www.france-ioi.org/user/inscription.php",{"sEmail":EMAIL,"sLogin":USER,"sPasswd1":PASSWORD,"sPasswd2":PASSWORD,"bRegister":"Valider+l'inscription"})
    print("[+++] Username : "+USER)
    print("[+++] Password : "+PASSWORD)
    print("[+++] Email : "+EMAIL)
else:
    ses.post("http://www.france-ioi.org/index.php", {"sLogin":USER,"sPassword":PASSWORD,"bLogin":"Se+connecter"})

if not "menu-deconnect" in ses.get("http://www.france-ioi.org/index.php").text:
    print("[!!!] Login error !")
    exit(-1)

print("[+++] Getting chapters...")
# getting available chapters
soup=bs4.BeautifulSoup(ses.get("http://www.france-ioi.org/algo/chapters.php").text, "lxml")
div=soup.find("div", { "id" : "progressionTabs" })
soup2=bs4.BeautifulSoup(str(div), "lxml")
chaps=[]
print("[+++] Analyzing...")
for found in soup2.find_all("a",href=True):
    ex="http://www.france-ioi.org/algo/chapter.php?idChapter="
    if found["href"].startswith(ex):
        if not found["href"][len(ex):] in chaps:
            chaps.append(found["href"][len(ex):])
print("[+++] Chapters:"," ; ".join(chaps))
if FILL_COURSES:
    print("[+++] Getting courses...")
    # filling data
    courses=[]
    for chap in chaps:
        courses.append([])
        soup = bs4.BeautifulSoup(ses.get("http://www.france-ioi.org/algo/chapter.php?idChapter="+chap).text, "lxml")
        div = soup.find("div", {"class": "chapter"})
        soup2 = bs4.BeautifulSoup(str(div), "lxml")
        for found in soup2.find_all("a", href=True):
            ex = "http://www.france-ioi.org/algo/course.php?idChapter="+chap+"&idCourse="
            if found["href"].startswith(ex):
                if not found["href"][len(ex):] in courses[-1]:
                    courses[-1].append(found["href"][len(ex):])
    print("[+++] Courses:"," ; ".join(str(item) for coursess in courses for item in coursess))

    print("[+++] Filling data...")
    for i in range(len(chaps)):
        chap=chaps[i]
        acourses=courses[i]
        for cour in acourses:
            if args.specific:
                if args.specific != chap + "/" + cour:
                    continue
            soup = bs4.BeautifulSoup(ses.get("http://www.france-ioi.org/algo/course.php?idChapter=" + chap + "&idCourse="+cour).text, "lxml")
            for form in soup.find_all("form"):
                if form["action"].startswith("course.php?idChapter="):
                    ses.post("http://www.france-ioi.org/algo/"+form["action"],{"bRead":"Marquer+comme+lu+et+continuer"})
        print("[---] "+str(int(i/len(chaps)*100))+"%...",end="\r")

if FILL_SOLUTIONS:
    print("[+++] Loading solutions...")
    # sols=[[idChapter,idTask,sLangProg/sExtension,code], ...]
    file=open("knownsolutions.dump","rb")
    sols=pickle.load(file)
    file.close()
    print("[+++] Filling known solutions ! ("+str(len(sols))+" found)")
    # Filling solutions
    for sol in sols:
        if CHOSEN_LANG:
            if sol[2]!=CHOSEN_LANG:
                continue
        if args.specific:
            if args.specific != sol[0] + "/" + sol[1]:
                continue
        ses.head("http://www.france-ioi.org/algo/task.php?idChapter="+sol[0]+"&idTask="+sol[1])
        ses.post("http://www.france-ioi.org/algo/editorAjax.php?sAction=save&idChapter="+sol[0]+"&idTask="+sol[1],{"json":"{\"sources\":{\"Code1\":{\"sSource\":\""+sol[3].replace("\"","\\\"")+"\",\"sLangProg\":\""+sol[2]+"\"}},\"tests\":{},\"bBasicEditorMode\":1,\"idUser\":"+get_user_id(ses)+"}"})
        ses.post("http://www.france-ioi.org/algo/evaluation.php?idChapter="+sol[0]+"&idTask="+sol[1]+"&bEvaluate=1&sOnlyBlock=mainContent",{"bNoSave":"0","sSourceContents":sol[3],"sExtension":sol[2]})
        ses.head("http://www.france-ioi.org/algo/task.php?idChapter="+sol[0]+"&idTask="+sol[1]+"&sTab=correction&sOnlyBlock=mainContent")
        print("[+++] Done : chap:" + sol[0] + ", task:" + sol[1] + ", lang:" + sol[2], end="\r")

if GET_NEW_SOLS:
    # Looking for unknown solutions
    print("[+++]  Looking for unknown solutions...")
    found_solutions=[]
    for chap in chaps:
        soup=bs4.BeautifulSoup(ses.get("http://www.france-ioi.org/algo/chapter.php?idChapter="+chap).text,"lxml")
        for div in soup.find_all("div"):
            if div.has_attr("class"):
                if "chapter-task-row" in div["class"]:
                    soup2=bs4.BeautifulSoup(str(div),"lxml")
                    img=soup2.find("img")
                    if img.has_attr("title"):
                        if "Termin" in img["title"]:
                            a=soup2.find("a", href=True)
                            ex="http://www.france-ioi.org/algo/task.php?idChapter="+chap+"&idTask="
                            if a["href"].startswith(ex):
                                task=a["href"][len(ex):]
                                if args.specific:
                                    if args.specific != chap + "/" + task:
                                        continue
                                print("[+++] Found a solution : chap:"+chap+", task:"+task,end="\r")
                                found_solutions.append([chap,task])

    file = open("knownsolutions.dump", "rb")
    new_sols = pickle.load(file)
    print("[+++]",len(new_sols),"solutions are known.")
    file.close()
    print("[+++] Getting solution data...")
    for sol in found_solutions:
        idChapter=sol[0]
        idTask=sol[1]
        soup=bs4.BeautifulSoup(ses.get("http://www.france-ioi.org/algo/task.php?idChapter="+idChapter+"&idTask="+idTask+"&sTab=correction&sOnlyBlock=mainContent").text,"lxml")
        for div in soup.find_all("div"):
            ss=bs4.BeautifulSoup(str(div),"lxml")
            if div.has_attr("lang") and ss.find("pre") is not None:
                lang=div["lang"]
                s=[sol[0],sol[1],lang,str(ss.find("pre").contents[0])]
                is_already_found=False
                for old_sol in new_sols:
                    if old_sol[0]==s[0] and old_sol[1]==s[1] and old_sol[2]==s[2]:
                        is_already_found=True
                if not is_already_found:
                    print("[+++] Done : chap:" + s[0] + ", task:" + s[1] + ", lang:"+s[2],end="\r")
                    new_sols.append(s)

    file = open("knownsolutions.dump", "wb")
    pickle.dump(new_sols, file)
    file.close()
