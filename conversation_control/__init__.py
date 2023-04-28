from collections import OrderedDict
from langchain.chains import LLMChain,SequentialChain,ConversationChain
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
    def __init__(self,name,session,models,force_outputs=[]):
        self.name=name
        self.handlers={}
        self.checkers={}
        self.observation={}
        self.history=[]
        self.modelState=models["state"]
        self.modelStore=models["store"]
        self.modelEvent=models["event"]
        self.session=session
        self.max_intents=3
        self.force_outputs=[]
        """
        states:{
            "id":"name",
            handlers:[],
            before_states[]
        }
        """
        with session() as sess:
            store=sess.query(self.modelStore).filter(
                self.modelStore.name==name).first()
            self.store=store.id
        self.states={
        }
        self.global_handlers=[]
    def force(self,chain,inputs):
        intents=0
        while self.max_intents>intents:
            results=chain.generate(inputs)
            for elem in self.force_outputs:
                if elem in results.generations[0].text:
                    break
            else:
                return results.generations
            intents+=1
        raise Exception("Limite de intentos superados")


    def prepare(self,fn):
        def wrapper(*args,**kwargs):
            self.chain=fn(*args,**kwargs)
            self.chain.control=self
        return wrapper

    def process_handler(self,data):
        event=self.get_event("is_bni_request")
        if event:
            if not data["_is_bni_request"]:
                if event["negative_response"]:
                    data["response"]=event["negative_response"]
                if event["negative_result"]!=None:
                    data["_is_bni_request@result"]=event["negative_result"]
            else:
                if event["positive_response"]:
                    data["response"]=event["positive_response"]
                if event["positive_result"]!=None:
                    data["_is_bni_request@result"]=event["positive_result"]




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


    def get_event(self,name):
        from dataclasses import asdict
        with control.session() as sess:
            instance=sess.query(control.modelEvent).filter(
                control.modelEvent.store==self.store,
                control.modelEvent.name==name).first()
            return asdict(instance)



    def process(self,result):
        for handler in self.handlers:
            if handler in result:
                self.handlers[handler](result,self.observation)
                
        for handler in self.global_handlers:
            handler(result)

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


class SequentialChain(SequentialChain):
    control:ConversationControl=None
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)



class AgentWrapper:
    def __init__(self,chain,control):
        self.chain=chain
        self.chain.control=control
        control.chain=chain
        if isinstance(self.chain,SequentialChain):
            for chain in self.chain.chains:
                chain.control=control

        self.control=control
    def run(self,query):
        return self.chain(query)

class Chain(LLMChain):
    control:ConversationControl=None
    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        return super()._call(inputs)
    @classmethod
    def handler(cls,fn):
        
        def wrapper(instance,*args,**kwargs):
            
            response=fn(instance,*args,**kwargs)
        
            return response
        
        return wrapper
class ConversationChain(ConversationChain):
    control:ConversationControl=None
    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        result=super()._call(inputs)
        
        #Aca manejo los handlers configurados en el asistente
        self.control.process(result)

        
        return result

    @classmethod
    def handler(cls,fn):
        
        def wrapper(instance,*args,**kwargs):

            response=fn(instance,*args,**kwargs)
            #instance.control.on.update(response)
            return response
        
        return wrapper

