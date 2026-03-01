import os
import glob

startDir = os.getcwd()
systemDirs=glob.glob(startDir+"/*t5a*/")
print(systemDirs)
for i in range(len(systemDirs)):
    #Reset directory to startDir
    os.chdir(startDir)
#    os.system("cd "+startDir)
    os.chdir(systemDirs[i])
#    os.system("cd "+systemDirs[i])
    for j in range(10):
        print(os.getcwd())
        os.chdir(str(j))
        print(os.getcwd())
#        os.system("cd "+str(j))
        os.system("printf '1\n0' | gmx trjconv -s nptPR.tpr -f traj_comp_full_skip100.xtc -pbc whole -center") # Input command here
        os.chdir("..")
#        os.system("cd ..")
    os.chdir("..")
#    os.system("cd ..")
os.chdir(startDir)
