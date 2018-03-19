# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

People Freight Integration Transportation
MILP Implementation

### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies

    * Gurobi and Anaconda for Windows
        1) Download and install Anaconda
            http://www.gurobi.com/downloads/get-anaconda
        
        2) Install Gurobi into Anaconda

            The next step is to install the Gurobi package into Anaconda.
            You do this by first adding the Gurobi channel into your 
            Anaconda platform and then installing the gurobi package from 
            this channel.

            From an Anaconda terminal issue the following command to add 
            the Gurobi channel to your default search list:

            conda config --add channels http://conda.anaconda.org/gurobi
            
            Now issue the following command to install the Gurobi package:
            conda install gurobi
            
            You can remove the Gurobi package at any time by issuing the command:
            conda remove gurobi

        3) Install a Gurobi License
            
            The third step is to install a Gurobi license (if you haven't 
            already done so). You are now ready to use Gurobi from within 
            Anaconda.

* Database configuration
* How to run tests
* Deployment instructions

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact