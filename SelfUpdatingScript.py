import os 
import requests 

def self_update():
	self = "https://raw.githubusercontent.com/MichaelTrotterPersonal/AutoGit/master/SelfUpdatingScript.py"
	self_content = requests.get(self)

	with open(os.path.realpath(__file__),'w') as this_script:
		this_script.write(self_content.text)

if __name__ == '__main__':

	self_update()
	print('Awesome')
