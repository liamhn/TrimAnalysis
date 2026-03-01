#1 0 				   #NAME
printf "1\n0" | gmx trjconv -s npt.tpr -f traj_comp.xtc -o firstframe.gro -b 0 -e 2 -center -ur compact -pbc mol

#1 1				   #NAME
printf "1\n1" | gmx trjconv -s npt.tpr -f traj_comp.xtc -o prot-only-firstframe.gro -b 0 -e 2 -center -ur compact -pbc mol

#0
printf "0" | gmx trjconv -f traj_comp.xtc -s firstframe.gro -pbc nojump -o traj_comp2-pbc.xtc

#1 0
printf "1\n0" | gmx trjconv -f traj_comp2-pbc.xtc -s firstframe.gro -fit rot+trans -o traj_comp3-pbc-rt.xtc

#1 1
printf "1\n1" | gmx trjconv -f traj_comp2-pbc.xtc -s firstframe.gro -fit rot+trans -o prot-only-traj_comp3-pbc-rt.xtc



#1 0                               #NAME
printf "1\n0" | gmx trjconv -s npt.tpr -f traj_comp.xtc -o mfirstframe.gro -b 0 -e 2 -center -ur compact -pbc mol

#1 13                               #NAME
printf "1\n13" | gmx trjconv -s npt.tpr -f traj_comp.xtc -o m-only-firstframe.gro -b 0 -e 2 -center -ur compact -pbc mol

#0
printf "0" | gmx trjconv -f traj_comp.xtc -s mfirstframe.gro -pbc nojump -o mtraj_comp2-pbc.xtc

#1 0
printf "1\n0" | gmx trjconv -f mtraj_comp2-pbc.xtc -s mfirstframe.gro -fit rot+trans -o mtraj_comp3-pbc-rt.xtc

#1 13
printf "1\n13" | gmx trjconv -f mtraj_comp2-pbc.xtc -s mfirstframe.gro -fit rot+trans -o m-only-traj_comp3-pbc-rt.xtc
