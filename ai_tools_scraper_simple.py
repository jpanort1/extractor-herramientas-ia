#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTOR AUTOMÁTICO DE HERRAMIENTAS DE IA
==========================================
Script simplificado para extraer herramientas de IA y guardarlas en Google Sheets
Diseñado para usuarios sin conocimientos técnicos
"""

import requests
from bs4 import BeautifulSoup
import gspread
import json
import csv
from datetime import datetime
import time
import os

def log_message(message):
    """Función para mostrar mensajes con timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def extraer_futuretools():
    """
    Extrae herramientas de FutureTools.io de forma simple y robusta
    """
    log_message("🔍 Extrayendo herramientas de FutureTools.io...")
    
    url = "https://www.futuretools.io/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        herramientas = []
        
        # Buscar elementos que contengan herramientas
        elementos = soup.find_all(['div', 'article', 'a'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['tool', 'card', 'item'] if x
        ))
        
        for elemento in elementos[:50]:  # Limitar a 50 para evitar sobrecarga
            try:
                # Extraer nombre
                nombre_elem = elemento.find(['h1', 'h2', 'h3', 'h4', 'a'])
                nombre = nombre_elem.get_text(strip=True) if nombre_elem else 'Sin nombre'
                
                # Extraer descripción
                desc_elem = elemento.find(['p', 'div'], class_=lambda x: x and 'description' in x.lower() if x else False)
                if not desc_elem:
                    desc_elem = elemento.find('p')
                descripcion = desc_elem.get_text(strip=True) if desc_elem else 'Sin descripción'
                
                # Extraer URL
                url_elem = elemento.find('a', href=True)
                url_herramienta = 'Sin URL'
                if url_elem:
                    href = url_elem['href']
                    if href.startswith('/'):
                        url_herramienta = f"https://www.futuretools.io{href}"
                    elif href.startswith('http'):
                        url_herramienta = href
                
                # Solo agregar si tiene información útil
                if len(nombre) > 3 and nombre != 'Sin nombre':
                    herramientas.append({
                        'nombre': nombre,
                        'descripcion': descripcion[:200],  # Limitar descripción
                        'url': url_herramienta,
                        'categoria': 'IA General',
                        'fuente': 'FutureTools.io',
                        'fecha': datetime.now().strftime('%Y-%m-%d')
                    })
                    
            except Exception as e:
                continue
        
        # Eliminar duplicados por nombre
        herramientas_unicas = []
        nombres_vistos = set()
        
        for herramienta in herramientas:
            nombre_lower = herramienta['nombre'].lower().strip()
            if nombre_lower not in nombres_vistos and len(nombre_lower) > 3:
                nombres_vistos.add(nombre_lower)
                herramientas_unicas.append(herramienta)
        
        log_message(f"✅ Extraídas {len(herramientas_unicas)} herramientas de FutureTools.io")
        return herramientas_unicas
        
    except Exception as e:
        log_message(f"❌ Error extrayendo de FutureTools.io: {str(e)}")
        return []

def extraer_toolify():
    """
    Extrae herramientas de Toolify.ai usando requests (sin Selenium para simplicidad)
    """
    log_message("🔍 Extrayendo herramientas de Toolify.ai...")
    
    url = "https://www.toolify.ai/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        herramientas = []
        
        # Buscar enlaces que contengan "/tool/"
        enlaces_herramientas = soup.find_all('a', href=lambda x: x and '/tool/' in x)
        
        for enlace in enlaces_herramientas[:30]:  # Limitar para evitar sobrecarga
            try:
                nombre = enlace.get_text(strip=True)
                url_herramienta = enlace['href']
                
                if not url_herramienta.startswith('http'):
                    url_herramienta = f"https://www.toolify.ai{url_herramienta}"
                
                # Buscar descripción en el elemento padre
                descripcion = 'Sin descripción'
                parent = enlace.parent
                if parent:
                    desc_elem = parent.find('p') or parent.find('div', class_=lambda x: x and 'desc' in x.lower() if x else False)
                    if desc_elem:
                        descripcion = desc_elem.get_text(strip=True)[:200]
                
                if len(nombre) > 3:
                    herramientas.append({
                        'nombre': nombre,
                        'descripcion': descripcion,
                        'url': url_herramienta,
                        'categoria': 'IA General',
                        'fuente': 'Toolify.ai',
                        'fecha': datetime.now().strftime('%Y-%m-%d')
                    })
                    
            except Exception as e:
                continue
        
        # Eliminar duplicados
        herramientas_unicas = []
        nombres_vistos = set()
        
        for herramienta in herramientas:
            nombre_lower = herramienta['nombre'].lower().strip()
            if nombre_lower not in nombres_vistos and len(nombre_lower) > 3:
                nombres_vistos.add(nombre_lower)
                herramientas_unicas.append(herramienta)
        
        log_message(f"✅ Extraídas {len(herramientas_unicas)} herramientas de Toolify.ai")
        return herramientas_unicas
        
    except Exception as e:
        log_message(f"❌ Error extrayendo de Toolify.ai: {str(e)}")
        return []

