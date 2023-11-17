from typing import Any
from Utils import add_logger_name_cls,load_from_cfg,generate_name_new,generate_logger_subfile,human_evaluation
from Recoder import Recoder
from EvalMethods import ToolUse,Keyword,GPT4eval,Blacklist
from Analyser import Analyse,Getinfo
import os
import zhipuai


# log_name = generate_name_new('dialog_init')
log_name = 'dialog_init'
logger_name = 'dialog_init.log'
logger_subfile = generate_logger_subfile()
add_logger_to_class = add_logger_name_cls(log_name,os.path.join('Logs',logger_subfile))
logger_path = os.path.join(os.path.join('Logs',logger_subfile),logger_name)
@add_logger_to_class
class AutoInteractor():
    def __init__(self, testcase,methodnum,threadnum) -> None:
        load_from_cfg(self, testcase)
        # self.recoders = []
        self.methodnum = methodnum
        self.threadnum = threadnum
        self.llm = self.llm()
        self.logger_path = logger_path
    
    def eval(self):
        """
        A function that creates a evaluation stack for every testcase.
        This function uses a dictionary to judge whether a evaluation method should be used in this testcase, and it's certain that this method should be used, it will be added to a dictionary. 
        The dictionary "eval_stack" is the final evaluation stack, the value of every key is the corresponding evaluation object.

        """
        eval_dict={"tool":ToolUse,"keywords":Keyword,"blacklist":Blacklist,"GPT4eval":GPT4eval}
        eval_stack={}
        for key in eval_dict.keys():
            if (key in self.eval_info.keys()):
                eval_cls=eval_dict[key]
                eval_method=eval_cls(self.prompt,'',self.eval_info,'',0)
                eval_stack[key]=eval_method
        return(eval_stack)
    
    def get_logger_path(self):
        return(self.logger_path)


    def base_interact(self, prompt):

        """
        A function to create the interaction between the LLM and the user.
        It will record the dialogue in the log file and the answers to prompts sent to LLM from the LLM will be saved in a list called ans_list.
        In this method, the dialogue mainly contains the propmts that the user sends to LLM, and the response from the LLM.

        """
        # recoder = Recoder()
        # recoder.ind = ind
        print(f"---------- New Epoch ---------- from thread {self.threadnum}")
        ans_list=[]
        for ind, pr in enumerate(prompt):
            # recoder.dialoge[ind] = ''
            print(f"To LLM:\t {pr} from thread {self.threadnum}")
            # recoder.dialoge[ind] += f"To LLM:\t {pr}\n"
            ans = self.llm(pr)
            # ans="Yes"
            ans_list.append(ans.lower())
        return(ans_list)


        # recoder.dialoge[ind] += f"To User:\t {ans}"
        # self.recoders.append(recoder)
    
    def tool_interact(self, prompt, tools:list):

        """
        A function to create the interaction between the LLM, the user and the tool.
        It will record the dialogue in the log file and the content that LLM sends to the tool will be saved in a list called ans_list.
        In this method, the dialogue mainly contains the propmts that the user sends to LLM, the content that the LLM sends to the tool and the response from the tool.

        """
        # recoder = Recoder()
        # recoder.ind = ind
        # recoder.prompt = prompt
        print(f"---------- New Epoch ---------- from thread {self.threadnum}")
        ans_list=[]
        for ind, pr in enumerate(prompt):
            # recoder.dialoge[ind] = ''
            print(f"To LLM:\t {pr} from thread {self.threadnum}")
            # recoder.dialoge[ind] += f"To LLM:\t {pr}\n"
            ans = self.llm(pr)
            ans_list.append(ans.lower())
            if ans.find(tools[0]['name']) != -1:  # TODO: add multi tools
                # recoder.tools = tools[0].name
                print(f"To Tool:\t {ans} from thread {self.threadnum}")
                # recoder.dialoge[ind] += f"To LLM:\t {pr}\n"
                tool_response = self.tools[0](ans)
                print(f"To LLM:\t {tool_response} from thread {self.threadnum}")
                # recoder.dialoge[ind] += f"To LLM:\t {tool_response}\n"
                ans = self.llm(tool_response)
            print(f"To User:\t {ans} from thread {self.threadnum}")
        #     recoder.dialoge[ind] += f"To LLM:\t {tool_response}\n"
        # self.recoders.append(recoder)
        return(ans_list)
    
    
    def run(self):

        """
        A function to start the interaction.
        If the interaction contains tools, it will record the dialogue between the tool, the user and the LLM.
        If the interaction doesn't contain tools, it will record the dialogue between the user and the LLM.
        The function use a list to record the answers from the LLM, and use this answer list to evaluate the LLM in this testcase. It will evaluate the LLM with every method chosen by the user.
        
        """
        eval_stack=self.eval()
        blacklist_score = 1
        score_dict = {}
        if self.eval_info.get('tool', None):#TODO:如果这里按照这个逻辑执行，对于同一个prompt，有了tool评价方法就不能再使用其他方法，并且所有prompt的答案设置都必须含有keyword评价方法。
            toolusage_ans=self.tool_interact(self.prompt, self.eval_info['tool'])
            eval_obj=eval_stack['tool']
            eval_obj.set_ans(toolusage_ans)
            eval_obj.set_field(self.field)
            eval_obj.set_threadnum(self.threadnum)
            toolusage_score,tool_eval_info=eval_obj.score(self.methodnum[0]) 
            print(tool_eval_info+f'from thread {self.threadnum}')
            score_dict['toolusage'] = toolusage_score
        else:
            keywords_ans=self.base_interact(self.prompt)
            if  self.eval_info.get('blacklist', None):
                eval_obj=eval_stack['blacklist']
                eval_obj.set_ans(keywords_ans)
                eval_obj.set_field(self.field)
                eval_obj.set_threadnum(self.threadnum)
                blacklist_score,blacklist_eval_info=eval_obj.score(self.methodnum[2]) 
                print(blacklist_eval_info+f'from thread {self.threadnum}')
                score_dict['blacklist'] = blacklist_score

            if  blacklist_score!=0 and self.eval_info.get('keywords', None):
                eval_obj=eval_stack['keywords']
                eval_obj.set_ans(keywords_ans)
                eval_obj.set_field(self.field)
                eval_obj.set_threadnum(self.threadnum)
                keywords_score,keywords_eval_info=eval_obj.score(self.methodnum[1]) 
                print(keywords_eval_info+f'from thread {self.threadnum}')
                score_dict['keywords'] = keywords_score

            if  blacklist_score!=0 and self.eval_info.get('GPT4eval', None):
                eval_obj=eval_stack['GPT4eval']
                eval_obj.set_ans(keywords_ans)
                eval_obj.set_field(self.field)
                eval_obj.set_prompt(self.prompt)
                eval_obj.set_threadnum(self.threadnum)
                GPT4_eval_score,GPT4_eval_info=eval_obj.score(self.methodnum[3]) 
                print(GPT4_eval_info+f'from thread {self.threadnum}')
                score_dict['GPT4_eval'] = GPT4_eval_score
        final_score_obj = self.finalscore(score_dict,self.field,self.threadnum)
        human_judge,final_score_info,final_score = final_score_obj.final_score_info()

        if human_judge != 'Human Evaluation':
            print(final_score_info)
        else:
            print('Human Evaluation!'+f'from thread {self.threadnum}')
            human_eval = {'prompt':self.prompt,'ans':keywords_ans,'field':self.field,'threadnum':self.threadnum}
            human_evaluation(human_eval)
        if final_score == 0:
            if 'blacklist' in self.eval_info:
                print(f'Mistaken case:prompt:{self.prompt},ans:{keywords_ans},field:{self.field},keywords:{self.eval_info["keywords"][0]},blacklist:{self.eval_info["blacklist"][0]}')
            else:
                print(f'Mistaken case:prompt:{self.prompt},ans:{keywords_ans},field:{self.field},keywords:{self.eval_info["keywords"][0]}')

        if final_score != 0:
            print(f'Example case:prompt:{self.prompt},ans:{keywords_ans},field:{self.field}')
            


