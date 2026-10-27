# Receptor Morse en Python

Programa que reconstruye el texto Morse a partir del video grabado por la cámara.
Tarea 1, Sistemas de Comunicaciones 2026, Universidad de Concepción. Julián Alfaro y Matías Vargas.

## Qué hace

1. Lee el video cuadro a cuadro, lo pasa a gris y lo reduce.
2. Ubica la ROI donde el brillo más varía (la fuente) y calcula I[n], el promedio de la ROI en cada cuadro.
3. Calibra una sola vez con PARIS PARIS a 0,5 m: umbral de Otsu y T = duración del mensaje / 93.
4. Separa encendido y apagado, agrupa los cuadros en rachas y mide su duración con la hora de cada cuadro.
   El mensaje es el grupo de pulsos entre los márgenes apagados (pausas de más de 2,5 s).
5. Encendido: menos de 2T es punto, de 2T a 6T es raya. Apagado: desde 2T termina la letra y desde 5T la palabra.
6. Busca cada patrón en la tabla Morse («?» si no existe) y calcula la CER con la distancia de Levenshtein.
7. Calcula el espectro de amplitud, la PSD (periodograma) y B95.

La frase transmitida solo se usa al final, para calcular la CER.

## Uso

```
pip install opencv-python numpy matplotlib
python receptor.py calibrar paris_paris_0p5m.mp4
python receptor.py decodificar sis_com_1m.mp4 --ref "SIS COM"
python receptor.py espectro sis_com_0p5m.mp4
```

- `calibrar` guarda el umbral y T en `calib.json`.
- `decodificar` muestra el texto, la CER y el gráfico de I[n], y guarda el gráfico como PNG junto al video.
- Con el flash del celular, calibrar con `--roi 3 3 --escala 4` (la fuente es pequeña).
- Si la ROI no queda sobre la fuente, se puede elegir a mano con `--centro x y` (en píxeles del cuadro reducido).

## Otras formas de usarlo

- Página: https://morse-siscom.github.io/receptor/ (mismo algoritmo, en el navegador)
- Google Colab: https://colab.research.google.com/github/morse-siscom/morse-siscom.github.io/blob/main/Receptor_Morse.ipynb
