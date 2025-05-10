from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

def obter_coordenadas(cidade):
    """
    Obtém as coordenadas (latitude e longitude) de uma cidade usando geopy.
    """
    geolocator = Nominatim(user_agent="cotador_frete")
    
    # Adiciona um pequeno delay para evitar limites de API
    time.sleep(1)
    
    try:
        location = geolocator.geocode(f"{cidade}, Brasil")
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Erro ao obter coordenadas para {cidade}: {str(e)}")
        return None

def calcular_distancia_km(origem, destino):
    """
    Calcula a distância em km entre duas cidades usando geopy.
    """
    origem_coords = obter_coordenadas(origem)
    destino_coords = obter_coordenadas(destino)
    
    if not origem_coords or not destino_coords:
        return None
    
    return round(geodesic(origem_coords, destino_coords).km, 2)
