# InvDes_BO
**Open-source Code for Multi-fidelity Bayesian Inverse Design of Spinodoid Cellular Materials**

First author: **Hirak Kansara**, contribution author: Leo Guo, Corresponding author: **Dr Wei Tan (wei.tan@qmul.ac.uk)**

This repository introduces a multi-fidelity Bayesian optimisation (InvDes) framework for inverse design of spinodoid structures—scalable, non-periodic topologies with efficient stress distribution—to enhance crush energy absorption under impact. The framework addresses the challenge of balancing conflicting objectives: maximising energy absorption while minimising peak forces, accounting for non-linear material behavior and plastic deformation. By integrating finite element analysis (FEA) with Bayesian optimisation, it efficiently navigates the design space, reducing computational costs compared to conventional methods (e.g., NSGA-II). Key features include:

By integrating information from multiple fidelity sources and scalarising the response using a similarity score, the framework enables efficient exploration of the design space while reducing reliance on costly evaluations. 

Ideal for real-world structural/material optimisation where complex trade-offs and non-linear dynamics are critical.

<img width="3092" height="2114" alt="1-s2 0-S1359836826003616-gr1_lrg" src="https://github.com/user-attachments/assets/7e4cc90b-f70e-41b5-8c5f-8e20ac04f150" />

Figure 1: Workflow for inverse design using multi-fidelity Bayesian optimisation.

<img width="2744" height="3448" alt="1-s2 0-S1359836826003616-gr7_lrg" src="https://github.com/user-attachments/assets/59b28ddf-0351-4801-9f4c-4108da590ce3" />

Figure 2: Summary of inverse design results illustrating the response obtained from four methods across four distinct targets: (a) Target 1, (b) Target 2, (c) Target 3, and (d) Target 4. 


## 🛠 Installation

### **Prerequisites**
- Python 3.8+  
- [pip](https://pip.pypa.io/en/stable/installation/)  
- FEA software (Abaqus)
- MATLAB (Requires the GIBBON library https://github.com/gibbonCode/GIBBON.git and ImageProcessingToolBox)

### **Steps**  
1. **Clone the repository**:  
   ```bash  
   git clone https://github.com/MCM-QMUL/InvDes_GAN.git
   cd InvDes_GAN 
   ```  

2. **Install dependencies**:  
   ```bash  
   pip install -r requirements.txt  
   ```  
   Key packages include:  
   - `numpy`, `scipy`: Numerical operations.  
   - `botorch`, `gpytorch`: Bayesian optimisation.  
   - `pymoo`: Multi-objective optimisation utilities.  

3. **Change directories in**:  
   - config.yaml to define path to the InvDes folder, path to spinodal resources, and path to GIBBON folder
   - InvDes_standalone\spinodal_resources\spinodoid_scripy.py to allow subprocess to call MATLAB.exe file
   - Add path to GIBBON folder in Objective_Spinodoid_Tet.m lines 6 & 7
---

## 🚀 Running Jobs

### **Basic Usage**  
Run the optimisation workflow with:  
```bash  
python main.py
```  

#### **Input Parameters** (edit `config.yaml`)  
- `input_columns`: Design parameters.
- `n_iterations`: Number of InvDes iterations used as stopping criteria
- `kernel`: Type of kernel used for covariance calculation
- `InvDes_type`: InvDes methods as described in the article
- `apply_transform`: If True, scales the objectives for them to be maximised.
  
#### **Output Parameters** (edit `config.yaml`)  
- `output_columns`: Parameters to output, maximised by default
- **Pareto-optimal designs**: Saved to `hydra_output_dir/pareto_front.csv`.
- **Optimisation History**: Saved to `hydra_output_dir/optimisation_history.csv`.  
- **Simulation logs**: Stored in `hydra_output_dir/main.log`.  

### **Example Workflow**  
1. Define objectives in `config.yaml`:  
   ```yaml  
   input_columns:
     - 'Ro'
     - 'Theta_1'
     - 'Theta_2'
     - 'Theta_3'
   output_columns:
     - 'Stress'
   ```  

2. Start optimisation:  # change mode in main.py if running framework either locally or on cluster
   ```bash  
   python main.py  
   ```  

3. Analyse results:  
   - Check the similiariy score 
---

## 💡 Notes  
- **Hardware**: Simulations are computationally intensive. Use HPC/cluster for large-scale runs.  
- **Troubleshooting**:  
  - If FEA fails, check `<job_name>.o<job_id>`.  
  - Mesh density can be changed in /InvDes_standalone/spinodal_resources/Objective_Spinodoid_Tet.m by changing the res variable for faster debugging.

## Reference
If using this code for research or industrial purposes, please cite:

[1] Kansara, H., Guo, L. and Tan*, W., 2026. Inverse design of cellular composites for targeted nonlinear mechanical response via multi-fidelity Bayesian optimisation. Composites Part B: Engineering, p.113740.

## License
MIT
