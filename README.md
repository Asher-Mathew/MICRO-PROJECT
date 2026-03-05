Campus Emergency Supply Distribution Optimization

This project focuses on solving an optimization problem related to the distribution of emergency supplies across campus facilities. The model uses Mixed Integer Linear Programming (MILP) and is implemented in Python using the PuLP optimization library.

Objective

The main goal of the project is to minimize the total annual cost involved in supplying emergency materials while ensuring that the following conditions are satisfied:

Demand requirements of each facility

Capacity limitations of warehouses

Overall budget constraints

Tools Used

The project was developed using the following tools:

Python

PuLP

Pandas

How to Run

Install the required dependencies:

pip install pandas pulp

Run the optimization script:

python src/optimization.py
Output

After execution, the program determines:

The optimal warehouses to use

The quantity of supplies shipped to each facility

A detailed cost breakdown including transportation, construction, and operational costs
