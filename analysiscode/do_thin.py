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
        os.system("gmx trjconv -f traj_comp_full.xtc -skip 10 -o traj_comp_full_skip10.xtc ") # Input command here
        os.chdir("..")
#        os.system("cd ..")
    os.chdir("..")
#    os.system("cd ..")
os.chdir(startDir)
