'''
Copyright 2015 by Tobias Houska
This file is part of Statistical Parameter Estimation Tool (SPOTPY).

:author: Tobias Houska

This example implements the external hydrological model HYMOD into SPOTPY.  
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import numpy as np
try:
    import spotpy
except ImportError:
    import sys
    sys.path.append(".")
    import spotpy
import os
import multiprocessing as mp
from distutils.dir_util import copy_tree, remove_tree
#from shutil import rmtree
import sys
        
class spot_setup(object):
    def __init__(self,parallel='seq'):

        self.params = [spotpy.parameter.Uniform('cmax',low=1.0 , high=500,  optguess=412.33),
                       spotpy.parameter.Uniform('bexp',low=0.1 , high=2.0,  optguess=0.1725),
                       spotpy.parameter.Uniform('alpha',low=0.1 , high=0.99, optguess=0.8127),
                       spotpy.parameter.Uniform('Ks',low=0.0 , high=0.10, optguess=0.0404),
                       spotpy.parameter.Uniform('Kq',low=0.1 , high=0.99, optguess=0.5592)]
                       
        self.curdir = os.getcwd()
        self.owd = os.path.dirname(os.path.realpath(__file__))
        self.hymod_path = self.owd+os.sep+'hymod_unix'
        self.evals = list(np.genfromtxt(self.hymod_path+os.sep+'bound.txt',skip_header=65)[:,3])[:730]
        self.Factor = 1944 * (1000 * 1000 ) / (1000 * 60 * 60 * 24)
        self.parallel = parallel                    

    def parameters(self):
        return spotpy.parameter.generate(self.params)
        
    def simulation(self,x):

        if self.parallel == 'seq':
            call = ''              
        elif self.parallel == 'mpi':
            #Running n parallel, care has to be taken when files are read or written
            #Therefor we check the ID of the current computer core 
            call = str(int(os.environ['OMPI_COMM_WORLD_RANK'])+2)
            #And generate a new folder with all underlying files
            copy_tree(self.hymod_path, self.hymod_path+call)        
        
        elif self.parallel == 'mpc':
            #Running n parallel, care has to be taken when files are read or written
            #Therefor we check the ID of the current computer core 
            call =str(os.getpid())
            #And generate a new folder with all underlying files
            copy_tree(self.hymod_path, self.hymod_path+call)        
        else:
            raise 'No call variable was assigned'

        os.chdir(self.hymod_path+call)
        try:
            params = open('Param.in','w')
    
            for i in range(len(x)):
                if i == len(x):
                    params.write(str(round(x[i],5)))
                else:
                    params.write(str(round(x[i],5))+' ')
            params.close()

            os.system('./hymod_%s.%s' % (sys.version_info.major, sys.version_info.minor))

            SimRR = open('Q.out', 'r')
            
            simulations=[]
            for i in range(64):
                SimRR.readline()
            for i in range(730):
                val= SimRR.readline()
                simulations.append(float(val)*self.Factor)
            SimRR.close()
        except:
            'Model has failed'
            simulations=[np.nan]*795 #Assign bad values - model might have crashed
        os.chdir(self.curdir)
        if self.parallel == 'mpi' or self.parallel == 'mpc':
            remove_tree(self.hymod_path+call)
        return simulations
        
    def evaluation(self):
        return self.evals
    
    def objectivefunction(self,simulation,evaluation, params=None):
        like = spotpy.objectivefunctions.nashsutcliffe(evaluation,simulation)     # Just an example, please choose an appropriate objective function depending on the used algorithm
        return like

