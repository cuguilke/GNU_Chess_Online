#!/usr/bin/python

from socket import *
import time	
from GNU_Chess_Agent import *

	
HOST = '0.0.0.0'                 
PORT = 50009           

sock = socket(AF_INET, SOCK_STREAM)  
# for reusing socket several times in short time 
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)


sock.bind((HOST, PORT))
sock.listen(1)

agentList = []
detachedInstanceList = []
agentID = 0

class AgentKill(Thread):
	def __init__(self,agentInstanceList, lock, condition):
		Thread.__init__(self)
		self.agentInstanceList = agentInstanceList
		self.lock = lock
		self.condition = condition
		self.serverclosed = False

	def run(self):
		while True:
			self.lock.acquire()
			self.condition.wait()
			if (self.serverclosed == True or self.agentInstanceList.__len__() == 0):
				self.lock.release()
				break
			# kill the thread
			for i in self.agentInstanceList:
				if ( i["Agent"] != None ):
					# detach agent but keep its game
					if ( i["Agent"].isdetach == True ):
						i["Agent"].join()
						i["Agent"] = None
						print "Agent will be detached"
						break
					# destroy it
					if ( i["Agent"].isdestroy == True ):
						i["instance"] = None
						i["Agent"].join()
						i["Agent"] = None
						print "Agent will be destroyed" 
						break

			prin(self.agentInstanceList)
			self.lock.release()

 
agentInstanceList = []
kill_lock = Lock()
kill_condition = Condition(kill_lock)
killAgent = AgentKill(agentInstanceList, kill_lock, kill_condition)
killAgent.start()

def prin(agentInstanceList):
	print "\nClient - Instance List"
	for i in agentInstanceList:
		print "Client - Name = " + i["username"] + " // ",
		print "ID = " + str(i["ID"]) + " // ", 
		print "Instance state = " + str(i["instance"] != None)
	


while True:
	try:
		print ">>Waiting for connection"
		# accept users
		connection, address = sock.accept()
		# create an agent for user
		agent = GNU_Chess_Agent(connection, address, agentID, kill_lock, kill_condition, agentInstanceList)
		#agent = GNU_Chess_Agent()
		agent.start()

		# add agent and its connection to a list
		agentList.append({"ID" : agentID, "Agent" : agent, "Connection" : connection})
		# increment agentIDs
		agentID += 1
		print ">>Connection established"

	except KeyboardInterrupt:
		print "Keyboard Interrupt"
		sock.close()
		print ">>Socket is closed"
		break

agentInstanceList = []
killAgent.serverclosed = True 
time.sleep(1)
kill_lock.acquire()
kill_condition.notifyAll()
kill_lock.release()

print "\nPrinting the Connections"
for i in agentList:
	print i 
	i["Connection"].close()




