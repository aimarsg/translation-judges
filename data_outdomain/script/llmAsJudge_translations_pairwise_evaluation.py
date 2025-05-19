import argparse
import os
import sys
import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import random
import getpass


random.seed(42)

def obtener_feedback(texto):
    clave = "AI:"
    # Buscar la posicion de la clave
    posicion = texto.find(clave)
    if posicion != -1:
        # Extraer todo lo que viene despues de la clave
        return texto[posicion + len(clave):].strip()
    else:
        return "Error: No se ha encontrado el feedback. Texto RAW: "+texto


def main(data_path, prompt_path, model, batch_size, output_path):

    # Comprobar si los archivos existen
    if not os.path.isfile(prompt_path):
        print(f"Error: El archivo {prompt_path} no existe.")
        sys.exit(1)
    else:
        with open(prompt_path, 'r') as archivo:
            content = archivo.read()
            contentJson = json.loads(content)
            system_template = contentJson["system"]
            user_template = contentJson["user"]
    
    if not os.path.isfile(data_path):
        print(f"Error: El archivo '{data_path}' no existe.")
        sys.exit(1)
    
    #######################     instanciar el modelo   #######################

    if model=="llama":
        #model_id = "meta-llama/Llama-3.2-3B-Instruct"
        model_id = "meta-llama/Llama-3.1-8B-Instruct"
    elif model=="gemma":
        model_id = "google/gemma-2-9b-it"
    elif model == "mistral":
        #model_id = "mistralai/Mistral-7B-Instruct-v0.3"
        model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    elif model == "aloe":
        model_id = "HPAI-BSC/Llama3.1-Aloe-Beta-8B"
    elif model == "latxa":
        model_id = "HiTZ/Latxa-Llama-3.1-8B-Instruct"
    elif model == "llamaeus":
        model_id = "orai-nlp/Llama-eus-8B"
    else:
        exit(1)

    tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side='left')
    tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", temperature=0, do_sample=True)

    pipe = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer, 
        max_new_tokens=300, 
        do_sample=True,
        model_kwargs={
            'device_map': 'auto',
            'batch_size':batch_size,
            "temperature": 0 ,
            }, 
        batch_size=batch_size 
    )

    hf = HuggingFacePipeline(pipeline=pipe, batch_size=batch_size, model_kwargs={"temperature": 0})


    ##############    Generar los prompts    ###################
    prompts = []
    combination_keys = []
    instance_metadata = []

    with open(data_path, 'r') as dataset:
        data = json.load(dataset)
        for instancia in data:
            # original text
            og_text = instancia["og_text"]
            # 4 translations
            translations = {}

            for key in ["nllb", "upv-cmbt", "itzuli"]:
                if key in instancia:
                    if instancia[key]!= "": # comprobar que no es vacio
                        translations[key] = instancia[key]
            
            items = list(translations.items())
            random.shuffle(items)
            translations = dict(items)            

            # crear todos los pares posibles de translations
            translation_pairs = [(item1, item2) 
                        for i, item1 in enumerate(translations.items()) 
                        for item2 in list(translations.items())[i+1:]]
            
            # con cada par de argumentos crear el prompt y añadirlo a la lista de prompts
            for translationA, translationB in translation_pairs:
                keyA, valueA = translationA
                keyB, valueB = translationB
                combination_keys.append([keyA, keyB])
                instance_metadata.append(
                    {
                        "id": instancia['id'],
                        "language": instancia['language'],
                    }
                )
        
                # Plantilla del prompt que se va a utilizar
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_template),
                    ("user",   user_template),
                    ("assistant", "{assistant_response}")
                ]
                )

                # completar plantilla del prompt con los datos 
                prompt = prompt_template.invoke(
                    {
                        # TODO RELLENAR EL PROMPT
                        "source_text": og_text,
                        "translation_a": valueA,
                        "translation_b": valueB,
                        "assistant_response": "Feedback:::\nEvaluation:",
                    })
                
                prompts.append(prompt) # guardar el prompt en la lista de prompts


    #######################   Pasar los prompts al modelo y guardar los resultados #################

    # sacar un ejemplo por terminal para probar
    print(instance_metadata)
    print(instance_metadata[0])
    print("prompt")
    print(prompts[0])
    response1 = hf.invoke(prompts[0]) 
    print("response")
    print(response1)
    print("combination")
    print(combination_keys[0])

    # pasar todos los prompts a la vez al modelo
    responses = hf.batch(prompts) 

    # guardar los output en un fichero
    output = []
    i=0
    for response in responses:
        json_output = {}

        json_output["id"] = instance_metadata[i]["id"]
        json_output["language"] = instance_metadata[i]["language"]
        json_output["combination"]   = combination_keys[i]
        i+=1

        json_output["model_evaluation"] = obtener_feedback(response)
        output.append(json_output)
    
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=4)
        
        

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Script para utilizar LLM-as-judge utilizando un prompt de plantilla")
    parser.add_argument("path", help="Ruta al directorio de datos")
    parser.add_argument("template", help="Plantilla para el prompt")
    parser.add_argument("model", help="llama/gemma/mistral/aloe/latxa/llamaeus", choices=["llama", "gemma", "mistral", "aloe", "latxa", "llamaeus"])
    parser.add_argument("--batch", help="batch size para la inferencia", type=int)
    parser.add_argument("--output_file", help="Nombre del fichero de salida")
    args = parser.parse_args()    

    if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = getpass.getpass("Enter your token: ")

    if args.batch is not None:
        batch_size = args.batch
    else: 
        batch_size = 24

    if args.output_file is None:
        output_file = f"output_{(args.model).replace('/', '_')}"
    else:
        output_file = args.output_file
    main(args.path, args.template, args.model, batch_size, output_file)

