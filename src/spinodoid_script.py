import torch
import numpy as np
import pandas as pd
import random
import os
import subprocess
import logging
import scipy.io as sio
import shutil

logger = logging.getLogger(__name__)
from utility import utility_functions

class Spinodoid_function:
    def __init__(self, train_x, train_y, path_to_spinodal_resources, path_to_GIBBON, hydra_output_directory, output_columns, batch_size, tkwargs, apply_transform, apply_densification_filter):
        self.dim = train_x.size(dim=1)
        self.bounds = torch.tensor([[0.3, 0, 0, 0], [0.6, 90, 90, 90]]).to(**tkwargs) 
        self.ref_point = torch.tensor([-10, -0.3]).to(**tkwargs) # -5, -0.3
        self.num_objectives = train_y.size(dim=1)
        self.path_to_spinodal_resources = path_to_spinodal_resources
        self.tkwargs = tkwargs
        self.hydra_output_directory = hydra_output_directory
        self.path_to_GIBBON = path_to_GIBBON
        self.output_columns = output_columns
        self.batch_size = batch_size
        self.apply_transform = apply_transform
        self.apply_densification_filter = apply_densification_filter

    def evaluate(self, x, batch_id, iteration_number, mode):
        global JOB_ID, SGE_TASK_ID
        if mode == 'cluster':
            JOB_ID = os.environ.get("JOB_ID")
            SGE_TASK_ID = batch_id
        elif mode == 'local':
            JOB_ID = 0
            SGE_TASK_ID = 0
        
        work_directory = os.path.join(self.hydra_output_directory, f"iteration_{iteration_number}/batch_{SGE_TASK_ID}")
        
        if not os.path.exists(work_directory):
            shutil.copytree(src=self.path_to_spinodal_resources, dst=work_directory)
        
        temp_directory = self.path_to_GIBBON + f"/data/temp_{JOB_ID}_batch_{SGE_TASK_ID}_iter_{iteration_number}"

        if not os.path.isdir(temp_directory):
            os.mkdir(temp_directory)

        sio.savemat(work_directory + '/temp_directory.mat',
                    {'temp_directory': temp_directory})
        
        x_numpy = x.cpu().detach().numpy()

        with open(os.path.join(work_directory, 'acquisition.txt'), 'w') as f:
            for row in x_numpy:
                f.write(' '.join(map(str, row)) + '\n')

        os.chdir(work_directory)

        matlab_process = subprocess.Popen(["matlab", "-nosplash", "-nodesktop", "-r", "Objective_Spinodoid_Tet; exit"])
        matlab_process.wait()

        output_file_path = os.path.join(work_directory, 'objective_output.csv')

        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            try:
                outputs = pd.read_csv(output_file_path, header=None, delim_whitespace=True)
            except pd.errors.EmptyDataError:
                logger.error(f"Empty data in file: {output_file_path}")
                outputs = pd.DataFrame([["ERROR"] * len(self.output_columns)])  
        else:
            logger.error(f"Output file missing or empty: {output_file_path}")
            outputs = pd.DataFrame([["ERROR"] * len(self.output_columns)]) 

        if outputs.empty:
            logger.error("No valid output data found, filling with 'ERROR'")
            outputs = pd.DataFrame([["ERROR"] * len(self.output_columns)])

        # objectives = utility_functions.output_transform(outputs, self.apply_transform).to(**self.tkwargs)
        return x, outputs

    def __call__(self, x):
        return self.evaluate(x)
