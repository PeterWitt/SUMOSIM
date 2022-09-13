import os
import sys
import traci
import numpy 

from flask import Flask, request
from threading import Thread
from flask_socketio import SocketIO, emit, send

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# True if user launches the app
connection_established = False
customer_arrived = False
# Set to a value that user selected in the app
destination_set = ""

# START of functions & variables related to SUMO simulation
# Creation of customer. Every Customer is called Cust and the number of created customers, i.e. cust1
def createCust(time: int, custCount, pos:float, origin:str):
    traci.person.add(f"cust{custCount}",origin, pos, time+1, "DEFAULT_PEDTYPE")
    #Customer waits, Stage will be appended by different function
    traci.person.appendWaitingStage(f"cust{custCount}", 1, description='waiting', stopID='')
    traci.person.setColor(f"cust{custCount}", (1, 0.2, 0.2))
    return f"cust{custCount}"

# If destination is choosen, function adds Stage to the called costumer
def createCustDest(custName: str, dest: str):
    traci.person.appendDrivingStage(custName, dest, "taxi")
    return True

def createShuttle(time, num):
    traci.vehicle.add(f'taxiV{num}', 'depot_rou1', typeID='shuttle', depart=f'{time+2}', line='taxi')
    traci.vehicle.setParkingAreaStop(f'taxiV{num}', "depot_park1", duration=1, flags=1)
    return f'taxiV{num}'

def custInfo(custName: str):
    if custName in traci.person.getIDList():
        custVehRes = traci.device
        custVeh = traci.person.getVehicle(custName)
        custDest = traci.person.getEdges(custName, )
        if custVeh == '':
            print('.', end="")

        #if custVeh in traci.vehicle.getIDList():
        #    print(traci.vehicle.getDrivingDistance(custVeh, custDest[1], 0.0))

def shuttleInfo(shuttleCust: str, prt_shuttle):
    cust_shuttle = ""
    for shuttle_dict in prt_shuttle:
        if traci.vehicle.getParameter(shuttle_dict["shuttle_name"], "device.taxi.currentCustomers") == shuttleCust and traci.vehicle.getParameter(shuttle_dict["shuttle_name"], "device.taxi.state") in ["1", "2", "3"]:
            cust_shuttle = shuttle_dict["shuttle_name"]
            break

    #Get distance to customer/destination
    #shuttleCust = traci.vehicle.getParameter(shuttle_dict["shuttle_name"], "device.taxi.currentCustomers")
    if cust_shuttle != "":
        if traci.vehicle.getParameter(cust_shuttle, "device.taxi.state") == "1":
            x, y = traci.person.getPosition(shuttleCust)
            return traci.vehicle.getDrivingDistance2D(cust_shuttle, x, y) 
                
        elif traci.vehicle.getParameter(cust_shuttle, "device.taxi.state") == "2":
            shuttleCustDest = traci.person.getEdges(shuttleCust)
            return traci.vehicle.getDrivingDistance(cust_shuttle, shuttleCustDest[len(shuttleCustDest)-1] , traci.person.getLanePosition(shuttleCust))            



def shuttleReroute(shuttle_dict: str):
    #Reroute Vehicle to depot     
    try:
        if not traci.vehicle.isStoppedParking(shuttle_dict["shuttle_name"]) and traci.vehicle.getParameter(shuttle_dict["shuttle_name"], "device.taxi.state") == "0":
            num = numpy.random.choice(numpy.arange(1,6), p=[0.2, 0.2, 0.2, 0.2, 0.2])
            traci.vehicle.changeTarget(shuttle_dict["shuttle_name"], traci.lane.getEdgeID(traci.parkingarea.getLaneID(f"depot_park1")))
            traci.vehicle.setParkingAreaStop(shuttle_dict["shuttle_name"], f"depot_park1", duration=999999, flags=1)
    except traci.exceptions.TraCIException as e:
        print(e)


originList = ["-E65", "-E46", "E42", "-E55", "E57", "E40", "-E39.532", "-E69", "721302669#2", "-407581698#2", "407568055#4", "504565992#2"]
freihamLiving = ["-E65", "E65", "-E45", "E45", "-E46", "E46", "-E47", "E47", "-E44", "E44", "-E43", "E43", "-E48", "E48", "-E49", "E49", "-E51", "E51", "-E52", "E52", "-E69", "E69", "-E70", "E70", "-E71", "E71", "E72", "-E72", "E73", "-E73", "-E74", "E74", "504569022", "-504569022"]
destList = ["E39", "-721302669#2", "-513657853#0", "E31"]

