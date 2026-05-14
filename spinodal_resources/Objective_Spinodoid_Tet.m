clear; close all; clc;

disp('File read start')
addpath(fullfile('C:/Users/hirak/Desktop/Gibbon/','lib')); 
addpath(fullfile('C:\Users\hirak\Desktop\Gibbon\lib_ext','geogram'));
Cube_Length = 40;
strain = linspace(0,0.5,201)';

if isfile('acquisition.txt') == 1
    fileID = fopen('acquisition.txt','r');
    A = textscan(fileID,'%f %f %f %f %f','delimiter','\t');
    fclose(fileID);

    fileID = fopen('objective_output.csv', 'w');  
    fclose(fileID); 
    
    Input = cell2mat(A(1:4));
    clear A;
    Ro      = Input(1, 1);
    res     = 15; %Input(1, 2);
    Theta_1 = Input(1, 2);
    Theta_2 = Input(1, 3);
    Theta_3 = Input(1, 4);
    spinodoid_generator_Tet
    ASSEMBLY_writer_Hill_PETG;
    clear Elements
    clear Nodes
    disp('Simulation start')
    system(['abaqus job=MAIN double cpus=6 mp_mode=' ...		           % This line calls ABAQUS solver to perform FE simulation.
        'THREADS memory="90 %" parallel=domain interactive ask_delete=OFF'])         
    % This line calls ABAQUS solver to perform FE simulation.
                                                                          
    if isfile('MAIN.sta') == 1
        CHECKER = fileread('MAIN.sta');
        Check = strfind(CHECKER, 'SUCCESSFULLY');
        if isempty(Check) ~= 1
            Force_reader
            clear Elements
            clear Nodes
            writematrix(Stress, 'objective_output.csv');
        else
            clear Elements
            clear Nodes
            writematrix(Stress, 'objective_output.csv');
        end

            clear CHECKER
            clear Check
    else
        clear Elements
        clear Nodes
    writematrix(Stress, 'objective_output.csv');

    end
    % delete Spinodoid_Tet.inp
    delete ASSEMBLY.inp
    delete MAIN.abq
    delete MAIN.com
    delete MAIN.dat
    delete MAIN.mdl
    delete MAIN.msg
    delete MAIN.odb
    delete MAIN.pac
    delete MAIN.prt
    delete MAIN.res
    delete MAIN.sel
    delete MAIN.sta
    delete MAIN.stt
    delete F_Z.rpt
    delete Mass.txt
    % delete ASSEMBLY_writer_Hill_PETG.m
    % delete Force_Extractor.py
    % delete Force_reader.m
    % delete MAIN.inp
    % delete MASS_VOLUME_Extractor.py
    % delete PETG_plastic_compression.csv
    % delete Plate_01.inp
    % delete SETTING.inp
    % delete spinodoid_generator_Tet.m
    % delete temp_directory.mat

else

    writematrix(Stress, 'objective_output.csv');
end

% exit;