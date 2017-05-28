import pickle
# [chap,course,lang,from,to]
# (lang="*" -> for all lang)
to_patch=[["646","1947","*","Allez-vous-en","Allez-vous en"],]
file=open("knownsolutions.dump","rb")
old=pickle.load(file)
file.close()
new_sols=[]
for sol in old:
    csol=sol
    for nsol in to_patch:
        v=sol[2]==nsol[2]
        if nsol[2]=="*":
            v=True
        if sol[0]==nsol[0] and sol[1]==nsol[1] and v:
            oc=csol[3]
            csol[3]=csol[3].replace(nsol[3],nsol[4])
            print("[+++] Patched :\n"+oc+"\n[+++] To :\n"+csol[3])
            break
    new_sols.append(csol)
file=open("knownsolutions.dump","wb")
pickle.dump(new_sols,file)
file.close()
