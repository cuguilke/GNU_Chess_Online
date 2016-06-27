from django.shortcuts import redirect,render
from django.http import HttpResponse
# Create your views here.
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required


from GNU_Chess_App.models import Chess_User 
import re
from socket import * 
from time import * 
HOST = '0.0.0.0'                 
PORT = 50009         
sock = socket(AF_INET, SOCK_STREAM)  

lastBoard = ""

def home(request):
    context = {  } 
    return render(request, "header.html", context) 

def login_view(request): 
    return render(request, "header.html", {}) 
 
def processResponse(message, username, sock): 
	if ( message.__contains__("Do you have an ID?") ): 
		m = Chess_User.objects.get(username=username) 
 		userid = m.user_id 
		if ( userid == -1 ):
			userid = "no"
			sock.send(str(userid)) 
			idString = sock.recv(1024)
			userid = int(re.findall("[0-9]+", idString)[0])
			m.user_id = userid
			m.save() 
			sock.send("attach") 
			s = sock.recv(1024)
			print s
			sock.send(username)
			s = sock.recv(1024) # takes ">>", now everything is crystal clear
			print s
		else:
			sock.send(str(userid)) 
			message = sock.recv(1024)
 			sock.send("attach") 
			s = sock.recv(1024)
			sock.send(username)
			s = sock.recv(1024) # takes ">>", now everything is crystal clear

def boardParser(s): #takes string
	s = s.split("\n")
	retVal = ""
	count = 0 
	for i in s:
		if ( i.__len__() == 16 and count != 8 ): 
			retVal += i + "\n"
			count += 1
	return retVal


def new(request):  
	global sock
	global lastBoard
 	sock.send("new")
	string = sock.recv(1024)
	sock.send("display")
	string = ""
 	while ( True ):
		string = sock.recv(1024)
		if ( string.__contains__("display") ):
			break 
	string = boardParser(string)
	lastBoard = string 
	return redirect('/playv') 
	#return render(request, "play.html",  {'play_message' : lastBoard, 'message' : 'Your turn.'}) 

def resume(request): 
	# load last saved board and redirect to "/play"
	global sock
	global lastBoard
 	sock.send("resume")
	string = sock.recv(1024)
	if ( string.__contains__("resume") ):
		lastBoard = boardParser(string)   
	return render(request, "play.html",  {'play_message' : lastBoard, 'message' : 'Your turn.'}) 

def save_view(request):   
    return render(request, "save.html", {})

def save_post(request): 
	message=""
	try:
		savename = request.POST["savename"]
	except:
		savename = None
	if ( savename ):
		sock.send("save " + savename)
		message = string = sock.recv(1024) 
	return render(request, "save.html", { 'message' : 'Game Saved' })

def load_view(request):
	global sock
	sock.send("load")
	insertform = []
	s = ""
	while ( True ):
		s = sock.recv(1024)
		if ( s.__contains__("List") ):
			break 
	s = s.split("\n")
	s = s[4:-1] 
	return render(request, "load.html", { 'loadnames' : s })

def load_post(request): 
	# list load game names
	# click to wanted game name and return to "/play"
	global sock
	global lastBoard 
	s = ""
	try:
		loadname = request.POST["loadname"]
	except:
		loadname = None
	if(loadname):
		sock.send(loadname)
		s = sock.recv(1024)
		sock.send("display")
	 	while ( True ):
			s = sock.recv(1024)
			if ( s.__contains__("display") ):
				break 
		s = boardParser(s)
		lastBoard = s
	return redirect('/playv') 
	#return render(request, "play.html",  {'play_message' : lastBoard, 'message' : 'Your turn.'}) 

def load_pass(request): 
	global sock
	global lastBoard  
	sock.send("back") 
	return redirect('/playv') 
	#return render(request, "play.html",  {'play_message' : lastBoard, 'message' : 'Your turn.'}) 
  

def login_post(request):
	context = {}
	user = None 
	try:
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
	except MultiValueDictKeyError:
		user = None
	# check for authentication
	if user is not None: 
		global sock
		sock = socket(AF_INET, SOCK_STREAM)  
		sock.connect((HOST, PORT))
	# do initial configurations
		message = sock.recv(1024)
		print message
		processResponse(message, username, sock)
		return redirect('/new')  
	else:
		# Return an 'invalid login' error message.
		return render(request, 'index.html', {'title' : 'message', 'message' : 'access denied '}) 
  
def signup_view(request):  
    context = {  } 
    return render(request, "signup.html", context) 

def signup_post(request):   
	username = request.POST['username']
	password = request.POST['password']
	user = User.objects.create_user(username, None, password)
	user.save()
	chess_user = Chess_User.objects.create(user_id=-1,username=username)
	chess_user.save()
	return redirect('/loginv') 
    #return render(request, "header.html", context) 

#@login_required(login_url='/loginv')
def play_view(request):   
	global lastBoard
	context = {}  
	return render(request, "play.html",  {'play_message' : lastBoard, 'message' : 'Your turn.'}) 

#@login_required(login_url='/loginv')
def play_post(request):    
	string = ""
	mes = ""
	is_valid = True
	global lastBoard
	global sock
	move = request.POST["Move"]

	sock.send(move)
	while ( True ):
		string = sock.recv(1024)
		if ( string.__contains__("Thinking") or  string.__contains__("display") ):
			break
		elif(string.__contains__("Invalid")):	
			is_valid = False
			break
	if(is_valid):
		string = boardParser(string)
		lastBoard = string
		mes = "Your turn."
	else:
		mes = "Invalid Move!"
		string = lastBoard  
	return render(request, "play.html",  {'play_message' : lastBoard, 'message' : mes}) 

def logout_view(request):
	'''Simply logout'''
	context = { }
	global sock
	sock.send("destroy")
	logout(request)
	return render(request, "logout.html", context) 



