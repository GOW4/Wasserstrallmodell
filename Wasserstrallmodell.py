# -*- coding: UTF-4 -*-
# Restartprogramm und konvektive Wärmeübergangsrandbedingung für das Wasserstrahlmodell

from abaqus import *
from abaqusConstants import *
from caeModules import *
from odbAccess import *
import os
import sys
import numpy as np
from math import sqrt

# 最大运行次数,maximale Anzahl an Läufen
MaxNum = 3
# 读取flodel, step, job名称方法
lastModelName = 'Model-Restart-Initial'
lastStepName = 'Step-1'
lastJobName = 'Restart-Initial'
# 后续计算文件的计算步长
steptimenum = 0.1

instancename = 'WORKPIECE'
nodesetname = 'SET-4'
surfacename = 'Surf-Workpiece'
instancename3 = 'Workpiece'
elementrange = 1.5

# 对流特性参数/对流传热设置
# v1=11330.4333216mm/s,0.5MPa,9.9838E-09t/mm2,
v=0.4*sqrt(2*0.1/0.000000009705)
pr=6.1358 #pr直接给出的为6.1358
xxx=1.5 #x 为斜度长度标量，mm

# 雷诺数 (示例计算，保留原式)
rex = (0.000000009705 * v * xxx) / 0.0000008902#Re(x)=19039.4740437
# 简单赋值，脚本中使用 x 作为长度标量
x = xxx  
lamda=0.000387979838948 #lamda为热导率(W/mmK)
#NU(x)根据公式计算得出387.979838948,平板湍流边界层的局部对流换热公式
nux = 0.03*pow(pr,0.33)*pow(rex,0.4)
# 根据努塞尔数计算热传导h
h=(lamda*nux)/(xxx)
# 热流边界温度为298K
sinkTempValue=298



# 原始模型名称 ursprungliche ModelIname.Model-Restart-Initial,import Model

# 创建并提交作业Restart-Initial,Job erstellen und absenden.Restart-Initial
mdb.job(name='Restart-Initial', model='Model-Restart-Initial', description='',
    type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None,
    memory=90, memoryUnits=PERCENTAGE, explicitPrecision=DOUBLE,
    nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
    contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
    resultsFormat=ODB, parallelizationMethodExplicit=DOMAIN, numDomains=4,
    activateLoadBalancing=False, multiprocessingMode=DEFAULT, numCpus=4)
mdb.jobs['Restart-Initial'].submit(consistencyChecking=OFF) # 提交作业并开始运行
print('Wait for Restart-Initial')
mdb.jobs['Restart-Initial'].waitForCompletion() # Warten auf Abschluss von Restart-Initial




#Start der Restart-Schleife und hinzufügen der konvektiven Wärmeübergangsrandbedingung


