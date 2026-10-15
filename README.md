# Código Morse SisCom

Transmisor de código Morse por luz (OOK) para la Tarea 1 de **Sistemas de Comunicaciones 2026**, Universidad de Concepción, Facultad de Ingeniería.

- **Profesor:** Dr. Fernando Castillo Rivera
- **Integrantes:** Julian Alfaro y Matías Vargas

**Página:** https://morse-siscom.github.io/

## Qué hace

La página convierte una frase (letras A a Z y espacios) en código Morse y la transmite encendiendo y apagando la pantalla del celular: blanca = 1, negra = 0. Usa las proporciones de UIT-R M.1677-1:

| Elemento | Pantalla | Duración |
| --- | --- | --- |
| Punto | Blanca | T |
| Raya | Blanca | 3T |
| Entre símbolos de una letra | Negra | T |
| Entre letras | Negra | 3T |
| Entre palabras | Negra | 7T |

T se elige en la página (200 ms por defecto). Antes y después del mensaje la pantalla queda negra durante un margen configurable. Cada transmisión queda registrada con su patrón previsto 0/1 (SIS COM = 61 intervalos).

## Uso

1. Abrir la página en el celular transmisor, con brillo al máximo y modo avión.
2. Escribir la frase y elegir T.
3. Usar "Pantalla blanca fija" para apuntar la cámara y bloquear exposición y enfoque.
4. Empezar a grabar con el otro celular y tocar "Transmitir".

El video se procesa con el receptor en Python de la tarea (calibración, decodificación, CER, FFT y PSD).

Desarrollado con apoyo de IA (Claude, Anthropic).
