#!/usr/bin/python 

from GNU_Chess_Wrapper import GNU_Chess_Wrapper
from threading import *
from subprocess import * 

class Read(Thread):
    def __init__(self, p_out, connection):
        Thread.__init__(self)
        self.pipe = p_out
	self.terminate = False
	self.connection = connection

    def run(self):
        while not self.terminate:
            line = self.pipe.readline() # blocking read
            if ( line == "exit\n" ):
		break
            self.connection.send(line)


class GNU_Chess_Agent(Thread):
	def __init__(self, connection, address, userID, kill_lock, kill_condition, agentInstanceList):
		print "Agent is created"
		self.agentInstanceList = agentInstanceList
  
		self.kill_lock = kill_lock
		self.kill_condition = kill_condition
		self.isdetach = False
		self.isdestroy = False
		self.instance = None
		self.userID = userID
		self.username = ""
		self.connection = connection
		self.address = address
		self.terminate = False
		self.connectedBefore = False
		print "Client is connected to the server from " + str(self.address)
		Thread.__init__(self)
		
	def run(self): 
		self.connection.sendall("Do you have an ID? \nIf you have an ID, please type it otherwise type 'no'.\n")
		line = self.connection.recv(1024)
		if ( line == "no" ):
			self.connection.sendall("--- Your id is : " + str(self.userID) + " ---\n")
			self.connection.sendall("Please remember your ID for other connections!" + "\n\n")
			self.connection.sendall("You are welcome!Enjoy your game.\n")
			self.agentInstanceList.append({ "Agent" : self, "ID" : self.userID, "username" : self.username, "instance" : None })
			self.connectedBefore = False
		else:
			ID = int(line)
			self.userID = ID
			for i in self.agentInstanceList:
				if ( i["ID"] == self.userID ):
 					self.connection.sendall("-" + i["username"] + "- hello again!Now, you can continue with your ongoing session.\n") 
					i["Agent"] = self
					self.instance = i["instance"] 
					self.username = i["username"]
					break
			self.connectedBefore = True
		while True:
			self.connection.sendall(">>")
			line = self.connection.recv(1024)
			if ( line == "attach" ):
				self.isdetach = False
				self.isdestroy = False
				self.agent_command("attach")
			elif ( line == "detach" or line == "exit" ):
				self.agent_command("detach")
				self.isdestroy = False
				self.isdetach = True
				self.connection.sendall("None")
				self.kill_lock.acquire()
				self.kill_condition.notifyAll()
				self.kill_lock.release()
				break
			elif ( line == "destroy" ):
				self.agent_command("destroy")
				self.isdestroy = True
				self.isdetach = False
				self.connection.sendall("None")
				self.kill_lock.acquire()
				self.kill_condition.notifyAll()
				self.kill_lock.release()
				break
			else:
				result = self.GNU_Chess_Wrapper_Communication(line)
				send = ""
				if ( result != [] ):
					for i in result:
						send += i
					self.connection.sendall(send)

 		self.connection.close()
		
	def agent_command(self,command):
		if(command == "attach" ):
			if ( self.instance != None ):
	 			self.connection.sendall("Now you are connected to your game!!!\n")
				for i in self.agentInstanceList:
					if ( i["ID"] == self.userID ):
						i["Agent"] = self 
						break		
			else:
				self.connection.sendall("You don't have an opened game!. So, your new game is starting...\n")
				opening = "::Welcome to GNU-Chess World!::\n>>In order to proceed...\n>>Write 'help' or '-h' for help section\n>>Write 'new' to start a new game with current options\n>>Write 'exit' or 'quit' to exit"
				self.connection.sendall(opening + "\n")
				self.connection.sendall("Please indicate your username: \n")
				self.connection.sendall(">>")
				self.username = self.connection.recv(1024)
				self.username = (self.username.split(' '))[0]
				self.instance = GNU_Chess_Wrapper(self.username,"hard",self.userID)
				for i in self.agentInstanceList:
					if ( i["ID"] == self.userID ):
						i["Agent"] = self 
						i["instance"] = self.instance
						i["username"] = self.username
						i["ID"] = self.userID
		elif(command == "detach" or command == "exit" ):
			print "detach " + str(self.userID)
			#self.instance.exit()
		elif(command == "destroy"):
			self.instance.exit()
			
	def get_instance(self):
		return self.instance

	def GNU_Chess_Wrapper_Communication(self,sentence): 
		result = []
		sp = sentence.split(' ')
		if (sp[0] == "help"):
			result = self.instance.help()
		elif (sp[0] == "kill"):
			self.instance.c_kill()
		elif (sp[0] == "new"):
			result = self.instance.new_game()
	 	elif (sp[0] == "exit" or sp[0] == "quit"):
			result = self.instance.exit()
		elif (sp[0] == "save"):
			result = self.instance.save_game(sp[1])
		elif (sp[0] == "load"):
			result = self.instance.load_game_part1()
			send = ""
			for i in result:
				send += i + "\n"
			self.connection.sendall(send)
			self.connection.sendall(">>")
			wanted_game = self.connection.recv(1024)
			if(wanted_game != "back"):
				result = self.instance.load_game_part2(wanted_game)
			else:
				result = "You are successfully exitted from load section\n"
		elif (sp[0] == "resume"):
			result = self.instance.resume_game()
		elif (sp[0] == "cur"):
			result = self.instance.ccurrent_game()
		elif (sp[0] == "set_side"):
			if(sp[1] == "-b"):
				result = self.instance.set_side("b")
			elif(sp[1] == "-w"):
				result = self.instance.set_side("w")
		elif (sp[0] == "set_difficulty"):
			if(sp[1] == "-easy"):
				result = self.instance.set_difficulty("easy")
			elif(sp[1] == "-hard"):
				result = self.instance.set_difficulty("hard")
		elif (sp[0] == "display"):
			result = self.instance.display_status()
		elif (sp[0] == "undo"):
			result = self.instance.undo_move()
		else:
			result = self.instance.move(sp[0]+"\n")
		return result

 


