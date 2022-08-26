from audioop import add
import os 
import sys
import traci
import numpy

def createCust(time: int, custCount: int, pos:float, origin:str, dest:str):
    traci.person.add(f"cust{custCount}",origin, pos, time+1, "DEFAULT_PEDTYPE")
#    traci.person.appendWalkingStage(f"cust{custCount}", origin, 10, )
    traci.person.appendDrivingStage(f"cust{custCount}", dest, "taxi")


def createShuttle(time, num):
    traci.vehicle.add(f'taxiV{num}', 'depot', typeID='shuttle', depart=f'{time+2}', line='taxi')

def custInfo(custName: str):
    if custName in traci.person.getIDList():
        custVehRes = traci.device
        custVeh = traci.person.getVehicle(custName)
        custDest = traci.person.getEdges(custName, )
        if custVeh == '':
            print('.', end="")

        if custVeh in traci.vehicle.getIDList():
            print(traci.vehicle.getDrivingDistance(custVeh, custDest[1], 0.0))

def shuttleInfo(shuttleName: str):
    if shuttleName in traci.vehicle.getIDList():
        shuttleCust = traci.vehicle.getParameter(shuttleName, "device.taxi.currentCustomers")
        print(shuttleCust, end="")
        if shuttleCust in traci.person.getIDList():
            custDest = traci.person.getEdges(shuttleCust, )
            print(traci.vehicle.getDrivingDistance(shuttleName, custDest[1], 0.0))
        

    
#def checkDemand(time):
#    taxiDiff = len(traci.vehicle.getTaxiFleet(4)) - len(traci.person.getTaxiReservations(0))
#    if taxiDiff > 50:
#        for i in taxiDiff:
#            createShuttle(time)
 #   print(traci.vehicle.getTaxiFleet(4))
 #   print(*traci.person.getTaxiReservations(0))


originList = ["-E65", "-E46", "E42", "-E55", "E57", "E40", "-E39.532", "-E69", "721302669#2", "-407581698#2", "407568055#4", "504565992#2"]
freihamLiving = ["-E65", "E65", "-E45", "E45", "-E46", "E46", "-E47", "E47", "-E44", "E44", "-E43", "E43", "-E48", "E48", "-E49", "E49", "-E51", "E51", "-E52", "E52", "-E69", "E69", "-E70", "E70", "-E71", "E71", "E72", "-E72", "E73", "-E73", "-E74", "E74", "504569022", "-504569022"]
destList = ["E39", "-721302669#2", "-513657853#0", "143578411#1"]


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui"
sumoCmd = [sumoBinary, "-c", "test.sumocfg", "--tripinfo-output", "tripinfos.xml",
             "--device.taxi.dispatch-algorithm", "greedy",]

traci.start(sumoCmd)
step = 0
count = 1
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    if step % 130 == 0 :
        createCust(step, count, 0, freihamLiving[numpy.random.randint(0, 34)], destList[numpy.random.choice(numpy.arange(0,4), p=[0.1, 0.1, 0.1, 0.7])])
        count += 1
    if 125 < step and step < 135:
        createShuttle(step, count) 
        count += 1 

    shuttleInfo("taxiV2")

    step += 1

traci.close()

