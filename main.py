import xbmc
import xbmcgui
import json
import random

def hacer_pregunta(titulo, opciones):
    dialog = xbmcgui.Dialog()
    return dialog.select(titulo, opciones)

def obtener_peliculas_kodi():
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovies",
        "params": {
            "properties": ["genre", "runtime", "playcount", "file", "year"]
        },
        "id": 1
    }
    response = xbmc.executeJSONRPC(json.dumps(query))
    data = json.loads(response)
    return data.get('result', {}).get('movies', [])

def main():
    dialog = xbmcgui.Dialog()
    dialog.notification("Recomendador", "Preparando el cuestionario...", xbmcgui.NOTIFICATION_INFO, 3000)

    # --- CUESTIONARIO ---
    # 1. GÉNEROS (Ampliado con Drama y Animación)
    generos = ["Ciencia ficción", "Terror", "Acción", "Comedia", "Suspense", "Fantasía", "Drama", "Animación"]
    p1 = hacer_pregunta("¿Qué género te apetece hoy?", generos)
    if p1 == -1: return
    genero_elegido = generos[p1].lower()

    # 2. DURACIÓN
    duraciones = ["Menos de 90 min (Algo rápido)", "Menos de 120 min (Normal)", "Cualquier duración"]
    p2 = hacer_pregunta("¿De cuánto tiempo dispones?", duraciones)
    if p2 == -1: return

    # 3. VISTAS
    vistas = ["Solo películas que NO haya visto", "No me importa repetir"]
    p3 = hacer_pregunta("¿Quieres algo nuevo o repetir?", vistas)
    if p3 == -1: return

    # 4. ÉPOCA
    epocas = [
        "Actual (De 2010 en adelante)", 
        "Moderna (De 1980 a 2010)", 
        "Clásica (1980 y anteriores)"
    ]
    p4 = hacer_pregunta("¿A qué época quieres viajar?", epocas)
    if p4 == -1: return

    # --- FILTRADO DE LA BIBLIOTECA ---
    todas_las_pelis = obtener_peliculas_kodi()
    pelis_filtradas = []

    for peli in todas_las_pelis:
        try:
            if not peli or 'label' not in peli:
                continue
                
            # --- CONTROL DE GÉNERO TOLERANTE ---
            generos_peli = peli.get('genre', [])
            if not isinstance(generos_peli, list):
                continue
            
            # Limpieza básica de cadenas para evitar problemas con tildes o guiones
            generos_peli_limpios = [g.lower().replace("-", " ").replace("ó", "o") for g in generos_peli]
            genero_elegido_limpio = genero_elegido.replace("ó", "o")
            
            match_genero = False
            if genero_elegido == "ciencia ficción":
                if any("cien" in g or "sci" in g for g in generos_peli_limpios):
                    match_genero = True
            else:
                if any(genero_elegido_limpio in g for g in generos_peli_limpios):
                    match_genero = True
                    
            if not match_genero:
                continue
            
            # --- CONTROL DE DURACIÓN ---
            runtime_original = peli.get('runtime', 0)
            if runtime_original is None:
                runtime_original = 0
            
            runtime_min = runtime_original / 60
            if p2 == 0 and runtime_min > 90: continue
            if p2 == 1 and runtime_min > 120: continue

            # --- CONTROL DE VISTO ---
            playcount = peli.get('playcount', 0)
            if playcount is None:
                playcount = 0
                
            if p3 == 0 and playcount > 0:
                continue

            # --- CONTROL DE ÉPOCA ---
            anio_peli = peli.get('year', 0)
            if anio_peli is None:
                anio_peli = 0
                
            if p4 == 0 and anio_peli < 2010: 
                continue
            elif p4 == 1 and (anio_peli < 1980 or anio_peli >= 2010): 
                continue
            elif p4 == 2 and anio_peli > 1980: 
                continue

            pelis_filtradas.append(peli)

        except Exception as e:
            xbmc.log(f"[Recomendador] Saltado elemento por error en filtro: {str(e)}", xbmc.LOGWARNING)
            continue

    # --- LÓGICA DEL TOP 5 Y REPRODUCCIÓN ---
    if pelis_filtradas:
        random.shuffle(pelis_filtradas)
        top_5_pelis = pelis_filtradas[:5]
        opciones_menu = [peli['label'] for peli in top_5_pelis]
        
        seleccion_final = hacer_pregunta("Mis 5 recomendaciones para ti (Elige una):", opciones_menu)
        
        if seleccion_final != -1:
            peli_a_reproducir = top_5_pelis[seleccion_final]
            
            ruta_archivo = peli_a_reproducir.get('file', '')
            if ruta_archivo:
                xbmc.executebuiltin(f"PlayMedia(\"{ruta_archivo}\")")
            else:
                id_peli = str(peli_a_reproducir['movieid'])
                xbmc.executebuiltin(f"PlayMedia(movieid={id_peli})")
    else:
        dialog.ok("Sin resultados", "No encontré películas con esos requisitos exactos en tu biblioteca.")

if __name__ == '__main__':
    main()
