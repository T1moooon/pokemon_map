import folium

from django.shortcuts import render
from django.utils.timezone import localtime
from .models import Pokemon


MOSCOW_CENTER = [55.751244, 37.618423]
DEFAULT_IMAGE_URL = (
    'https://vignette.wikia.nocookie.net/pokemon/images/6/6e/%21.png/revision'
    '/latest/fixed-aspect-ratio-down/width/240/height/240?cb=20130525215832'
    '&fill=transparent'
)


def add_pokemon(folium_map, lat, lon, image_url=DEFAULT_IMAGE_URL):
    icon = folium.features.CustomIcon(
        image_url,
        icon_size=(50, 50),
    )
    folium.Marker(
        [lat, lon],
        # Warning! `tooltip` attribute is disabled intentionally
        # to fix strange folium cyrillic encoding bug
        icon=icon,
    ).add_to(folium_map)


def show_all_pokemons(request):
    current_time = localtime()
    pokemons = Pokemon.objects.all()

    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)

    for pokemon in pokemons:
        active_entities = pokemon.pokemonentity_set.filter(
            appeared_at__lte=current_time,
            disappeared_at__gte=current_time
        )
        for pokemon_entity in active_entities:
            add_pokemon(
                folium_map,
                pokemon_entity.lat,
                pokemon_entity.lon,
                request.build_absolute_uri(pokemon.image.url) if pokemon.image else None
            )

    pokemons_on_page = []
    for pokemon in pokemons:
        pokemons_on_page.append({
            'pokemon_id': pokemon.id,
            'img_url': pokemon.image.url if pokemon.image else None,
            'title_ru': pokemon.title,
        })

    return render(request, 'mainpage.html', context={
        'map': folium_map._repr_html_(),
        'pokemons': pokemons_on_page,
    })


def show_pokemon(request, pokemon_id):
    pokemon = Pokemon.objects.get(id=pokemon_id)
    current_time = localtime()
    active_entities = pokemon.pokemonentity_set.filter(
        appeared_at__lte=current_time,
        disappeared_at__gte=current_time
    )

    next_evolution = None
    if hasattr(pokemon, 'next_evolutions') and pokemon.next_evolutions.exists():
        next_pokemon = pokemon.next_evolutions.first()
        next_evolution = {
            "title_ru": next_pokemon.title,
            "pokemon_id": next_pokemon.id,
            "img_url": request.build_absolute_uri(next_pokemon.image.url) if next_pokemon.image else None
        }

    pokemon_dict = {
        "pokemon_id": pokemon.id,
        "title_ru": pokemon.title,
        "title_en": pokemon.title_en,
        "title_jp": pokemon.title_jp,
        "description": pokemon.description,
        "img_url": request.build_absolute_uri(pokemon.image.url) if pokemon.image else None,
        "entities": [{
            "level": entity.level,
            "lat": entity.lat,
            "lon": entity.lon
        } for entity in active_entities],
        "next_evolution": next_evolution,
        "previous_evolution": {
            "title_ru": pokemon.previous_evolution.title,
            "pokemon_id": pokemon.previous_evolution.id,
            "img_url": request.build_absolute_uri(pokemon.previous_evolution.image.url) if pokemon.previous_evolution.image else None
        } if pokemon.previous_evolution else None
    }

    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)
    for pokemon_entity in active_entities:
        add_pokemon(
            folium_map,
            pokemon_entity.lat,
            pokemon_entity.lon,
            request.build_absolute_uri(pokemon.image.url) if pokemon.image else None
        )

    return render(request, 'pokemon.html', context={
        'map': folium_map._repr_html_(),
        'pokemon': pokemon_dict
    })
