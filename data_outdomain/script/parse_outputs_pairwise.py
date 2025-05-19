import json
import os
import re
import pandas as pd
import argparse
from collections import defaultdict
import trueskill

def process_json_to_table(data, src_lang):
    # Cargar el archivo JSON

    suma_winners = defaultdict(int)

    # create all players
    players = {
        "nllb": trueskill.Rating(),
        "upv-cmbt": trueskill.Rating(),
        "itzuli": trueskill.Rating(),
    }
        

    comparaciones = []

    for inst in data:
        comb = inst["combination"]
        #print(comb)

        model_eval = inst["model_evaluation"]
        #print(model_eval)
        winner_str = model_eval.lower().split("chosen translation:")
        if len(winner_str) > 1:
            winner_str = winner_str[1]
        else:
            winner_str = winner_str[0]
        winner = re.sub(r"[^\w\s]", "", winner_str)           # quita signos de puntuación
        winner_final = re.sub(r"\s+", "", winner).strip()      # limpia espacios múltiples
        #print(winner)
        if len(winner) > 0:
            winner_final = winner_final.replace("translation", "").strip()
            winner = winner_final[0]
            if winner not in ["a", "b"]:
                winner = winner_final[-1]
        if winner=="a":
            suma_winners[comb[0]] += 1
            winner_model = comb[0]
            loser_model = comb[1]

        elif winner=="b":
            suma_winners[comb[1]] += 1
            winner_model = comb[1]
            loser_model = comb[0]
        else:
            print(f"Error al parsear winner en code {inst['id']}:\n{winner}")
            print(f"winner_str: {winner_str}")
            continue
        

        comparaciones.append((winner_model, loser_model))


    # Aplicar TrueSkill a cada comparación
    for ganador, perdedor in comparaciones:
        players[ganador], players[perdedor] = trueskill.rate_1vs1(players[ganador], players[perdedor])
    
    # ranking de los players con trueskill
    ranking = sorted(players.items(), key=lambda x: -x[1].mu)

    #ranking con el contador de winners
    sorted_args = sorted(suma_winners.items(), key=lambda x: x[1], reverse=True)

    # convertir en json los rankings
    cont_ranking = {}
    for i, (modelo, cont) in enumerate(sorted_args, start=1):
        cont_ranking[modelo] = cont
        
    
    trueskill_ranking = {}
    for i, (name, rating) in enumerate(ranking, 1):
        trueskill_ranking[name] = round(rating.mu, 2)

    return cont_ranking, trueskill_ranking
    

def main(input_file, output_file):
    # Procesar el archivo JSON
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        
    ranking_json = {}
        
    # OVERALL SCORE
    #cont_ranking, trueskill_ranking = process_json_to_table(data, "en-es")
    
    # parse cont_ranking
    ranking_json["Overall"] = {}
    overall_winner_count = {}
    overall_trueskill = {}
    
    
    # BY LANGUAGE SCORE
    # get only data with language es and en
    ranking_json["By_language"] = {}
    
    for lang in ["es"]:
        ranking_json["By_language"][lang] = {}
        data_lang = [inst for inst in data if inst["language"] == lang]
        cont_ranking, trueskill_ranking = process_json_to_table(data_lang, lang)
        ranking_json["By_language"][lang]["winner_count"] = cont_ranking
        ranking_json["By_language"][lang]["trueskill"] = trueskill_ranking
        
        # recorrer el ranking y guardar los resultados en overall
        for model, count in cont_ranking.items():
            if model not in overall_winner_count:
                overall_winner_count[model] = count
            else:
                # si ya existe, hacer la media
                overall_winner_count[model] = round((overall_winner_count[model] + count) / 2, 2)
                
            
        for model, rating in trueskill_ranking.items():
            if model not in overall_trueskill:
                overall_trueskill[model] = rating
            else:
                # si ya existe, hacer la media
                overall_trueskill[model] = round((overall_trueskill[model] + rating) / 2, 2)
            
    # sort overall_winner_count and overall_trueskill
    overall_winner_count = dict(sorted(overall_winner_count.items(), key=lambda x: -x[1]))
    overall_trueskill = dict(sorted(overall_trueskill.items(), key=lambda x: -x[1]))

    ranking_json["Overall"]["winner_count"] = overall_winner_count
    ranking_json["Overall"]["trueskill"] = overall_trueskill
    
    # BY CORPUS SCORE
    # ranking_json["By_corpus"] = {}
    # # get a list with all the corpus names
    # corpus_names = set(inst["corpus"] for inst in data)
    # # for each corpus, get the data and process it
    # for corpus in corpus_names:
    #     ranking_json["By_corpus"][corpus] = {}
    #     data_corpus = [inst for inst in data if inst["corpus"] == corpus]
    #     cont_ranking_corpus, trueskill_ranking_corpus = process_json_to_table(data_corpus, corpus.split("-")[1])    
    #     ranking_json["By_corpus"][corpus]["winner_count"] = cont_ranking_corpus
    #     ranking_json["By_corpus"][corpus]["trueskill"] = trueskill_ranking_corpus
    
    #print(ranking_json)
    # write the ranking to a json file
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(ranking_json, file, ensure_ascii=False, indent=4)
        
    print(f"Ranking saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesar un archivo JSON y generar una tabla CSV con ratings de modelos.")
    parser.add_argument("input_file", help="Ruta al archivo JSON de entrada")

    args = parser.parse_args()

    # Extraer directorio actual y nombre base del archivo
    input_dir = os.path.dirname(args.input_file)
    input_filename = os.path.basename(args.input_file).replace(".json", "_ranking.json")

    # Construir la nueva ruta al directorio ranking (hermano de outputs)
    parent_dir = os.path.dirname(input_dir)
    output_dir = os.path.join(parent_dir, "ranking")
    os.makedirs(output_dir, exist_ok=True)  # Crea la carpeta si no existe

    # Construir la ruta de salida completa
    output_path = os.path.join(output_dir, input_filename)
    print(f"Output path: {output_path}")
    
    main(args.input_file, output_path)
