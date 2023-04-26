from  collections import  orderedDict



class ConversationState:
 	def __init__(self,conversation):
 		self.conversation=conversation
 		self.last_response={}
 		self.states=orderedDict()
 		self.current_state=None
 		self.previous_states=[]
 	def add(self,name,condition):
 		self.states[name]=conversation

 	def run(self,*args,**kwargs):
 		output=self.conversation(*args,**kwargs)
 		if type(output)==str:
 			self.last_response={"response":output}
 		else:
 			self.last_response=output
 		notbreak=True
 		for elem,checker in self.states.items():
 			if checker(output):
 				self.previous_states.append(elem)
 				del checker[elem]
 				break
 		else:
 			notbreak=True
 		
 		return output
