#!/usr/bin/python 

from subprocess import * 
import time
import sqlite3

##############################################################################################
import sys
import Queue
import threading

class WriteThread(threading.Thread):
    def __init__(self, p_in, source_queue):
        threading.Thread.__init__(self)
        self.pipe = p_in
        self.source_queue = source_queue

    def run(self):
        while True:
            source = self.source_queue.get()
            #self.result_list.append("writing to process: ", repr(source))
            self.pipe.write(source)
            self.pipe.flush()
            self.source_queue.task_done()

class ReadThread(threading.Thread):
    def __init__(self, p_out, target_queue):
        threading.Thread.__init__(self)
        self.pipe = p_out
        self.target_queue = target_queue

    def run(self):
        while True:
            line = self.pipe.readline() # blocking read
            if line == '':
                break
            #self.result_list.append("reader read: ", line.rstrip())
            self.target_queue.put(line)

##############################################################################################
 
class GNU_Chess_Wrapper:
	''' This is a very user-friendly wrapper class specially built for GNUChess.
	    For a beautiful GNUChess experience, use this class with its cool interface.
	    (GNU_Chess_Interface)'''
	def __init__(self,username,difficulty, userID):
	#if user changes the options before starting a new game, __init__ will run with user's decisions
	#if user just wants a new game, __init__ will run with default decisions made by us
		#self.result_list.append("--------__init__--------")
		self.result_list = []
		self.userID = userID
		self.t_time = 0
		self.username = username
		self.side = "white"
		self.save_count = 0
		self.current_game = ""
		self.is_saved = False
		self.sname_list = []
		self.gname_list = []
		self.DBconnection = sqlite3.connect("GNU_Chess_Wrapper.db")
		c = self.DBconnection.cursor()
		#c.execute("DROP TABLE LoadGame;")
		#c.execute("DROP TABLE ResumeGame;")
		#c.execute("DROP TABLE SaveCount;")
		
		self.DBconnection.commit()
		#c.execute("PRAGMA foreign_keys = ON;") 
		c.execute('''CREATE TABLE IF NOT EXISTS LoadGame(
				user_id INTEGER,
				save_name_user VARCHAR(30),
				save_name_gnu VARCHAR(30),
				date VARCHAR(21),
				username VARCHAR(30),
				PRIMARY KEY(user_id, save_name_user));''')
		c.execute('''CREATE TABLE IF NOT EXISTS ResumeGame(
				user_id INTEGER,
				save_name_user VARCHAR(30),
				save_name_gnu VARCHAR(30),
				PRIMARY KEY(user_id),
				FOREIGN KEY(user_id) REFERENCES LoadGame(user_id));''')
				
		c.execute('''CREATE TABLE IF NOT EXISTS SaveCount(
					save_count INTEGER,
					PRIMARY KEY(save_count));''')
		self.DBconnection.commit()		
		c.execute("SELECT COUNT(*) FROM SaveCount;")
		eus = c.fetchone()
		eus = eus[0]
		if(eus > 0):
			c.execute("SELECT * FROM SaveCount;")
			self.save_count = c.fetchone()
			self.save_count = self.save_count[0]
		else:
			c.execute("INSERT INTO SaveCount VALUES(0)")
			self.save_count = 0		
		self.DBconnection.commit()

		self.process = Popen(["gnuchess"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
			
		###############---------#######################
   		self.source_queue = Queue.Queue()
  		self.target_queue = Queue.Queue()

   		self.writer = WriteThread(self.process.stdin, self.source_queue)
   		self.writer.setDaemon(True)
  		self.writer.start()

		self.reader = ReadThread(self.process.stdout, self.target_queue)
   		self.reader.setDaemon(True)
   		self.reader.start()
		###############################################
		self.set_difficulty(difficulty)
		self.DBconnection.close()
	def move(self,command): 
		self.result_list = []
		##############---------########################
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		self.source_queue.put(command)
  		self.source_queue.join() # wait until all items in source_queue are processed
		source = ""
		if(command=="go\n"):
			if(self.side == "white"):
				self.side = "black"
			else:
				self.side = "white"
		while(True):
			if(source == "Thinking...\n"):	
				self.result_list.append(source)
				while(self.target_queue.empty()):
					pass	
				# expect some output from reader thread	
				time.sleep(2)	
				source = self.target_queue.get()	
				self.target_queue.task_done()
				source = self.target_queue.get()	
				self.target_queue.task_done()
				while(not self.target_queue.empty()):
					source = self.target_queue.get()
					self.result_list.append(source)	
					self.target_queue.task_done()
				break
			elif(source[:12] == "Invalid move"):
				self.result_list.append("!!"+source)
				break
			else:
				source = self.target_queue.get()	
				self.target_queue.task_done()

		self.result_list.append("Your turn.\n")
		self.is_saved = False
		return 	self.result_list
		###############################################
	def undo_move(self):
		self.source_queue.put("undo\n")
		self.source_queue.put("undo\n") 
		self.source_queue.join() # wait until all items in source_queue are processed
		time.sleep(2)
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		result = self.display_status()	
		return result	
	#a file needed to store the last saved game's name, then user can resume from there.
	def resume_game(self):
		self.DBconnection = sqlite3.connect("GNU_Chess_Wrapper.db")
		self.result_list = []
		result = []
		result.append("--------resume_game--------")
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		self.is_saved = True
		c = self.DBconnection.cursor()
		can_resume = True
		try:
			c.execute('''SELECT *
			   FROM ResumeGame
			   WHERE user_id = ?''',(self.userID,))
		except sqlite3.OperationalError:
			can_resume = False
		#if there exist a saved game, then resume game will invoke that	
		if(can_resume):	
			eus = c.fetchone()
			if(eus != None):
				save_name = eus[1]
				#current game takes save_nox. remember
				self.current_game = eus[2]
				result.append("Now, you are playing : " +  save_name)
				self.process.stdin.write("load " + self.current_game + "\n")	
				time.sleep(0.5)
				if(self.side == "black"):
					self.source_queue.put("go\n")
					self.source_queue.join() # wait until all items in source_queue are processed
					source = ""
					while(True):
						if(source == "Thinking...\n"):			
							while(self.target_queue.empty()):
								pass	
							# expect some output from reader thread	
							time.sleep(2)			
							source = self.target_queue.get()	
							self.target_queue.task_done()
							source = self.target_queue.get()	
							self.target_queue.task_done()
							while(not self.target_queue.empty()):
								source = self.target_queue.get()
								result.append(source)	
								self.target_queue.task_done()
							break
						else:
							source = self.target_queue.get()	
							self.target_queue.task_done()
					self.result_list = result 
				else:
					self.result_list = self.display_status()
					self.result_list = result + self.result_list
				self.result_list.append("Your turn.\n") 
		else:
			self.result_list = result
			self.result_list.append("Nothing happened since you don't have any saved game\n")
		self.DBconnection.close()
		return 	self.result_list			
	# we used it in easy mode since its original easy mode is not reliable
	def set_thinking_time(self,time):
		self.result_list = []
                #self.result_list.append("--------set_thinking_time--------")
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		self.t_time = time
		self.source_queue.put("time " + str(time) + "\n")
  		self.source_queue.join() # wait until all items in source_queue are processed

		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		return 	self.result_list
	# save_name,save_time,save_number should be stored
	def save_game(self,save_name):
		self.DBconnection = sqlite3.connect("GNU_Chess_Wrapper.db")
		self.result_list = []
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		self.result_list.append("Game Saved\n")
		c = self.DBconnection.cursor()
		c.execute("SELECT * FROM SaveCount;")
		self.save_count = c.fetchone()
		self.save_count = self.save_count[0]
		self.save_count += 1                
		# check for existence of file !!!
		c.execute("UPDATE SaveCount SET save_count = ?",(self.save_count,))
		self.DBconnection.commit()
		c.execute('''SELECT COUNT(*)
					 FROM LoadGame
					 WHERE user_id = ? AND save_name_user = ?;''',(self.userID,save_name))
		eus = c.fetchone()
		eus = eus[0]
		t = str(time.localtime()[0:6])
		save_gnu = "save_" + str(self.save_count)
		t = t.split(", ")
		t = '{0}-{1}-{2} {3}:{4}:{5}'.format(*t)
		#user wants to override
		if(eus > 0):
			c.execute("UPDATE LoadGame SET save_name_gnu = ?, date = ? WHERE user_id = ? AND save_name_user = ?;",(save_gnu,t,self.userID,save_name))
		else:
			c.execute("INSERT INTO LoadGame VALUES(?,?,?,?,?);",(self.userID,save_name,save_gnu,t,self.username))
		#assigne new resume_game
		self.DBconnection.commit()
		c.execute('''SELECT COUNT(*)
					 FROM ResumeGame
					 WHERE user_id = ?;''',(self.userID,))
		eus = c.fetchone()
		eus = eus[0]
		if(eus > 0):
			c.execute("UPDATE ResumeGame SET save_name_user = ?, save_name_gnu = ? WHERE user_id = ?;",(save_name,save_gnu,self.userID))
		else:
			c.execute("INSERT INTO ResumeGame VALUES(?,?,?);",(self.userID,save_name,save_gnu))
		self.DBconnection.commit()	
		#save to gnuchess
		self.process.stdin.write("save " + save_gnu + "\n")
		#it will be assigned False in each move command
		self.is_saved = True
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		self.DBconnection.close()
		return 	self.result_list
		

	#when called, prints the list of saved games and loads the picked one (part1 and part2 jobs respectively)
	def load_game_part1(self):
		self.DBconnection = sqlite3.connect("GNU_Chess_Wrapper.db")
		self.is_saved = True
		self.result_list = []
		self.result_list.append("--------load_game--------\n")
		self.sname_list = []
		self.gname_list = []
		self.result_list.append("::Saved Game List::\n")
		c = self.DBconnection.cursor()
		c.execute("SELECT COUNT(*) FROM LoadGame WHERE user_id = ?",(self.userID,))
		eus = c.fetchone()
		eus = eus[0]
		if(eus > 0):
			c.execute("SELECT * FROM LoadGame WHERE user_id = ?",(self.userID,))
			save_list = c.fetchall()
			for i in save_list:
				self.result_list.append(" " + i[1] + " " + i[3])
				self.sname_list.append(i[1])
				self.gname_list.append(i[2])
			#self.result_list.append("If you want to exit from load section, write 'back'")
			#self.result_list.append("Write the name of the file to load: ")
		else:
			self.result_list.append("You don't have a saved game\n")
		self.DBconnection.close() 
		return 	self.result_list

	def load_game_part2(self,neym):	
		self.DBconnection = sqlite3.connect("GNU_Chess_Wrapper.db")	
		self.result_list = []	
		if ( neym in self.sname_list ):
			self.result_list.append("loading file...\n")
			self.current_game = self.gname_list[self.sname_list.index(neym)]
			while(not self.target_queue.empty()):
				source = self.target_queue.get()	
				self.target_queue.task_done()

			self.source_queue.put("load " + self.current_game + "\n")
			self.source_queue.join() # wait until all items in source_queue are processed

			while(self.target_queue.empty()):
				pass	
			# expect some output from reader thread	
			time.sleep(1)
			for i in range(0,4):
				source = self.target_queue.get()	
				self.target_queue.task_done()
			while(not self.target_queue.empty()):
				source = self.target_queue.get()
				self.result_list.append(source)	
				self.target_queue.task_done()
				
			if(self.side == "black"):
				self.source_queue.put("go\n")
				self.source_queue.join() # wait until all items in source_queue are processed
				source = ""
				while(True):
					if(source == "Thinking...\n"):			
						while(self.target_queue.empty()):
							pass	
						# expect some output from reader thread	
						time.sleep(2)			
						source = self.target_queue.get()	
						self.target_queue.task_done()
						source = self.target_queue.get()	
						self.target_queue.task_done()
						while(not self.target_queue.empty()):
							source = self.target_queue.get()
							self.result_list.append(source)	
							self.target_queue.task_done()
						break
					else:
						source = self.target_queue.get()	
						self.target_queue.task_done()
					self.result_list.append("Your turn.\n")
			# set resume game to loaded game
			c = self.DBconnection.cursor()
			c.execute('''SELECT COUNT(*)
						 FROM ResumeGame
						 WHERE user_id = ?;''',(self.userID,))
			eus = c.fetchone()
			eus = eus[0]
			if(eus > 0):
				c.execute("UPDATE ResumeGame SET save_name_user = ?,save_name_gnu = ? WHERE user_id = ?;",(neym,self.current_game,self.userID))
			else:
				c.execute("INSERT INTO ResumeGame VALUES(?,?,?);",(self.userID,neym,self.current_game))
			self.DBconnection.commit()
		elif (neym == "back"):
			pass
		else:
			self.result_list.append("Please write the correct name of the file!\n")	
		self.DBconnection.close() 			
		return 	self.result_list

	# resets the chessboard		
	def new_game(self):
		self.result_list = []
		self.result_list.append("--------new_game--------\n")
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		#new game call will make the player white, always.
		self.is_saved = False
		self.side = "white"
		
		self.source_queue.put("new\n")
  		self.source_queue.join() # wait until all items in source_queue are processed
		time.sleep(0.5)
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()
		return 	self.result_list		
	
	# displays the current chessboard	
	def display_status(self):
		self.result_list = []
		self.result_list.append("--------display_status--------\n")
		while(not self.target_queue.empty()):
			source = self.target_queue.get()	
			self.target_queue.task_done()

        	self.source_queue.put("show board\n")
  		self.source_queue.join() # wait until all items in source_queue are processed

		while(self.target_queue.empty()):
			pass	
		# expect some output from reader thread	
		time.sleep(0.5)
		for i in range(0,4):
			source = self.target_queue.get()	
			self.target_queue.task_done()

		while(not self.target_queue.empty()):
			source = self.target_queue.get()
			self.result_list.append(source)	
			self.target_queue.task_done()
 		return 	self.result_list


	#------------------------OPTIONS STRUCTURE AND ITS FUNCTIONS START------------------------------
	# set_side from options structure. Modifiable, both while playing the game and before starting the game
	def set_side(self,side):
		self.result_list = []
                self.result_list.append("--------set_side--------\n")
		if(side == "b"):
			if(self.side == "white"):
				self.source_queue.put("go\n")
		  		self.source_queue.join() # wait until all items in source_queue are processed
				source = ""
				while(True):
					if(source == "Thinking...\n"):	
						self.result_list.append(source)		
						while(self.target_queue.empty()):
							pass	
						# expect some output from reader thread	
						time.sleep(2)			
						source = self.target_queue.get()	
						self.target_queue.task_done()
						source = self.target_queue.get()	
						self.target_queue.task_done()
						while(not self.target_queue.empty()):
							source = self.target_queue.get()
							self.result_list.append(source)	
							self.target_queue.task_done()
						break
					else:
						source = self.target_queue.get()	
						self.target_queue.task_done()
			self.side = "black"
		elif(side == "w"): 
			if(self.side == "black"):
				self.source_queue.put("go\n")
		  		self.source_queue.join() # wait until all items in source_queue are processed
				source = ""
				while(True):
					if(source == "Thinking...\n"):	
						self.result_list.append(source)	
						while(self.target_queue.empty()):
							pass	
						# expect some output from reader thread	
						time.sleep(2)		
						source = self.target_queue.get()	
						self.target_queue.task_done()
						source = self.target_queue.get()	
						self.target_queue.task_done()
						while(not self.target_queue.empty()):
							source = self.target_queue.get()
							self.result_list.append(source)	
							self.target_queue.task_done()
						break
					else:
						source = self.target_queue.get()	
						self.target_queue.task_done()
			self.side = "white"
		self.result_list.append("Your new side setting applied successfully.\n")
		self.result_list.append("You are now " + self.side + "\n") 
		return 	self.result_list
	# sets difficulty of computer
	def set_difficulty(self,difficulty):
		self.result_list = []
                self.result_list.append("--------set_difficulty--------\n")
		if(difficulty == "easy"):
			self.set_thinking_time(1)
		elif(difficulty == "hard"):
	 		self.set_thinking_time(5000)
		self.result_list.append("Difficulty is set as " + difficulty + "\n")
		return 	self.result_list

	#------------------------OPTIONS STRUCTURE AND ITS FUNCTIONS END---------------------------------

	# kill command for developers
	def c_kill(self):
		self.process.kill()

	def command_list(self):
                self.result_list.append("::Command List::\n")
		self.result_list.append("'resume' for resume game\n")
		self.result_list.append("'new' for new game\n")
		self.result_list.append("'save' for save game\n")
		self.result_list.append("'load' for load game\n")
		self.result_list.append("'set_side -(b/w)' to set side\n")
		self.result_list.append("'set_difficulty -(easy/hard)' to set difficulty\n")
		self.result_list.append("('help'/'-h') for help\n")
		self.result_list.append("'display' to display the board\n")
		self.result_list.append("'undo' to take back the last move\n")
		self.result_list.append("both 'exit' and 'quit' works for you know what\n")
		return 	self.result_list
 
	# only for admins
	def ccurrent_game(self):
		self.result_list = []
		self.result_list.append("Current game : " + self.current_game + "\n")
		return 	self.result_list
	def help(self):
		self.result_list = self.command_list()
		self.result_list.append("Coded by Sener and Cugu\n")
		return 	self.result_list

	def exit(self):
		self.result_list = []
		if(self.is_saved):
			self.result_list.append("Bye\n")
			self.process.stdin.write("exit\n")
			
		else:
			#save the current game, then exit
			self.save_game(self.username)
			self.process.stdin.write("exit\n")
			self.result_list.append("Bye\n")
			self.result_list.append("Game saved with your username.\n")

		return 	self.result_list








