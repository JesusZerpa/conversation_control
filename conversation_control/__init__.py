from collections import OrderedDict
from langchain.chains import LLMChain
from typing import Dict


class ConversationState:
 	def __init__(self,conversation):
 		self.conversation=conversation
 		self.last_response={}
 		self.states=OrderedDict()
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


class ConversationControl:
	def __init__(self,name,session,models):
		self.name=name
		self.handlers={}
		self.checkers={}
		self.ctx={}
		self.history=[]
		self.modelState=models["state"]
		self.modelStore=models["store"]
		self.modelEvent=models["event"]
		self.session=session
		"""
		states:{
			"id":"name",
			handlers:[],
			before_states[]
		}
		"""
		self.states={
		}
		self.global_handlers=[]

	def prepare(self,fn):
		def wrapper(*args,**kwargs):
			self.chain=fn(*args,**kwargs)
		return wrapper




	def handler_response(self,handler):
		self.global_handlers.append(handler)
	def add_state(self,state):
		if type(state)==state and "id" in state  and "handlers" in state and "before_states" in state:
			assert state["id"] in self.state,Exception(f"Este estado ya existe {state['id']}")
			self.states[state["id"]]=state

	def add_handler(self,name):
		def wrapper(fn):
			"""
			Ejecuta una accion manejando el estado de la conversacion
			"""
			self.handlers[name]=fn
		return wrapper
	def check(self,name,callback):
		self.checkers[name]=callback
	def verify(self,output):
		handlers=[]
		for handler,checker in self.checkers.items():
			if checker(output):
				handlers.append(handlers)
		for state_id in self.states:
			if state_id not in self.history:
				before_states=True
				for before in self.states[state_id].before_states:
					if before not in self.history:
						before_states=False
						break
				if before_states:
					self.history.append(state_id)



	def process(self,handler):
		self.handler(self.ctx)
		for handler in self.global_handlers:
			handler(self.ctx)

	def __call__(self):
		"""
		Actualiza los handlers y states  en la base de datos
		ConversationState
		ConversationStore
		ConversationEvent
		"""
		print("PROCESANDO PARA CONTRUIR DB")
		print(self.handlers)
		print(self.states)
		for handler in self.handlers:
			with self.session() as sess:
				#Verificamos los eventos y el store existan en la base de datos
				results=sess.query(self.modelStore,self.modelEvent).filter(
					self.modelStore.name==self.name,
					self.modelEvent.handler==handler).join(self.modelEvent).first()
				print("wwww",results)
				if not results:
					store=self.modelStore(name=self.name)
					sess.add(store)
					sess.commit()
				if not results:
					event=self.modelEvent(
						store=store.id,
						handler=handler)
					sess.add(event)
					sess.commit()

		for state_name in self.states:
			with self.session() as sess:
				#Verificamos los states y el store existan en la base de datos
				results=sess.query(
					self.modelStore,self.modelState).filter(
					self.modelStore.name==self.name,
					self.modelState.name==state_name).join(self.modelState).first()
				#si el store no exite lo crea
				if not results:
					store=self.modelStore(name=name)
					sess.add(store)
					sess.commit()
				#si el state no existe lo crea
				if not results:
					state=self.modelState(
						store=store.id,
						name=state_name)
			
					sess.add(state)
					sess.commit()

class AgentWrapper:
	def __init__(self,chain,control):
		self.chain=chain
		self.control=control
	def run(self,query):
		self.chain.run(query)

class Chain(LLMChain):
	pass
	def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
		return super()._call(inputs)
	@classmethod
	def handler(cls,fn):
		
		def wrapper(*args,**kwargs):
			print("jjjjjjjjj",args,kwargs)
			return fn(args)
			"""
			output=fn(instance)
			verificated=instance.controller.verify(output)
			if verificated:
				instance.controller.process(verificated)
			"""
				
		return wrapper