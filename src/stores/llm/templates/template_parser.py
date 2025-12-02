import os

# Constructing template parser class to follow its rules while going with embeddings
class TemplateParser:

    # Initiate the class by giving it the language and which default language if we didn't give the language
    def __init__(self , language : str=None , default_language = 'en'):
        
        # Saving current path , __file__ means current file
        self.current_path = os.path.dirname(os.path.abspath(__file__))

        # Setting default language of the parser with the default language set with the initiation
        self.default_language = default_language

        # initiate variable language with none
        self.language = None

        # using the function set language to set the language
        self.set_language(language=language)


    # making a set language function to take a language and set it in the template parser
    def set_language(self , language : str = "en"):
        
        # if it's none , setting language with default language
        if not language :
            self.language=self.default_language
            return None
        
        # getting the language supported path , whether it's arabic or english
        language_path = os.path.join(self.current_path,"locales",language)

        # if it exists in the supported path , setting it
        if language and os.path.exists(language_path):
            self.language = language

        # if it's not , set it with default language , english
        else :
            self.language=self.default_language

    # a function to get the template for every template like footer , system , document
    def get(self , group : str , key : str , vars : dict = {}):
        
        # if the group is not given return none , group is usually 'rag'
        if not group or not key:
            return None
        
        # get the group path
        group_path = os.path.join(self.current_path , "locales" , self.language , f"{group}.py")

        # setting the language for the prompt
        targeted_language = self.language

        # now check if the group path exists or not
        if not os.path.exists(group_path):
            # it the group path doesn't exist , construct one
            group_path = os.path.join(self.current_path , "locales" , self.default_language , f"rag.py")
            targeted_language = self.default_language

        # if the group path exists return none
        if not os.path.exists(group_path):
            return None
        
        # import group module
        module = __import__(f"stores.llm.templates.locales.{targeted_language}.{group}",fromlist=[group])

        if not module:
            return None
        # get the attribute for the module
        key_attribute = getattr(module,key)

        # if the ket attribute is none , return none
        if not key_attribute:
            return None

        return key_attribute.substitute(vars)