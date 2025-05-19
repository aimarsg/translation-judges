import pandas as pd
import krippendorff
import argparse
import sys

def calcular_krippendorff_alpha(csv1, csv2):
    # Columnas de rankings
    ranking_cols = ['enes-eu', 'gt', 'en-eu', 'latxa', 'es-eu']

    try:
        df1 = pd.read_csv(csv1, sep=';')
        df2 = pd.read_csv(csv2, sep=',')
    except Exception as e:
        print(f"Error al leer los archivos: {e}")
        sys.exit(1)
    

    # Asegurar que los rankings son float
    df1[ranking_cols] = df1[ranking_cols].astype(float)
    df2[ranking_cols] = df2[ranking_cols].astype(float)

    # if Language column is es on first line, drop en-eu column. else if it is en, drop es-eu column
    # if df2.iloc[0]['Language'] == 'es':
    #     df1.drop(columns=['en-eu'], inplace=True)
    #     df2.drop(columns=['en-eu'], inplace=True)
    #     ranking_cols.remove('en-eu')
    # elif df2.iloc[0]['Language'] == 'en':
    #     df1.drop(columns=['es-eu'], inplace=True)
    #     df2.drop(columns=['es-eu'], inplace=True)
    #     ranking_cols.remove('es-eu')


    # Hacer merge solo de las instancias comunes
    df_merged = pd.merge(df1, df2, on=["corpus", "code", "ita"], how="inner", suffixes=('_a1', '_a2'))
    # guardar df_merged en un archivo CSV
    df_merged.to_csv("merged.csv", sep=';', index=False)

    if df_merged.empty:
        print("No hay instancias comunes entre los dos archivos.")
        sys.exit(1)

    #print(f"Instancias comunes encontradas: {len(df_merged)}")

    # Preparar los datos para el cálculo de Krippendorff
    registros = []
    for _, row in df_merged.iterrows():
        for col in ranking_cols:
            v1 = row[f"{col}_a1"]
            v2 = row[f"{col}_a2"]
            registros.append([v1, v2])

    # Transponer para que cada lista sea un anotador
    data = list(zip(*registros))
    #print(f"Datos para Krippendorff: {data}")

    # Calcular Krippendorff's alpha (ordinal)
    alpha = krippendorff.alpha(reliability_data=data, level_of_measurement='ordinal')

    print(f"file: {csv2}\n annotator: {csv1} \nKrippendorff's alpha (ordinal): {alpha:.4f}\n")


def main():
    parser = argparse.ArgumentParser(description="Calcula Krippendorff's alpha ordinal entre rankings anotados por dos personas.")
    parser.add_argument("csv1", help="Ruta al archivo CSV del anotador 1")
    parser.add_argument("csv2", help="Ruta al archivo CSV del anotador 2")
    args = parser.parse_args()

    calcular_krippendorff_alpha(args.csv1, args.csv2)

if __name__ == "__main__":
    main()
