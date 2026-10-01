# Eliminador de Metadatos — ReconForense

Interfaz Tkinter + backend Bash/ExifTool para analizar y limpiar metadatos.

## Archivos

- `eliminador_metadatos.py` — interfaz gráfica.
- `limpiar_metadatos.sh` — backend Bash.
- `metadata_cleanup.gif` — animación HUD donde los elementos de metadatos entran en la papelera.

## Instalación en Kali Linux

```bash
sudo apt update
sudo apt install python3 python3-tk libimage-exiftool-perl
```

## Ejecución

```bash
chmod +x limpiar_metadatos.sh eliminador_metadatos.py
./eliminador_metadatos.py
```

El programa genera por defecto un archivo `*_SIN_METADATOS.ext` y conserva intacto el original.

## Nota forense

La barra de progreso de la interfaz es visual: ExifTool realiza la operación como una única tarea y no expone un porcentaje fiable de bytes procesados. Para evidencia digital, conservar siempre el original y registrar SHA-256 antes/después.

El alcance de `-all=` depende del formato y de las etiquetas que ExifTool pueda escribir/eliminar. No debe interpretarse como garantía de eliminación de toda información derivada del sistema de archivos o de cualquier estructura interna del contenedor.
