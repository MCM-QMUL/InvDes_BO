% clear all; close all; clc

%%%%%%%%%%%%%%%%%%%%%%%%%% Reading Force %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
force_peak_cube = 80475.8856371; 
EA_cube = 1747052.65623; 

system('abaqus cae noGUI=Force_Extractor');

fileID = fopen(['F_Z.rpt'],'r');
A = textscan(fileID,'%f %f %f','delimiter','\t', 'headerLines', 3);
fclose(fileID);

Force = cell2mat(A(3));

Displacement = cell2mat(A(2))*-1;

Strain = Displacement/Cube_Length;
Stress = Force/Cube_Length/Cube_Length;