def escribir_google_sheets(datos, nombre_hoja="Herramientas IA", nombre_pestana="Datos"):
    """
    Escribe los datos en Google Sheets de forma simple
    """
    if not datos:
        log_message("⚠️ No hay datos para escribir en Google Sheets")
        return False
    
    try:
        log_message("📊 Conectando con Google Sheets...")
        
        # Buscar archivo de credenciales
        archivos_credenciales = ['credentials.json', 'service_account.json', 'google_credentials.json']
        archivo_credenciales = None
        
        for archivo in archivos_credenciales:
            if os.path.exists(archivo):
                archivo_credenciales = archivo
                break
        
        if not archivo_credenciales:
            log_message("❌ No se encontró archivo de credenciales de Google")
            log_message("💡 Necesitas descargar el archivo credentials.json de Google Cloud Console")
            return False
        
        # Conectar con Google Sheets
        gc = gspread.service_account(filename=archivo_credenciales)
        
        # Abrir o crear la hoja de cálculo
        try:
            hoja_calculo = gc.open(nombre_hoja)
            log_message(f"📋 Hoja '{nombre_hoja}' encontrada")
        except gspread.exceptions.SpreadsheetNotFound:
            log_message(f"📋 Creando nueva hoja '{nombre_hoja}'...")
            hoja_calculo = gc.create(nombre_hoja)
            hoja_calculo.share('', perm_type='anyone', role='reader')
        
        # Seleccionar o crear pestaña
        try:
            pestana = hoja_calculo.worksheet(nombre_pestana)
        except gspread.exceptions.WorksheetNotFound:
            log_message(f"📄 Creando nueva pestaña '{nombre_pestana}'...")
            pestana = hoja_calculo.add_worksheet(title=nombre_pestana, rows="1000", cols="10")
        
        # Obtener datos existentes para evitar duplicados
        try:
            registros_existentes = pestana.get_all_records()
            nombres_existentes = {registro.get('nombre', '').lower().strip() for registro in registros_existentes}
        except:
            registros_existentes = []
            nombres_existentes = set()
        
        # Preparar headers si la hoja está vacía
        headers = ['nombre', 'descripcion', 'url', 'categoria', 'fuente', 'fecha']
        if not registros_existentes:
            log_message("📝 Agregando headers...")
            pestana.append_row(headers)
        
        # Filtrar duplicados
        datos_nuevos = []
        for dato in datos:
            nombre_lower = dato.get('nombre', '').lower().strip()
            if nombre_lower and nombre_lower not in nombres_existentes:
                datos_nuevos.append(dato)
                nombres_existentes.add(nombre_lower)
        
        if datos_nuevos:
            log_message(f"📝 Agregando {len(datos_nuevos)} nuevas herramientas...")
            
            # Preparar filas para insertar
            filas = []
            for dato in datos_nuevos:
                fila = [dato.get(header, '') for header in headers]
                filas.append(fila)
            
            # Insertar datos por lotes
            pestana.append_rows(filas)
            
            log_message(f"✅ {len(datos_nuevos)} herramientas agregadas exitosamente")
            log_message(f"🔗 URL de la hoja: {hoja_calculo.url}")
            
            return True
        else:
            log_message("ℹ️ No hay herramientas nuevas para agregar")
            return False
            
    except Exception as e:
        log_message(f"❌ Error escribiendo en Google Sheets: {str(e)}")
        return False

def guardar_respaldo_local(datos):
    """
    Guarda un respaldo local de los datos en CSV y JSON
    """
    if not datos:
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Guardar en CSV
    try:
        archivo_csv = f"herramientas_ia_{timestamp}.csv"
        with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
            if datos:
                writer = csv.DictWriter(f, fieldnames=datos[0].keys())
                writer.writeheader()
                writer.writerows(datos)
        log_message(f"💾 Respaldo CSV guardado: {archivo_csv}")
    except Exception as e:
        log_message(f"⚠️ Error guardando CSV: {e}")
    
    # Guardar en JSON
    try:
        archivo_json = f"herramientas_ia_{timestamp}.json"
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        log_message(f"💾 Respaldo JSON guardado: {archivo_json}")
    except Exception as e:
        log_message(f"⚠️ Error guardando JSON: {e}")

def main():
    """
    Función principal que ejecuta todo el proceso
    """
    log_message("🚀 INICIANDO EXTRACTOR DE HERRAMIENTAS DE IA")
    log_message("=" * 50)
    
    todas_herramientas = []
    
    # Extraer de FutureTools.io
    herramientas_futuretools = extraer_futuretools()
    todas_herramientas.extend(herramientas_futuretools)
    
    # Esperar un poco entre extracciones
    time.sleep(2)
    
    # Extraer de Toolify.ai
    herramientas_toolify = extraer_toolify()
    todas_herramientas.extend(herramientas_toolify)
    
    if todas_herramientas:
        log_message(f"📊 Total de herramientas extraídas: {len(todas_herramientas)}")
        
        # Guardar respaldo local
        guardar_respaldo_local(todas_herramientas)
        
        # Escribir en Google Sheets
        exito = escribir_google_sheets(todas_herramientas)
        
        if exito:
            log_message("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        else:
            log_message("⚠️ Proceso completado con errores en Google Sheets")
    else:
        log_message("❌ No se pudieron extraer herramientas de ninguna fuente")
    
    log_message("=" * 50)
    log_message("✅ Extractor finalizado")

if __name__ == "__main__":
    main()