# END of functions & variables related to SUMO simulation

# START of Flask API
@socketio.on("track_vehicle")
def start_sumo_background_task():
    global connection_established
    global destination_set
    global customer_arrived

    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui"
    sumoCmd = [sumoBinary, "-c", "..\SUMOSIM\\test.sumocfg", "--tripinfo-output", "tripinfos.xml",
        "--device.taxi.dispatch-algorithm=greedy", "--start", "true" , "--ignore-route-errors", "--device.taxi.idle-algorithm=randomCircling",
        "--begin=30000", "--collision.action=none"]

    traci.start(sumoCmd)
    step = 0
    count = 1
    managed_cust = []
    prt_shuttle = []
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        all_cust = traci.person.getIDList()

        if connection_established:
            customer_info = dict()
            customer_info["cust_name"] = createCust(step+1, f"Mobil{count}", 190, '-E42')
            print("Customer", customer_info["cust_name"], "is created.")
            traci.person.setColor(customer_info["cust_name"], (1, 0.5, 0.5))
            customer_info["dest_set"] = False
            managed_cust.append(customer_info)
            connection_established = False
            customer_arrived = False
        if destination_set != '':
            for i in range(len(managed_cust)):
                if "Mobil" in managed_cust[i]["cust_name"]:
                    managed_cust[i]["dest_set"] = True
                    createCustDest(managed_cust[i]["cust_name"], destination_set)
            destination_set = ''
        else:
            for cust_info in managed_cust:
                if not cust_info["dest_set"]:
                    traci.person.appendWaitingStage(cust_info["cust_name"], 1, description='waiting', stopID='')

        if step%10 == 0:
            for shuttle_info in prt_shuttle:
                shuttleReroute(shuttle_info)   
            
            for cust_info in managed_cust:
                if cust_info["cust_name"] not in all_cust:
                    managed_cust.remove(cust_info)
                    customer_arrived = True
                    data = dict()
                    data["customerArrived"] = customer_arrived
                    socketio.emit("customer_arrived", data)
                    print("Customer " + cust_info["cust_name"] + " arrived and was deleted.")
                    continue
                
                if cust_info["dest_set"]:
                    cust_dest = traci.person.getEdges(cust_info["cust_name"])
                    if traci.person.getLaneID(cust_info["cust_name"]) != cust_dest[len(cust_dest)-1]:
                        deg = traci.person.getAngle(cust_info["cust_name"])
                        x, y = traci.person.getPosition(cust_info["cust_name"])
                        lon, lat = traci.simulation.convertGeo(x, y)
                        dist = shuttleInfo(cust_info["cust_name"], prt_shuttle)
                        data = dict()
                        data["latitude"] = lat
                        data["longitude"] = lon
                        data["degree"] = deg
                        data["dist_to_arrival"] = dist
                        print("Data that should be sent: ",  data)
                        socketio.emit("track_vehicle", data)

        if step == 20:
            for i in range(1, 2):
                prt_temp = dict()
                prt_temp["shuttle_name"] = createShuttle(step, count)
                prt_temp["reroute"] = False
                prt_shuttle.append(prt_temp)
                count += 1
        if step == 21:
            for i in range(1, 5):
                customer_info = dict()
                customer_info["cust_name"] = createCust(step, count, 0, freihamLiving[numpy.random.randint(0, 34)], )
                createCustDest(customer_info["cust_name"] , destList[numpy.random.choice(numpy.arange(0,4), p=[0.1, 0.1, 0.1, 0.7])])
                customer_info["dest_set"] = True
                #managed_cust.append(customer_info)
                count += 1
        step += 1

    traci.close()

@app.route('/establish-connection', methods=['POST'])
def establish_connection():
    global connection_established
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        if json["connectionEstablished"] == 'true':
            print("User started the app. Connection established!")
            connection_established = True
        return json
    else:
        return 'Content-Type not supported!'

@app.route('/set-destination', methods=['POST'])
def set_destination():
    global destination_set
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        if json["destinationSet"] != '':
            destination_set = json["destinationSet"]
            print("Destination is set as", destination_set)
        return json
    else:
        return 'Content-Type not supported!'

if __name__ == "__main__":
    thread = Thread(target=start_sumo_background_task)
    thread.daemon = True
    thread.start()
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)
    #app.run('0.0.0.0', debug=True, use_reloader=False)