for i in range(MaxNum):
        # Create a model for the restart step by copying the last model
        mdb.Model(name='Model-Restart-%s' format(i + 1), objectToCopy=mdb.models[lastModelName])
        a = mdb.models['Model-Restart-%s'.format(i + 1)].rootAssembly
        mdb.models['Model-Restart-%s'.format(i + 1)] TempDisplacementDynamicsStep(name='Step-&s'.format(i + 2), previous=lastStepName,
                                                                                    timePeriod=steptimenum, improvedDtmethod=ON)
        mdb.job(name='Restart-%s'.format(i + 1), model='Model-Restart-%s'.format(i + 1), description='',
        type=RESTART, atTime=None, waitMinutes=0, waitHours=0, queue=None,
        memory=90, memoryUnits=PERCENTAGE, explicitPrecision=DOUBLE,
        nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
        contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
        resultsFormat=ODB, parallelizationMethodExplicit=DOMAIN, numDomains=4,
        activateLoadBalancing=False, multiprocessingMode=DEFAULT, numCpus=4)

        #laststepname更新为新步骤名称
        mdb.jobs['Restart-%s'.format(i + 1)].submit(consistencyChecking=OFF)
        print('Wait for Restart-%s'.format(i + 1))
        mdb.jobs['Restart-%s'.format(i + 1)].waitForCompletion() # Warten auf Abschluss von Restart-i+1

        # create and submit job
        job_name = 'Restart-%s'.format(i + 1)
        odb= openOdb(path=job_name + '.odb')
        mdb.Job(name=job_name, model=new_model_name, description='', type=ANALYSIS,
                atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                memoryUnits=PERCENTAGE, explicitPrecision=DOUBLE,
                nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
                contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
                resultsFormat=ODB, parallelizationMethodExplicit=DOMAIN, numDomains=4,
                activateLoadBalancing=False, multiprocessingMode=DEFAULT, numCpus=4)

        mdb.jobs[job_name].submit(consistencyChecking=OFF)
        print('Wait for {}'.format(job_name))
        mdb.jobs[job_name].waitForCompletion()
        job_name = 'Restart-{}'.format(i + 1)
        odb = openOdb(path=job_name + '.odb', readOnly=True) #odb Ergebnisse datei

        # try to open the ODB and extract CPRESS; protect with exception handling
        try:
            lastFrame = odb.steps['Step-%s'.format(i + 2)].frames[-1]
            cpress_output_Data = lastFrame.fieldOutputs['CPRESS General_contact_Demain']
            topCenter_2 = odb.rootAssembly.nodesets[nodesetname]
            centerDisplacement = cpress_output_Data.getSubset(region=topCenter_2)
            num = len(centerDisplacement.values)
            multilist1 = [0] * num
            multilist2 = [0] * num
            j = 0



            for k in range(0, num):
                a = centerDisplacement.values[k].data
                if (a > 0) and (a <= 70):
                    multilist1[j] = centerDisplacement.values[k].nodeLabel
                    multilist2[j] = centerDisplacement.values[k].data
                    j += 1
                else:
                     j=j




            nozeronum = len(np.nonzero(multilist1)[0]) # Berechnen die Anzahl der nicht null Elemente in multilist1
            cpFile=open('workpiece_nodes_list.txt','w')
            for k in range(0,nozeronum):
                cpFile.write("%30.0f\n"%(multilist1[k]))
            else:
                cpFile.close()







            odb.close()
            
            #==========================节点坐标解析场办法===================    
            



            #导入节点txt文件，首先对被切体进行操作
           
            result=[]
            with open('workpiece_nodes_list.txt','r') as f:
              lines=f.readlines()
            for line in lines:
                result.append(int(line.strip()))
            numnodelist=len(result)
            numnodet1= [0]*numnodelist
        # numnodet1为节点编号数组
            for k in range(0,numnodelist):
                a= result[k] [0]
                a=int(a)
                numnodet1[k]=a


            num0=len(numnodet1)
            os.remove('workpiece_nodes_list.txt') # 删除临时文件
#2创建一个二维数组multilist，行数为num0，列数为4
            multilist = [[0 for co1 in range(4)] for row in range(num0)]
#3根据所有节点编号找到相应的所有节点坐标
            a = mdb.models['Model-Restart-%s' format(i+1)].rootAssembly
            n1 = a.instances[instancename3].nodes
            node1 = n1.sequenceFromLabels(labels=numnodet1)
#4利用循环把上述numnodet1数组里节点编号对应的节点坐标存入multilist数组
            for k in range(0,num0):
                node1=n1[numnodet1[k]-1]
                multilist[k][0]=node1.coordinates[0]
                multilist[k][1]=node1.coordinates[1]
                multilist[k][2]=node1.coordinates[2]
                multilist[k][3]=1

#5根据数组multilist里数据，设置节点解析场AnalysisField-1,并且相对容差为1.5个单元长度，
            mdb.models['Model-Restart-%s' format(i+1)].MappedField(name='AnalysisField-1',
                description='', regionType=POINT, partLevelData=False, localCsys=None,
                pointDataFormat=XYZ, fieldDataType=SCALAR, xyzPointData=multilist
                neighborSearchTolerance=elementrange)
        
#把节点的解析场数据与对流换热边界条件关联
#注意，这里是被切体数据，因此，有模型名称 'Model-Restart-%s' format(i+1) 表面集Surf-Selfcontact, 施加载荷步骤Step-%s'.format(i + 2)
#解析场名称AnalysisField-1,对流换热系数h,环境温度sinkTempValue
            a = mdb.models['Model-Restart-%s' format(i+1)].rootAssembly
            region = a. surfaces[surfacename]
            mdb.models['Model-Restart-%s' format(i+1)].FilmCondition(name='Int-workpiece',
                createStepName='Step-%s'.format(i + 2), surface=region,definition=FIELD,
                field='AnalysisField-1', filmCoeff=h, filmCoeffAmplitude='', 
                sinkTemperature=sinktempu, sinkTempAmplitude='', sinkDistributionType=UNIFORM,
                sinkFieldName='')

        except:
            pass
        lastModelName = 'Model-Restart-%s'.format(i + 1)
        lastStepName = 'Step-%s'.format(i + 2)
        lastJobName = 'Restart-%s'.format(i + 1)