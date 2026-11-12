# Video documental

**Reconociendo prácticas escolares desde una mirada decolonial**: edición en estilo documental del video grabado por Osmar, Jenny, Miriam y Marta a partir de su guion.

## Qué incluye la edición

- **Apertura**: dos frases sobre imágenes con movimiento lento y el título principal.
- **11 capítulos** con tarjeta de presentación (número, título y subtítulo tomados de cada escena del guion).
- **Imágenes de apoyo (B-roll)** sobre la voz: telesecundarias de Guanajuato, telar de cintura, milpa, aulas, marcha del orgullo, desfile escolar, etc.
- **Rótulos con nombre** la primera vez que aparece cada participante.
- **Transiciones** con fundido a negro entre capítulos y fundidos en las imágenes.
- **Música ambiental** que baja automáticamente cuando alguien habla.
- **Cierre** con la frase final y créditos con autoría y licencias de música e imágenes.

## Cómo volver a generarlo

```bash
python3 scripts/build.py RUTA/AL/VIDEO_ORIGINAL.MOV carpeta_de_trabajo
```

Requiere `ffmpeg` y `Pillow`. El resultado queda en `carpeta_de_trabajo/documental_final.mp4`.
Los tiempos de cada escena, las imágenes de apoyo y los rótulos se ajustan en las listas
`SCENES`, `BROLL` y `LOWER` al inicio de `scripts/build.py`.

## Créditos de recursos

- Música: “The Long Dark”, de Scott Buckley (CC BY 3.0), y “I Don't See the Branches, I See the Leaves”, de Chris Zabriskie (CC BY 4.0), ambas de Wikimedia Commons.
- Imágenes: Wikimedia Commons; autores y licencias en `assets/imagenes/credits.tsv`.
